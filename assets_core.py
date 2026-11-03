# -*- coding: utf-8 -*-
"""
ComfyUI 资产管理插件核心库
============================
无 ComfyUI 依赖, 可独立测试。提供: 配置读写 / 元数据提取 / 归档 / 扫描 /
索引列表 / 删除 / 备份 / 媒体文件安全读取。
"""

import json
import os
import shutil
import subprocess
import time
import zipfile
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".mkv", ".gif"}
ALL_EXT = IMAGE_EXT | VIDEO_EXT
NEG_HINTS = ("negative", "neg prompt", "neg", "负")

DEFAULT_CONFIG = {
    "output_dir": "",   # 空 = 使用 ComfyUI 默认 output
    "archive_dir": "",  # 空 = 使用 <ComfyUI>/asset_archive
    "backup_dir": "",   # 空 = 使用 <ComfyUI>/asset_backups
    "auto_archive": True,
    "archive_existing": False,  # 首次运行是否归档 output 里已有的历史产物(False=只归档安装后的新产物)
    "thumb_width": 480,
    "interval_sec": 10,
    "ffprobe": "",      # 空 = 自动探测(优先 PATH 里的 ffprobe)
    "ffmpeg": "",       # 空 = 自动探测(优先 PATH 里的 ffmpeg)
}


def resolve_exe(fp):
    """解析可执行文件路径: 支持绝对路径 / 命令名(走 PATH) / 空(自动探测)"""
    if not fp:
        return None
    if os.path.isfile(fp):
        return fp
    import shutil
    return shutil.which(fp) or None


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

def load_config(base_dir):
    cfg = dict(DEFAULT_CONFIG)
    fp = Path(base_dir) / "config.json"
    if fp.is_file():
        try:
            user = json.loads(fp.read_text(encoding="utf-8"))
            if isinstance(user, dict):
                cfg.update(user)
        except Exception:
            pass
    return cfg


def save_config(base_dir, cfg):
    fp = Path(base_dir) / "config.json"
    tmp = fp.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, fp)


def state_file(archive_dir):
    return Path(archive_dir) / "archive_state.json"


def load_state(archive_dir):
    try:
        return json.loads(state_file(archive_dir).read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(archive_dir, state):
    fp = state_file(archive_dir)
    tmp = Path(str(fp) + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, fp)


# ---------------------------------------------------------------------------
# 打开时间状态 (v1.2.0)
# ---------------------------------------------------------------------------

def open_state_file(archive_dir):
    """打开时间状态文件: <archive_dir>/open_state.json"""
    return Path(archive_dir) / "open_state.json"


def load_open_state(archive_dir):
    """读取打开时间状态; 文件缺失/损坏/非 dict 一律返回 {}"""
    try:
        data = json.loads(open_state_file(archive_dir).read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save_open_state(archive_dir, state):
    """原子写打开时间状态(临时文件 + os.replace), 与 save_state 同写法"""
    fp = open_state_file(archive_dir)
    try:
        Path(archive_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    tmp = Path(str(fp) + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, fp)


def open_key_run(run_rel):
    """归档条目(相对 archive_dir)的打开时间键"""
    return "run:" + (run_rel if isinstance(run_rel, str) else "")


def open_key_out(rel):
    """输出目录条目(相对 output_dir)的打开时间键"""
    return "out:" + (rel if isinstance(rel, str) else "")


def touch_open(archive_dir, key, ts=None):
    """记录一次「打开/预览」: 更新 open_state.json 并落盘

    key: 任意字符串("run:<run_rel>" / "out:<rel>");  ts: None=now, 也接受 ISO 字符串/时间戳
    """
    if not isinstance(key, str) or not key.strip():
        return {"ok": False, "error": "Missing key"}
    when = None
    if ts is None:
        when = datetime.now()
    elif isinstance(ts, (int, float)):
        try:
            when = datetime.fromtimestamp(ts)
        except Exception:
            when = None
    else:
        try:
            when = datetime.fromisoformat(str(ts).strip())
        except Exception:
            when = None
    if when is None:
        when = datetime.now()
    iso = when.isoformat(timespec="seconds")
    state = load_open_state(archive_dir)
    state[key] = iso
    try:
        save_open_state(archive_dir, state)
    except Exception as e:
        return {"ok": False, "error": "Failed to save open state: " + _err_brief(e)}
    return {"ok": True, "key": key, "opened": iso}


# ---------------------------------------------------------------------------
# 元数据提取
# ---------------------------------------------------------------------------

def safe_json(s):
    if isinstance(s, (dict, list)):
        return s
    if not isinstance(s, str):
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def _exif_user_comment(exif_bytes):
    try:
        import piexif
        exif_dict = piexif.load(exif_bytes)
        uc = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
        if not uc:
            return None
        if isinstance(uc, bytes):
            for enc in ("utf-8", "utf-16"):
                try:
                    s = uc.decode(enc).strip("\x00")
                    if s:
                        return s
                except Exception:
                    pass
        return None
    except Exception:
        return None


def extract_image_metadata(path):
    prompt = workflow = None
    try:
        with Image.open(path) as im:
            info = dict(im.info)
    except Exception:
        info = {}
    prompt = info.get("prompt")
    workflow = info.get("workflow")
    if not (prompt or workflow) and info.get("exif"):
        uc = _exif_user_comment(info["exif"])
        if uc:
            obj = safe_json(uc)
            if isinstance(obj, dict):
                prompt = prompt or obj.get("prompt") or obj.get("prompt_info")
                workflow = workflow or obj.get("workflow")
    return prompt, workflow


def extract_video_metadata(path, cfg):
    fp = resolve_exe(cfg.get("ffprobe"))
    if not fp:
        return None, None
    try:
        r = subprocess.run(
            [fp, "-v", "error", "-show_entries", "format_tags", "-of", "json", str(path)],
            capture_output=True, timeout=30,
        )
        data = json.loads(r.stdout.decode("utf-8", errors="replace") or "{}")
    except Exception:
        return None, None
    tags = (data.get("format") or {}).get("tags") or {}
    return tags.get("prompt"), tags.get("workflow")


def parse_prompt_graph(graph):
    texts, params, models, seeds = [], {}, {}, []
    if not isinstance(graph, dict):
        return {"positive": "", "negative": "", "texts": texts, "params": params, "models": []}
    for nid, node in graph.items():
        if not isinstance(node, dict):
            continue
        cls = node.get("class_type") or ""
        meta = node.get("_meta") or {}
        title = meta.get("title") or cls
        inputs = node.get("inputs") or {}
        if not isinstance(inputs, dict):
            continue
        title_l = str(title).lower()
        for k, v in inputs.items():
            if not isinstance(v, str) or not v.strip():
                continue
            kk = k.lower()
            looks_path = any(x in v for x in (".safetensors", ".ckpt", ".gguf", ".sft", ".onnx", ".pth", ".pt", ".bin"))
            looks_text = (kk in ("text", "prompt", "value", "positive", "negative",
                                 "conditioned_prompt", "integrated_multimodal_description")
                          or ("text" in kk or "prompt" in kk))
            if looks_text and not looks_path and len(v) < 100000:
                is_neg = (kk == "negative" or any(h in title_l for h in NEG_HINTS) or "负" in title)
                texts.append({"node": str(nid), "title": title,
                              "role": "negative" if is_neg else "positive", "text": v})
            if looks_path:
                models.setdefault(cls or title, []).append(v)
        for k, v in inputs.items():
            kk = k.lower()
            if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip()):
                if kk in ("seed", "noise_seed"):
                    try:
                        seeds.append(int(v))
                    except Exception:
                        pass
                elif kk in ("steps", "video_steps", "audio_steps", "cfg", "cfg_scale",
                            "shift", "shift_video", "shift_audio", "sampler_name", "scheduler",
                            "width", "height", "frame_rate", "length", "denoise",
                            "strength_model", "aspect_ratio", "megapixels", "multiple",
                            "quality", "crf", "start_step", "end_step"):
                    if kk not in params:
                        params[kk] = v
    positive = "\n".join(t["text"] for t in texts if t["role"] == "positive")
    negative = "\n".join(t["text"] for t in texts if t["role"] == "negative")
    if seeds:
        params["seeds"] = seeds
    model_list, seen = [], set()
    for names in models.values():
        for n in names:
            if n not in seen:
                seen.add(n)
                model_list.append(n)
    return {"positive": positive, "negative": negative, "texts": texts,
            "params": params, "models": model_list}


# ---------------------------------------------------------------------------
# 归档
# ---------------------------------------------------------------------------

def make_video_thumb(src, dst, cfg):
    ff = resolve_exe(cfg.get("ffmpeg"))
    if not ff:
        return None
    width = int(cfg.get("thumb_width", 480))
    for ss in ("0", "1"):
        try:
            r = subprocess.run(
                [ff, "-y", "-hide_banner", "-loglevel", "error",
                 "-ss", ss, "-i", str(src), "-frames:v", "1",
                 "-vf", f"scale={width}:-2", str(dst)],
                capture_output=True, timeout=60,
            )
            if r.returncode == 0 and dst.exists() and dst.stat().st_size > 0:
                return "thumb.jpg"
        except Exception:
            pass
        if dst.exists():
            try:
                dst.unlink()
            except Exception:
                pass
    return None


def archive_file(rel, src, archive_dir, state, cfg):
    st = os.stat(src)
    state_key = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
    if state.get(rel) == state_key:
        return None
    ext = Path(rel).suffix.lower()
    kind = "video" if ext in VIDEO_EXT else "image"
    arch = Path(archive_dir)

    if kind == "image":
        prompt_raw, workflow_raw = extract_image_metadata(src)
    else:
        prompt_raw, workflow_raw = extract_video_metadata(src, cfg)
    prompt_graph = safe_json(prompt_raw)
    workflow_graph = safe_json(workflow_raw)
    parsed = parse_prompt_graph(prompt_graph) if prompt_graph else \
        {"positive": "", "negative": "", "texts": [], "params": {}, "models": []}

    stem = Path(rel).stem
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in stem)[:60].strip("._")
    mtime = datetime.fromtimestamp(st.st_mtime)
    date_folder = mtime.strftime("%Y-%m-%d")
    run_id = mtime.strftime("%Y%m%d-%H%M%S") + "_" + (safe or "output")
    run_dir = arch / date_folder / run_id
    n = 2
    while run_dir.exists():
        run_dir = arch / date_folder / f"{run_id}_{n}"
        n += 1
    run_dir.mkdir(parents=True, exist_ok=True)

    media_name = Path(rel).name
    shutil.copy2(src, run_dir / media_name)

    thumb = None
    if kind == "image" and HAS_PIL:
        try:
            with Image.open(src) as im:
                im = im.convert("RGB")
                im.thumbnail((cfg["thumb_width"], cfg["thumb_width"]))
                im.save(run_dir / "thumb.jpg", "JPEG", quality=82, optimize=True)
                thumb = "thumb.jpg"
        except Exception:
            pass
    elif kind == "video":
        thumb = make_video_thumb(src, run_dir / "thumb.jpg", cfg)

    info = {
        "run_id": run_dir.name,
        "archived_at": datetime.now().isoformat(timespec="seconds"),
        "generated_at": mtime.isoformat(timespec="seconds"),
        "created_at": datetime.fromtimestamp(st.st_ctime).isoformat(timespec="seconds"),
        "source_mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "source_rel": rel,
        "media": media_name,
        "kind": kind,
        "file_size": st.st_size,
        "positive": parsed["positive"],
        "negative": parsed["negative"],
        "prompt_nodes": parsed["texts"],
        "params": parsed["params"],
        "models": parsed["models"],
        "has_workflow": workflow_graph is not None,
        "thumb": thumb,
        "prompt_json": prompt_graph,
        "workflow_json": workflow_graph,
    }
    (run_dir / "info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["=== ComfyUI 产物信息 ===",
             f"来源: {rel}", f"生成时间: {info['generated_at']}",
             f"类型: {'视频' if kind == 'video' else '图片'}",
             f"大小: {st.st_size / 1024:.0f} KB"]
    if parsed["models"]:
        lines.append("模型/LoRA: " + ", ".join(parsed["models"]))
    if parsed["params"]:
        lines.append("参数: " + json.dumps(parsed["params"], ensure_ascii=False))
    lines += ["", "=== 正向提示词 ===", parsed["positive"] or "(未检测到)"]
    if parsed["negative"]:
        lines += ["", "=== 负向提示词 ===", parsed["negative"]]
    (run_dir / "prompt.txt").write_text("\n".join(lines), encoding="utf-8")

    if workflow_graph:
        (run_dir / "workflow.json").write_text(
            json.dumps(workflow_graph, ensure_ascii=False, indent=1), encoding="utf-8")

    state[rel] = state_key
    return {"run": run_dir.name, "dir": run_dir.relative_to(arch).as_posix(), "kind": kind}


def scan_all(output_dir, archive_dir, state, cfg):
    out = Path(output_dir)
    if not out.is_dir():
        return 0
    new_runs = []
    state_changed = False
    archive_existing = bool(cfg.get("archive_existing", False))
    baseline_done = bool(state.get("__baseline_done__", False))
    for root, dirs, files in os.walk(out):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.startswith("."):
                continue
            if Path(fn).suffix.lower() not in ALL_EXT:
                continue
            src = Path(root) / fn
            rel = src.relative_to(out).as_posix()
            try:
                st = os.stat(src)
            except OSError:
                continue
            cur_key = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
            if state.get(rel) == cur_key:
                continue
            # 等待写入完成
            last = None
            t0 = time.time()
            stable = False
            while time.time() - t0 < 6.0:
                try:
                    cur = (os.stat(src).st_size, os.stat(src).st_mtime_ns)
                except OSError:
                    break
                if cur == last:
                    stable = True
                    break
                last = cur
                time.sleep(0.5)
            if not stable:
                continue
            if rel in state:
                # 已记录过(归档过或基线过), 文件有变化 → 归档新版本
                r = archive_file(rel, src, archive_dir, state, cfg)
                if r:
                    new_runs.append(r)
            elif baseline_done or archive_existing:
                # 基线已建立后的新文件, 或用户开启"归档历史" → 归档
                r = archive_file(rel, src, archive_dir, state, cfg)
                if r:
                    new_runs.append(r)
            else:
                # 首次扫描且不归档历史: 只记录基线(不复制文件)
                state[rel] = cur_key
                state_changed = True
    if not baseline_done:
        state["__baseline_done__"] = True
        state_changed = True
    if new_runs or state_changed:
        save_state(archive_dir, state)
    return len(new_runs)


# ---------------------------------------------------------------------------
# 索引 / 列表
# ---------------------------------------------------------------------------

def list_runs(archive_dir, open_state=None):
    arch = Path(archive_dir)
    runs = []
    if not arch.is_dir():
        return runs
    if not isinstance(open_state, dict):
        open_state = {}
    for date_dir in arch.iterdir():
        if not date_dir.is_dir():
            continue
        for run_dir in date_dir.iterdir():
            info_file = run_dir / "info.json"
            if not info_file.is_file():
                continue
            try:
                info = json.loads(info_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            try:
                files = sorted(p.name for p in run_dir.iterdir() if p.is_file())
            except OSError:
                files = []
            run_rel = run_dir.relative_to(arch).as_posix()
            runs.append({
                "id": info.get("run_id") or run_dir.name,
                "date": (info.get("generated_at") or "")[:10],
                "time": info.get("generated_at") or "",
                "name": info.get("source_rel") or run_dir.name,
                "kind": info.get("kind") or "image",
                "media": info.get("media"),
                "thumb": info.get("thumb"),
                "files": files,
                "dir": run_rel,
                "positive": info.get("positive") or "",
                "negative": info.get("negative") or "",
                "models": info.get("models") or [],
                "params": info.get("params") or {},
                "has_workflow": bool(info.get("has_workflow")),
                "source_rel": info.get("source_rel") or "",
                "created": info.get("created_at") or info.get("generated_at") or "",
                "mtime": info.get("source_mtime") or info.get("generated_at") or "",
                "opened": open_state.get(open_key_run(run_rel)) or "",
            })
    runs.sort(key=lambda r: r.get("time") or "", reverse=True)
    return runs


# ---------------------------------------------------------------------------
# 删除
# ---------------------------------------------------------------------------

def delete_run(archive_dir, output_dir, state, run_id):
    arch = Path(archive_dir).resolve()
    out = Path(output_dir).resolve() if output_dir else None
    if not run_id or not isinstance(run_id, str):
        return {"ok": False, "error": "Missing run_id"}
    run_dir = (arch / run_id).resolve()
    if run_dir == arch or not str(run_dir).startswith(str(arch) + os.sep):
        return {"ok": False, "error": "Invalid archive path"}
    info_file = run_dir / "info.json"
    if not (run_dir.is_dir() and info_file.is_file()):
        return {"ok": False, "error": "Archive entry not found"}
    source_rel = None
    try:
        info = json.loads(info_file.read_text(encoding="utf-8"))
        source_rel = info.get("source_rel")
    except Exception:
        pass
    shutil.rmtree(run_dir)
    if source_rel and out:
        src = (out / source_rel).resolve()
        # 防穿越: source_rel 必须解析后仍位于 output 目录内
        if str(src).startswith(str(out) + os.sep) and src.is_file():
            try:
                src.unlink()
            except Exception:
                pass
        state.pop(source_rel, None)
    save_state(archive_dir, state)
    return {"ok": True, "source_rel": source_rel}


# ---------------------------------------------------------------------------
# 备份
# ---------------------------------------------------------------------------

def default_asset_dirs(base_dir):
    """通用默认目录(相对 ComfyUI 安装目录, 与机器无关)"""
    comfy_dir = Path(base_dir).resolve().parent.parent
    return str(comfy_dir / "asset_archive"), str(comfy_dir / "asset_backups")


def backup_assets(cfg, base_dir, workflow_dirs=None):
    _arch_default, _bak_default = default_asset_dirs(base_dir)
    archive_dir = Path(cfg.get("archive_dir") or _arch_default)
    backup_dir = Path(cfg.get("backup_dir") or _bak_default)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = backup_dir / f"ComfyUI_asset_backup_{stamp}.zip"
    workflow_dirs = workflow_dirs or []

    def _add(zf, root, arcname):
        root = Path(root)
        if not root.exists():
            return 0
        n = 0
        for f in root.rglob("*"):
            if f.is_file():
                rel = f.relative_to(root).as_posix()
                zf.write(f, f"{arcname}/{rel}")
                n += 1
        return n

    total = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        total += _add(zf, archive_dir, "assets")
        for i, wd in enumerate(workflow_dirs):
            if wd:
                total += _add(zf, wd, f"workflows_{i}")
        cfg_file = Path(base_dir) / "config.json"
        if cfg_file.is_file():
            zf.write(cfg_file, "config.json")
            total += 1
    size = zip_path.stat().st_size
    return {"ok": True, "file": str(zip_path), "name": zip_path.name,
            "size": size, "files": total}


# ---------------------------------------------------------------------------
# 媒体文件安全读取
# ---------------------------------------------------------------------------

def safe_media_path(archive_dir, rel):
    """校验 rel 在 archive_dir 内且为文件, 返回 Path 或 None"""
    arch = Path(archive_dir).resolve()
    p = (arch / rel).resolve()
    if not str(p).startswith(str(arch) + os.sep):
        return None
    if not p.is_file():
        return None
    return p


# ---------------------------------------------------------------------------
# 输出目录: 浏览 + 文件夹管理 (v1.2.0)
# ---------------------------------------------------------------------------

def _err_brief(exc):
    """异常摘要(英文短句, 不含本地化系统消息)"""
    errno_ = getattr(exc, "errno", None)
    if errno_ is None:
        return type(exc).__name__
    return "%s errno=%s" % (type(exc).__name__, errno_)


def _warn_add(existing, text):
    """把警告摘要追加到已有警告后面"""
    return (existing + "; " + text) if existing else text


def _iso_ts(ts):
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def _norm_rel(value):
    """规范化 output 相对路径(POSIX, 无首尾斜杠, 无 . / .. 段)。

    绝对路径 / 盘符 / .. 越界 -> ValueError
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Invalid path")
    s = value.strip()
    if s == "":
        return ""
    if "\x00" in s or ":" in s:
        raise ValueError("Invalid path")
    s = s.replace("\\", "/")
    if s.startswith("/"):
        raise ValueError("Invalid path")
    parts = []
    for seg in s.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            raise ValueError("Invalid path")
        parts.append(seg)
    return "/".join(parts)


def _resolve_in(root, rel):
    """在 root 内解析 rel; 解析后越界 -> ValueError"""
    root_p = Path(root).resolve()
    p = (root_p / rel).resolve()
    if p == root_p:
        return p
    if not str(p).startswith(str(root_p) + os.sep):
        raise ValueError("Invalid path")
    return p


def _dir_file_count(path):
    """递归统计目录内文件数; 出错按 0 计"""
    try:
        entries = list(os.scandir(path))
    except OSError:
        return 0
    total = 0
    for e in entries:
        try:
            if e.is_dir(follow_symlinks=False):
                total += _dir_file_count(e.path)
            elif e.is_file(follow_symlinks=False):
                total += 1
        except OSError:
            continue
    return total


def _dir_entry_count(path):
    n = 0
    try:
        with os.scandir(path) as it:
            for _ in it:
                n += 1
    except OSError:
        return 0
    return n


def _output_root(output_dir):
    if not output_dir:
        return None
    try:
        return Path(output_dir).resolve()
    except Exception:
        return None


def _valid_name(name):
    """文件夹/文件新名字校验: 空 / 纯点 / 含 \\ / : / .. 均非法"""
    if not isinstance(name, str):
        return False
    s = name.strip()
    if not s or s.strip(".") == "":
        return False
    if any(ch in s for ch in ("/", "\\", ":", "\x00")):
        return False
    if ".." in s:
        return False
    return True


def _valid_rename_name(name):
    """改名的新名字校验: 允许 "."(扩展名) 与 ".." 字面量(a..b); 拒空 / 纯点 / 含 \\ / : / NUL"""
    if not isinstance(name, str):
        return False
    s = name.strip()
    if not s or s.strip(".") == "":
        return False
    if any(ch in s for ch in ("/", "\\", ":", "\x00")):
        return False
    return True


def _archive_index(archive_dir):
    """source_rel -> {dir, thumb, media}; 同一来源取最新归档条目"""
    index = {}
    try:
        runs = list_runs(archive_dir)
    except Exception:
        return index
    for r in runs:
        sr = r.get("source_rel") or ""
        if sr and sr not in index:
            index[sr] = {
                "dir": r.get("dir") or "",
                "thumb": r.get("thumb") or "",
                "media": r.get("media") or "",
            }
    return index


def _rewrite_archive_source(archive_dir, old_rel, new_rel, moved_at):
    """把归档里 source_rel == old_rel 的条目改写成 new_rel 并写 moved_at; 返回改写条数"""
    n = 0
    arch = Path(archive_dir)
    try:
        info_files = list(arch.glob("*/*/info.json"))
    except OSError:
        return 0
    for fp in info_files:
        try:
            info = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(info, dict) or info.get("source_rel") != old_rel:
            continue
        info["source_rel"] = new_rel
        info["moved_at"] = moved_at
        tmp = Path(str(fp) + ".tmp")
        tmp.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, fp)
        n += 1
    return n


def _migrate_state_key(state, old_rel, new_rel, new_path):
    """归档状态键迁移: 旧键存在则搬到新键; 不存在则按新文件写一份基线键(同 move_output 口径)"""
    if old_rel in state:
        state[new_rel] = state.pop(old_rel)
    else:
        st = os.stat(str(new_path))
        state[new_rel] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}


def _iter_files_under(base_path, prefix_old, prefix_new):
    """(old_rel, new_rel, 新绝对路径) 列表, 递归 base_path(base_path 已是改名后的新路径)"""
    pairs = []
    try:
        walker = os.walk(str(base_path))
    except Exception:
        return pairs
    for dirpath, dirnames, filenames in walker:
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                f_rel = p.relative_to(base_path).as_posix()
            except ValueError:
                continue
            pairs.append((prefix_old + "/" + f_rel, prefix_new + "/" + f_rel, p))
    return pairs


def list_output(output_dir, rel="", archive_dir=None, open_state=None):
    """列出 output 下某目录的直接子项(跳过 . 开头项, 不排序)"""
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    try:
        rel_n = _norm_rel(rel)
        target = _resolve_in(root, rel_n)
    except ValueError:
        return {"ok": False, "error": "Directory not found"}
    if not target.is_dir():
        return {"ok": False, "error": "Directory not found"}
    if not isinstance(open_state, dict):
        open_state = load_open_state(archive_dir) if archive_dir else {}
    index = _archive_index(archive_dir) if archive_dir else {}
    try:
        entries = list(os.scandir(target))
    except OSError:
        return {"ok": False, "error": "Directory not found"}
    dirs, files = [], []
    for e in entries:
        name = e.name
        if name.startswith("."):
            continue
        child_rel = name if not rel_n else rel_n + "/" + name
        try:
            is_dir = e.is_dir(follow_symlinks=False)
            is_file = e.is_file(follow_symlinks=False)
        except OSError:
            continue
        if is_dir:
            created, mtime = "", ""
            try:
                st = e.stat(follow_symlinks=False)
                created = _iso_ts(st.st_ctime)
                mtime = _iso_ts(st.st_mtime)
            except OSError:
                pass
            dirs.append({
                "name": name,
                "rel": child_rel,
                "created": created,
                "mtime": mtime,
                "file_count": _dir_file_count(e.path),
                "opened": open_state.get(open_key_out(child_rel)) or "",
            })
            continue
        if not is_file:
            continue
        size, created, mtime = 0, "", ""
        try:
            st = e.stat(follow_symlinks=False)
            size = int(st.st_size)
            created = _iso_ts(st.st_ctime)
            mtime = _iso_ts(st.st_mtime)
        except OSError:
            pass
        ext = Path(name).suffix.lower()
        kind = "image" if ext in IMAGE_EXT else ("video" if ext in VIDEO_EXT else "other")
        run = index.get(child_rel) or {}
        files.append({
            "name": name,
            "rel": child_rel,
            "kind": kind,
            "size": size,
            "created": created,
            "mtime": mtime,
            "opened": open_state.get(open_key_out(child_rel)) or "",
            "run_dir": run.get("dir") or "",
            "thumb": run.get("thumb") or "",
            "media": run.get("media") or "",
        })
    if rel_n == "":
        parent = None
    else:
        parent = rel_n.rsplit("/", 1)[0] if "/" in rel_n else ""
    return {"ok": True, "path": rel_n, "abs": str(target), "parent": parent,
            "dirs": dirs, "files": files}


def folder_tree(output_dir, open_state=None, max_depth=8, max_nodes=2000):
    """output 目录的完整文件夹树(只含目录), 供左栏一次拉全(v1.2.1 §2.6)

    - 一趟递归: 每个目录只 os.scandir 一次, 自底向上累计递归 file_count(无 O(n^2))
    - 跳过以 "." 开头的目录; 超 max_depth / max_nodes -> truncated=True 并停止深入(不报错)
    """
    root = _output_root(output_dir)
    if root is None or not root.is_dir():
        return {"ok": False, "error": "Directory not found"}
    if not isinstance(open_state, dict):
        open_state = {}
    try:
        max_depth = int(max_depth)
    except Exception:
        max_depth = 8
    try:
        max_nodes = int(max_nodes)
    except Exception:
        max_nodes = 2000
    if max_depth < 1:
        max_depth = 1
    if max_nodes < 1:
        max_nodes = 1

    stat_truncated = [False]
    stat_count = [0]

    def walk(path, rel, depth):
        """返回 (本层子目录节点列表, 本目录递归文件数)"""
        nodes = []
        file_count = 0
        try:
            with os.scandir(path) as it:
                entries = list(it)
        except OSError:
            return nodes, 0
        dir_entries = []
        for e in entries:
            name = e.name
            if name.startswith("."):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    dir_entries.append(e)
                elif e.is_file(follow_symlinks=False):
                    file_count += 1
            except OSError:
                continue
        for e in dir_entries:
            if depth > max_depth or stat_count[0] >= max_nodes:
                stat_truncated[0] = True
                continue
            child_rel = e.name if not rel else rel + "/" + e.name
            created, mtime = "", ""
            try:
                st = e.stat(follow_symlinks=False)
                created = _iso_ts(st.st_ctime)
                mtime = _iso_ts(st.st_mtime)
            except OSError:
                pass
            children, sub_files = walk(e.path, child_rel, depth + 1)
            stat_count[0] += 1
            file_count += sub_files
            nodes.append({
                "rel": child_rel,
                "name": e.name,
                "depth": depth,
                "created": created,
                "mtime": mtime,
                "opened": open_state.get(open_key_out(child_rel)) or "",
                "file_count": sub_files,
                "children": children,
            })
        return nodes, file_count

    nodes, _root_files = walk(root, "", 1)
    return {"ok": True, "abs": str(root), "truncated": stat_truncated[0],
            "node_count": stat_count[0], "nodes": nodes}


def _kind_of(name):
    ext = Path(name).suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    return "other"


def list_output_files(output_dir, rel="", max_files=5000):
    """递归列出 rel 文件夹下的所有文件(v1.2.2, 供「下载文件夹」用)

    -> {"ok","path","truncated","count","files":[{"rel","name","kind","size","mtime"}]}
    files[].rel 相对 output 根; 跳过 "." 开头的文件与目录; 超 max_files 置 truncated 并停止。
    """
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    try:
        limit = int(max_files)
    except Exception:
        limit = 5000
    if limit < 1:
        limit = 5000
    try:
        rel_n = _norm_rel(rel)
        target = _resolve_in(root, rel_n)
    except ValueError:
        return {"ok": False, "error": "Directory not found"}

    if target.is_file():
        try:
            st = target.stat()
        except OSError:
            return {"ok": False, "error": "Directory not found"}
        return {"ok": True, "path": rel_n, "truncated": False, "count": 1,
                "files": [{"rel": rel_n, "name": target.name, "kind": _kind_of(target.name),
                           "size": int(st.st_size), "mtime": _iso_ts(st.st_mtime)}]}
    if not target.is_dir():
        return {"ok": False, "error": "Directory not found"}

    files = []
    truncated = False
    for cur, dirs, names in os.walk(str(target)):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for nm in names:
            if nm.startswith("."):
                continue
            if len(files) >= limit:
                truncated = True
                break
            fp = Path(cur) / nm
            try:
                st = fp.stat()
            except OSError:
                continue
            try:
                child_rel = fp.relative_to(root).as_posix()
            except ValueError:
                continue
            files.append({"rel": child_rel, "name": nm, "kind": _kind_of(nm),
                          "size": int(st.st_size), "mtime": _iso_ts(st.st_mtime)})
        if truncated:
            break
    return {"ok": True, "path": rel_n, "truncated": truncated,
            "count": len(files), "files": files}


def mkdir_output(output_dir, rel_parent="", name=""):
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    if not _valid_name(name):
        return {"ok": False, "error": "Invalid folder name"}
    clean = name.strip()
    try:
        parent_rel = _norm_rel(rel_parent)
        parent = _resolve_in(root, parent_rel)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if not parent.is_dir():
        return {"ok": False, "error": "Directory not found"}
    target = parent / clean
    if target.exists():
        return {"ok": False, "error": "Already exists"}
    try:
        target.mkdir()
    except OSError as e:
        return {"ok": False, "error": "Failed to create folder: " + _err_brief(e)}
    new_rel = clean if not parent_rel else parent_rel + "/" + clean
    return {"ok": True, "rel": new_rel}


def rename_output(output_dir, rel="", new_name="", archive_dir=None, state=None):
    """文件或文件夹改名; 同步归档条目 source_rel 与归档状态键(v1.2.0 勘误 A2)

    archive_dir=None 且 state=None 时只做磁盘改名(向后兼容旧的两参调用)。
    """
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    try:
        rel_n = _norm_rel(rel)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if rel_n == "":
        return {"ok": False, "error": "Cannot rename the output root"}
    if not _valid_rename_name(new_name):
        return {"ok": False, "error": "Invalid folder name"}
    clean = new_name.strip()
    try:
        src = _resolve_in(root, rel_n)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if not src.exists():
        return {"ok": False, "error": "Not found"}
    parent_rel = rel_n.rsplit("/", 1)[0] if "/" in rel_n else ""
    new_rel = clean if not parent_rel else parent_rel + "/" + clean
    if new_rel == rel_n:
        return {"ok": True, "old": rel_n, "rel": new_rel}
    dst = src.parent / clean
    if dst.exists():
        return {"ok": False, "error": "Already exists"}
    is_dir = src.is_dir()
    try:
        os.rename(str(src), str(dst))
    except OSError as e:
        return {"ok": False, "error": "Failed to rename: " + _err_brief(e)}

    result = {"ok": True, "old": rel_n, "rel": new_rel}
    if not archive_dir and state is None:
        return result

    # 磁盘改名已成功; 归档/状态/打开时间联动失败只记 warn, 不改 ok
    if is_dir:
        pairs = _iter_files_under(dst, rel_n, new_rel)
    else:
        pairs = [(rel_n, new_rel, dst)]
    warn = ""
    state_dirty = False
    # open_state 只在 archive_dir 有值时联动; 用精确对迁移(不做前缀匹配, 避免 out:a 误伤 ab/x.png)
    open_state = load_open_state(archive_dir) if archive_dir else None
    open_dirty = False
    if open_state is not None and is_dir:
        k_old = open_key_out(rel_n)
        k_new = open_key_out(new_rel)
        if k_old in open_state:
            try:
                open_state[k_new] = open_state.pop(k_old)
                open_dirty = True
            except Exception as e:
                warn = _warn_add(warn, "open_state migration failed: " + _err_brief(e))
    moved_at = datetime.now().isoformat(timespec="seconds")
    for old_rel, new_rel_f, new_path in pairs:
        if archive_dir:
            try:
                _rewrite_archive_source(archive_dir, old_rel, new_rel_f, moved_at)
            except Exception as e:
                warn = _warn_add(warn, "archive rewrite failed: " + _err_brief(e))
        if state is not None:
            try:
                _migrate_state_key(state, old_rel, new_rel_f, new_path)
                state_dirty = True
            except Exception as e:
                warn = _warn_add(warn, "state migration failed: " + _err_brief(e))
        if open_state is not None:
            k_old = open_key_out(old_rel)
            k_new = open_key_out(new_rel_f)
            if k_old in open_state:
                try:
                    open_state[k_new] = open_state.pop(k_old)
                    open_dirty = True
                except Exception as e:
                    warn = _warn_add(warn, "open_state migration failed: " + _err_brief(e))
    if state is not None and state_dirty and archive_dir:
        try:
            save_state(archive_dir, state)
        except Exception as e:
            warn = _warn_add(warn, "state save failed: " + _err_brief(e))
    if open_state is not None and open_dirty:
        try:
            save_open_state(archive_dir, open_state)
        except Exception as e:
            warn = _warn_add(warn, "open_state save failed: " + _err_brief(e))
    if warn:
        result["warn"] = warn
    return result


def delete_output_dir(output_dir, rel="", recursive=False):
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    try:
        rel_n = _norm_rel(rel)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if rel_n == "":
        return {"ok": False, "error": "Cannot delete the output root"}
    try:
        target = _resolve_in(root, rel_n)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if not target.is_dir():
        return {"ok": False, "error": "Directory not found"}
    n_files = _dir_file_count(target)
    if not recursive and _dir_entry_count(target) > 0:
        return {"ok": False, "error": "Folder is not empty", "files": n_files}
    try:
        if recursive:
            shutil.rmtree(str(target))
        else:
            os.rmdir(str(target))
    except OSError as e:
        return {"ok": False, "error": "Failed to delete folder: " + _err_brief(e)}
    return {"ok": True, "files": n_files}


def delete_output_file(output_dir, rel="", archive_dir=None, state=None):
    """删除 output 下的单个文件(v1.2.3)

    与网格视图预览里的「从硬盘删除」同语义: 若有归档条目(source_rel == rel)一并删除,
    并清掉归档状态键 —— 这样两个视图删同一个资产的结果一致。
    -> {"ok": True, "rel": rel, "archives_removed": n}
    """
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    try:
        rel_n = _norm_rel(rel)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if not rel_n:
        return {"ok": False, "error": "Invalid path"}
    try:
        target = _resolve_in(root, rel_n)
    except ValueError:
        return {"ok": False, "error": "Invalid path"}
    if target.is_dir():
        return {"ok": False, "error": "Not a file"}
    if not target.is_file():
        return {"ok": False, "error": "Not found"}
    try:
        target.unlink()
    except OSError as e:
        return {"ok": False, "error": "Failed to delete file: " + _err_brief(e)}

    removed = 0
    if archive_dir:
        arch = Path(archive_dir)
        try:
            info_files = list(arch.glob("*/*/info.json"))
        except OSError:
            info_files = []
        for fp in info_files:
            try:
                info = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(info, dict) or info.get("source_rel") != rel_n:
                continue
            try:
                shutil.rmtree(str(fp.parent))
                removed += 1
            except Exception:
                pass
    if state is not None:
        state.pop(rel_n, None)
        if archive_dir:
            try:
                save_state(archive_dir, state)
            except Exception:
                pass
    return {"ok": True, "rel": rel_n, "archives_removed": removed}


def move_output(output_dir, rels, dest_rel="", archive_dir=None, state=None):
    """把 output 下的文件移动到目标文件夹(仅文件), 并同步归档条目 + 归档状态键"""
    if not isinstance(rels, list):
        return {"ok": False, "error": "from must be an array"}
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    try:
        dest_n = _norm_rel(dest_rel)
        dest_path = _resolve_in(root, dest_n)
    except ValueError:
        return {"ok": False, "error": "Directory not found"}
    if not dest_path.is_dir():
        return {"ok": False, "error": "Directory not found"}

    moved, failed = [], []
    state_dirty = False
    # open_state 只在 archive_dir 有值时联动: 整段 load 一次, 逐条改内存, 末尾 save 一次
    open_state = load_open_state(archive_dir) if archive_dir else None
    open_dirty = False
    open_warn_idx = None
    for raw in rels:
        from_text = raw if isinstance(raw, str) else str(raw)
        try:
            src_rel = _norm_rel(raw)
        except ValueError:
            failed.append({"from": from_text, "error": "Invalid path"})
            continue
        if not src_rel:
            failed.append({"from": from_text, "error": "Invalid path"})
            continue
        src_path = root / src_rel
        if not src_path.exists():
            failed.append({"from": src_rel, "error": "Not found"})
            continue
        if src_path.is_dir():
            failed.append({"from": src_rel, "error": "Folders cannot be moved"})
            continue

        name = Path(src_rel).name
        target = dest_path / name
        to_rel = (dest_n + "/" + name) if dest_n else name
        renamed = False
        if src_path == target:
            # 目标就是它自己: 空操作算成功, 不制造 _1 副本
            moved.append({"from": src_rel, "to": to_rel, "renamed": False})
            continue
        if target.exists():
            stem, suffix = os.path.splitext(name)
            i = 1
            while True:
                cand = "%s_%d%s" % (stem, i, suffix)
                cand_path = dest_path / cand
                if not cand_path.exists():
                    target = cand_path
                    to_rel = (dest_n + "/" + cand) if dest_n else cand
                    renamed = True
                    break
                i += 1
        try:
            try:
                os.replace(str(src_path), str(target))
            except OSError:
                shutil.move(str(src_path), str(target))
        except Exception as e:
            failed.append({"from": src_rel, "error": "Failed to move file: " + _err_brief(e)})
            continue

        warn = ""
        if archive_dir:
            try:
                _rewrite_archive_source(
                    archive_dir, src_rel, to_rel,
                    datetime.now().isoformat(timespec="seconds"))
            except Exception as e:
                warn = "archive rewrite failed: " + _err_brief(e)
        if state is not None:
            try:
                _migrate_state_key(state, src_rel, to_rel, target)
                state_dirty = True
            except Exception as e:
                warn = _warn_add(warn, "state migration failed: " + _err_brief(e))
        if open_state is not None:
            k_old = open_key_out(src_rel)
            k_new = open_key_out(to_rel)
            if k_old in open_state:
                try:
                    open_state[k_new] = open_state.pop(k_old)
                    open_dirty = True
                    open_warn_idx = len(moved)
                except Exception as e:
                    warn = _warn_add(warn, "open_state migration failed: " + _err_brief(e))

        entry = {"from": src_rel, "to": to_rel, "renamed": renamed}
        if warn:
            entry["warn"] = warn
        moved.append(entry)

    if state is not None and state_dirty and archive_dir:
        try:
            save_state(archive_dir, state)
        except Exception:
            pass
    if open_state is not None and open_dirty:
        try:
            save_open_state(archive_dir, open_state)
        except Exception as e:
            if open_warn_idx is not None:
                moved[open_warn_idx]["warn"] = _warn_add(
                    moved[open_warn_idx].get("warn", ""),
                    "open_state save failed: " + _err_brief(e))
    return {"ok": True, "moved": moved, "failed": failed,
            "moved_count": len(moved), "failed_count": len(failed)}


def safe_output_path(output_dir, rel):
    """校验 rel 在 output_dir 内且为文件, 返回 Path 或 None"""
    root = _output_root(output_dir)
    if root is None:
        return None
    try:
        rel_n = _norm_rel(rel)
    except ValueError:
        return None
    if not rel_n:
        return None
    try:
        p = _resolve_in(root, rel_n)
    except ValueError:
        return None
    if not p.is_file():
        return None
    return p
