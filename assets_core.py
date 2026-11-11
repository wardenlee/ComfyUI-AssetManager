# -*- coding: utf-8 -*-
"""
ComfyUI 资产管理插件核心库
============================
无 ComfyUI 依赖, 可独立测试。提供: 配置读写 / 元数据提取 / 归档 / 扫描 /
索引列表 / 删除 / 备份 / 媒体文件安全读取。
"""

import json
import os
import re
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

# ---------------------------------------------------------------------------
# v1.2.5: 插件自身产物识别
# 归档目录里每个条目都会带 thumb.jpg / info.json / prompt.txt / workflow.json;
# 这些是"给界面用的元数据与预览图", **不是用户产物**, 任何视图都不该当成资产列出、
# 也不该被再次归档(否则 archive 落在 output 内时会自己归档自己, 越滚越多)。
# ---------------------------------------------------------------------------
THUMB_NAME_RE = re.compile(r"^thumb\.(?:jpe?g|png|webp|gif|bmp)$", re.IGNORECASE)
BACKUP_ZIP_RE = re.compile(r"^comfyui_asset_backup_\d{8}_\d{6}\.zip$", re.IGNORECASE)
RUN_ARTIFACT_NAMES = {"info.json", "prompt.txt", "workflow.json"}
STATE_ARTIFACT_NAMES = {"archive_state.json", "open_state.json"}

# v1.2.6: 浏览器普遍放不出来的视频容器 —— 不出现在任何列表/下载里(数据仍会归档, 只是不可见)
BROWSER_UNPLAYABLE_VIDEO_EXT = {".mkv"}

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

    # v1.2.8: 不再落 workflow.json 散落文件 —— 内嵌元数据已携带工作流(云端对拍 1/1 逐键一致),
    # 预览里可按需从 info.json 的 workflow_json 重组下载; 存量条目磁盘上的 workflow.json 原样保留。
    # has_workflow 仍表示"内嵌工作流元数据存在"(= 可恢复), 与磁盘文件无关。

    state[rel] = state_key
    return {"run": run_dir.name, "dir": run_dir.relative_to(arch).as_posix(), "kind": kind}


def scan_all(output_dir, archive_dir, state, cfg):
    out = Path(output_dir)
    if not out.is_dir():
        return 0
    # v1.2.5: 归档 / 备份目录若落在 output 内, 必须整体跳过 —— 否则会"自己归档自己",
    # 每扫描一轮就在库里多出一批 thumb.jpg / 媒体副本的假条目(实测一次 +6 条并连锁)。
    hidden = hidden_roots(output_dir, [archive_dir, (cfg or {}).get("backup_dir")])
    # 归档目录**就是** output 本身: 一旦扫描就会自己归档自己(无限膨胀) → 直接不扫
    try:
        if archive_dir:
            root_abs = Path(output_dir).resolve()
            if Path(archive_dir).resolve() == root_abs:
                return 0
    except Exception:
        pass
    new_runs = []
    state_changed = False
    archive_existing = bool(cfg.get("archive_existing", False))
    baseline_done = bool(state.get("__baseline_done__", False))
    for root, dirs, files in os.walk(out):
        dirs[:] = [d for d in dirs
                   if not d.startswith(".") and not _is_hidden(Path(root) / d, hidden)]
        for fn in files:
            if fn.startswith("."):
                continue
            if is_artifact_name(fn):
                continue
            # v1.2.7: 半成品后缀(.part/.tmp/.crdownload/.download)与 0 字节媒体是写一半的残留,
            # 不归档也不建基线 —— 等它写完/有内容后再自然进入扫描
            if is_half_written(fn):
                continue
            if Path(fn).suffix.lower() not in ALL_EXT:
                continue
            src = Path(root) / fn
            rel = src.relative_to(out).as_posix()
            try:
                st = os.stat(src)
            except OSError:
                continue
            if st.st_size == 0:
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
                    # v1.3.4: 真机反馈——视频节点先写一版再重写, 两次 scan 各归档一条
                    # (稳定窗只在单次 scan 内有效)。新条目归档成功后, 把同 source_rel 的
                    # 旧条目移入回收站(软删除, 可恢复) —— 库里同源只保留最新条目。
                    _retire_old_runs(rel, r["dir"], archive_dir)
            elif baseline_done or archive_existing:
                # 基线已建立后的新文件, 或用户开启"归档历史" → 归档
                r = archive_file(rel, src, archive_dir, state, cfg)
                if r:
                    new_runs.append(r)
                    _retire_old_runs(rel, r["dir"], archive_dir)
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

def _is_bogus_run(src_rel, media, prefixes):
    """v1.2.5: 判断归档条目是否"插件自己的产物被误当资产"(历史遗留数据)

    - media 是缩略图/元数据这类插件产物名 -> 假条目(旧版扫描曾把 thumb.jpg 归档成一张图)
    - source_rel 的文件名本身是插件产物      -> 假条目
    - source_rel 落在归档/备份目录内(prefixes) -> 假条目(自己归档自己)
    """
    if is_artifact_name(media):
        return True
    src = (src_rel or "").replace("\\", "/").strip()
    if not src:
        return False
    base = src.rsplit("/", 1)[-1]
    if is_artifact_name(base):
        return True
    low = src.lower()
    for p in (prefixes or []):
        if p and low.startswith(p.lower()):
            return True
    return False


def list_runs(archive_dir, open_state=None, skip_source_prefixes=None):
    arch = Path(archive_dir)
    runs = []
    if not arch.is_dir():
        return runs
    if not isinstance(open_state, dict):
        open_state = {}
    # v1.2.5: 归档/备份目录若在 output 内, 其相对前缀由调用方传入 → 这些 source_rel 的条目是自噬产物
    prefixes = []
    for p in (skip_source_prefixes or []):
        s = str(p or "").replace("\\", "/").strip()
        s = s.strip("/")
        if s:
            prefixes.append(s + "/")
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
            if not isinstance(info, dict):
                continue
            # 只隐藏、不删盘: 历史遗留的假条目不再出现在任何视图里
            if _is_bogus_run(info.get("source_rel"), info.get("media"), prefixes):
                continue
            # v1.2.6: 浏览器放不出来的视频容器(.mkv 等)不在网格/日历出现
            if is_unplayable_video(info.get("media")):
                continue
            try:
                files = []
                sizes = {}
                for p in run_dir.iterdir():
                    if not p.is_file():
                        continue
                    files.append(p.name)
                    try:
                        sizes[p.name] = p.stat().st_size
                    except OSError:
                        pass
                files.sort()
            except OSError:
                files = []
            # v1.2.7: 媒体文件缺失或 0 字节的坏条目(无法预览)也不出现在网格/日历
            _media = info.get("media") or ""
            if _media and (sizes.get(_media) is None or sizes.get(_media) == 0):
                continue
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
    """v1.3.0: 删归档条目 = 整批移入回收站(条目本体 + output 源文件), 可恢复。

    对外返回结构与旧版一致(ok/source_rel), 新增 "trash": 批次名。
    """
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

    items = [{"name": run_dir.name, "orig_rel": run_id.replace("\\", "/").strip("/"),
              "size": _audit_dir_stats(run_dir), "kind_detail": "archive-run"}]
    src_file = None
    if source_rel and out:
        cand = (out / source_rel).resolve()
        if str(cand).startswith(str(out) + os.sep) and cand.is_file():
            src_file = cand
            items.append({"name": Path(source_rel).name, "orig_rel": source_rel,
                          "size": cand.stat().st_size, "kind_detail": "output-file"})
    batch = _trash_new_batch(archive_dir, "run", items)
    bdir = _trash_root(archive_dir) / batch
    moved = _trash_move_one(run_dir, bdir / run_dir.name)
    if not moved:
        return {"ok": False, "error": "Failed to move archive entry to trash"}
    if src_file is not None:
        _trash_move_one(src_file, bdir / Path(source_rel).name)
    if source_rel:
        state.pop(source_rel, None)
    save_state(archive_dir, state)
    return {"ok": True, "source_rel": source_rel, "trash": batch}


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
# v1.2.9: 归档库体检(纯只读, §6(C)-①) —— 重复来源 / 不可预览 / 孤儿 / 同内容粗判
# ---------------------------------------------------------------------------

AUDIT_HASH_BYTES = 65536  # 同内容粗判只读媒体副本前 64KB


def _audit_dir_stats(run_dir):
    """条目目录内全部文件的字节合计(体检 totals 用, 只读)。"""
    total = 0
    try:
        for p in run_dir.iterdir():
            if not p.is_file():
                continue
            try:
                total += p.stat().st_size
            except OSError:
                pass
    except OSError:
        pass
    return total


def _audit_hash64k(path):
    """媒体副本前 64KB 的 sha256(十六进制); 文件小于 64KB 就全读。失败返回 None。"""
    try:
        with open(str(path), "rb") as f:
            head = f.read(AUDIT_HASH_BYTES)
        import hashlib
        return hashlib.sha256(head).hexdigest()
    except Exception:
        return None


def audit_archive(archive_dir, output_dir=None, skip_source_prefixes=None):
    """归档库体检: 只读清单, 不写盘、不改状态、不删任何东西(§6(C)-①)。

    与 list_runs 不同, 体检**遍历全部条目**(含被 v1.2.5/1.2.7 隐藏的坏账):
    - dup_source:   source_rel 相同的条目组(count>=2), 标最早/最新与组内占用
    - unplayable:   媒体缺失 / 0 字节 / 浏览器放不出的容器(.mkv 等)
    - orphans:      source_rel 指向的 output 文件已不存在(需传 output_dir)
    - same_content: 媒体副本 (size, 前64KB sha256) 相同的组(组内 >=2 才列)
    """
    arch = Path(archive_dir)
    if not arch.is_dir():
        return {"ok": False, "error": "Directory not found"}
    prefixes = []
    for p in (skip_source_prefixes or []):
        s = str(p or "").replace("\\", "/").strip().strip("/")
        if s:
            prefixes.append(s + "/")
    out_root = None
    if output_dir:
        try:
            cand = Path(output_dir)
            out_root = cand if cand.is_dir() else None
        except Exception:
            out_root = None

    entries = []
    total_bytes = 0
    skipped = 0
    try:
        date_dirs = list(arch.iterdir())
    except OSError:
        date_dirs = []
    for date_dir in date_dirs:
        if not date_dir.is_dir():
            continue
        try:
            run_dirs = list(date_dir.iterdir())
        except OSError:
            continue
        for run_dir in run_dirs:
            if not run_dir.is_dir():
                continue
            info_file = run_dir / "info.json"
            if not info_file.is_file():
                continue
            try:
                info = json.loads(info_file.read_text(encoding="utf-8"))
            except Exception:
                skipped += 1
                continue
            if not isinstance(info, dict):
                skipped += 1
                continue
            media = info.get("media") or ""
            media_path = (run_dir / media) if media else None
            has_media = bool(media_path and media_path.is_file())
            media_size = 0
            if has_media:
                try:
                    media_size = media_path.stat().st_size
                except OSError:
                    has_media = False
            dir_bytes = _audit_dir_stats(run_dir)
            total_bytes += dir_bytes
            rel = run_dir.relative_to(arch).as_posix()
            entries.append({
                "dir": rel,
                "source_rel": info.get("source_rel") or "",
                "media": media,
                "has_media": has_media,
                "media_size": media_size if has_media else 0,
                "kind": info.get("kind") or "image",
                "generated_at": info.get("generated_at") or "",
                "dir_bytes": dir_bytes,
            })

    # 1) 重复 source_rel 组
    by_src = {}
    for e in entries:
        src = e["source_rel"]
        if src:
            by_src.setdefault(src, []).append(e)
    dup_source = []
    for src, group in by_src.items():
        if len(group) < 2:
            continue
        times = sorted([e["generated_at"] for e in group if e["generated_at"]])
        dup_source.append({
            "source_rel": src,
            "count": len(group),
            "bytes": sum(e["dir_bytes"] for e in group),
            "oldest": times[0] if times else "",
            "newest": times[-1] if times else "",
            "dirs": [e["dir"] for e in group],
        })
    dup_source.sort(key=lambda g: -g["bytes"])

    # 2) 不可预览条目(含被视图隐藏的坏账)
    unplayable = []
    for e in entries:
        if not e["media"]:
            reason = "media-missing"
        elif not e["has_media"]:
            reason = "media-missing"
        elif e["media_size"] == 0:
            reason = "media-zero-byte"
        elif is_unplayable_video(e["media"]):
            reason = "unplayable-container"
        else:
            continue
        unplayable.append({"dir": e["dir"], "media": e["media"], "reason": reason,
                           "source_rel": e["source_rel"]})

    # 3) 孤儿条目(source_rel 指向的 output 文件已不存在)
    orphans = []
    if out_root is not None:
        for e in entries:
            src = e["source_rel"]
            if not src:
                continue
            low = src.replace("\\", "/").lower()
            if any(low.startswith(p.lower()) for p in prefixes):
                continue
            try:
                if (out_root / src.replace("\\", "/")).exists():
                    continue
            except OSError:
                continue
            orphans.append({"dir": e["dir"], "source_rel": src, "reason": "output-missing"})

    # 4) 同内容粗判(size + 前 64KB hash); 坏账(缺媒体/0字节)不参与
    by_content = {}
    for e in entries:
        if not e["has_media"] or e["media_size"] == 0:
            continue
        h = _audit_hash64k(Path(archive_dir) / e["dir"] / e["media"])
        if not h:
            continue
        key = (e["media_size"], h)
        by_content.setdefault(key, []).append(e)
    same_content = []
    for (size, h), group in by_content.items():
        if len(group) < 2:
            continue
        same_content.append({
            "size": size,
            "hash64k": h,
            "bytes": sum(e["dir_bytes"] for e in group),
            "dirs": [e["dir"] for e in group],
        })
    same_content.sort(key=lambda g: -g["bytes"])

    return {"ok": True,
            "totals": {"runs": len(entries), "bytes": total_bytes},
            "dup_source": dup_source,
            "unplayable": unplayable,
            "orphans": orphans,
            "same_content": same_content,
            "skipped": skipped}


# ---------------------------------------------------------------------------
# v1.3.0: 统一可回滚软删除(§6(C)-②) —— 三条删除路径统一移入 <archive_dir>/_trash
# ---------------------------------------------------------------------------

TRASH_DIR_NAME = "_trash"


def _trash_root(archive_dir):
    """回收站根目录: <archive_dir>/_trash"""
    return Path(archive_dir) / TRASH_DIR_NAME


def _trash_new_batch(archive_dir, kind, items, when=None):
    """新建一个回收站批次目录并写入 manifest; items 已由调用方移入。

    items: [{"name": 批次内文件/目录名, "orig_rel": 原相对路径, "size": n, "kind_detail": str|None}]
    """
    root = _trash_root(archive_dir)
    root.mkdir(parents=True, exist_ok=True)
    when_dt = None
    if when:
        try:
            when_dt = datetime.fromisoformat(str(when))
        except Exception:
            when_dt = None
    if when_dt is None:
        when_dt = datetime.now()
    stamp = when_dt.strftime("%Y%m%d-%H%M%S")
    batch = stamp + "_" + kind
    n = 2
    while (root / batch).exists():
        batch = stamp + "_" + kind + "_" + str(n)
        n += 1
    bdir = root / batch
    bdir.mkdir()
    manifest = {"batch": batch, "when": when_dt.isoformat(timespec="seconds"),
                "kind": kind, "count": len(items), "items": items}
    (bdir / "trash_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return batch


def _trash_move_one(src, dst):
    """把 src 移到 dst; 同盘 shutil.move, 失败 fallback 复制+删原。"""
    try:
        shutil.move(str(src), str(dst))
        return True
    except OSError:
        pass
    try:
        if Path(src).is_dir():
            shutil.copytree(str(src), str(dst))
            shutil.rmtree(str(src))
        else:
            shutil.copy2(str(src), str(dst))
            os.remove(str(src))
        return True
    except OSError:
        return False


def _retire_old_runs(source_rel, new_dir, archive_dir):
    """v1.3.4: 同 source_rel 重归档后, 把旧条目移入回收站(软删除, 可恢复)。

    只在【新条目归档成功后】由 scan_all 调用; 直接扫 <日期>/<run>/info.json
    (覆盖 list_runs 隐藏的坏条目); 任一失败不影响其余。
    """
    arch = Path(archive_dir)
    if not arch.is_dir():
        return
    rel_new = str(new_dir or "").replace("\\", "/").strip("/")
    try:
        date_dirs = [d for d in arch.iterdir() if d.is_dir() and d.name != TRASH_DIR_NAME]
    except OSError:
        return
    for date_dir in date_dirs:
        try:
            run_dirs = list(date_dir.iterdir())
        except OSError:
            continue
        for run_dir in run_dirs:
            if not run_dir.is_dir():
                continue
            rel_old = run_dir.relative_to(arch).as_posix()
            if rel_old == rel_new:
                continue
            info_file = run_dir / "info.json"
            if not info_file.is_file():
                continue
            try:
                info = json.loads(info_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(info, dict):
                continue
            if (info.get("source_rel") or "") != source_rel:
                continue
            items = [{"name": run_dir.name, "orig_rel": rel_old,
                      "size": _audit_dir_stats(run_dir), "kind_detail": "archive-run"}]
            try:
                batch = _trash_new_batch(archive_dir, "run", items)
            except Exception:
                continue
            _trash_move_one(run_dir, _trash_root(archive_dir) / batch / run_dir.name)


def trash_list(archive_dir):
    """回收站批次清单(新→旧), 每批含件数/占用/内容摘要。只读。"""
    root = _trash_root(archive_dir)
    batches = []
    if not root.is_dir():
        return {"ok": True, "batches": []}
    try:
        dirs = [p for p in root.iterdir() if p.is_dir()]
    except OSError:
        return {"ok": True, "batches": []}
    for bdir in dirs:
        mf = bdir / "trash_manifest.json"
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(manifest, dict):
            continue
        items = []
        total = 0
        for it in (manifest.get("items") or []):
            if not isinstance(it, dict):
                continue
            size = 0
            try:
                p = bdir / it.get("name")
                if p.is_file():
                    size = p.stat().st_size
                elif p.is_dir():
                    size = _audit_dir_stats(p)
            except OSError:
                pass
            total += size
            items.append({"name": it.get("name") or "", "orig_rel": it.get("orig_rel") or "",
                          "size": size})
        batches.append({"batch": manifest.get("batch") or bdir.name,
                        "when": manifest.get("when") or "",
                        "kind": manifest.get("kind") or "run",
                        "count": len(items),
                        "bytes": total,
                        "items": items})
    batches.sort(key=lambda b: b.get("when") or "", reverse=True)
    return {"ok": True, "batches": batches}


def trash_restore(archive_dir, output_dir, batch, item=None):
    """恢复一个批次(或其中单个 item)到原位; 目标已存在同名 -> ok False。"""
    root = _trash_root(archive_dir)
    bdir = (root / str(batch)).resolve()
    if bdir == root.resolve() or not str(bdir).startswith(str(root.resolve()) + os.sep):
        return {"ok": False, "error": "Invalid batch"}
    mf = bdir / "trash_manifest.json"
    if not mf.is_file():
        return {"ok": False, "error": "Batch not found"}
    try:
        manifest = json.loads(mf.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "Manifest unreadable"}
    entries = manifest.get("items") or []
    if item:
        entries = [e for e in entries if isinstance(e, dict) and e.get("name") == item]
        if not entries:
            return {"ok": False, "error": "Item not found"}
    restored, failed = 0, []
    out_root = Path(output_dir).resolve() if output_dir else None
    for e in entries:
        name = e.get("name") or ""
        orig_rel = (e.get("orig_rel") or "").replace("\\", "/").strip("/")
        src = bdir / name
        if not name or not src.exists():
            failed.append(name)
            continue
        # v1.3.0 修正: 按 item 的 kind_detail 分流(一个 run 批次里混有归档条目与 output 源文件),
        # 不能按 manifest.kind 一刀切 —— 否则 output 源文件会被错误恢复进归档库。
        detail = e.get("kind_detail") or ""
        if detail == "archive-run":
            # 恢复条目目录回归档库原位: orig_rel 形如 <date>/<run_id>
            if not orig_rel or ".." in orig_rel.split("/"):
                failed.append(name)
                continue
            dst = Path(archive_dir) / orig_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
        else:
            # output_file / output_dir: 恢复回 output 原位
            if not orig_rel or out_root is None or ".." in orig_rel.split("/"):
                failed.append(name)
                continue
            dst = out_root / orig_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            failed.append(name)
            continue
        if _trash_move_one(src, dst):
            restored += 1
        else:
            failed.append(name)
    # 全部恢复成功的批次目录清理; 部分成功则重写 manifest 保留剩余
    if not failed and not item:
        try:
            shutil.rmtree(str(bdir))
        except OSError:
            pass
    elif restored:
        rest = [e for e in (manifest.get("items") or [])
                if isinstance(e, dict) and e.get("name") not in set(
                    x for x in [e2.get("name") for e2 in entries])]
        if not rest:
            try:
                shutil.rmtree(str(bdir))
            except OSError:
                pass
        else:
            manifest["items"] = rest
            manifest["count"] = len(rest)
            try:
                mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                              encoding="utf-8")
            except OSError:
                pass
    return {"ok": not failed, "restored": restored, "failed": failed}


def trash_purge(archive_dir, batch):
    """永久删除一个回收站批次(前端二次确认后调用)。"""
    root = _trash_root(archive_dir).resolve()
    bdir = (root / str(batch)).resolve()
    if bdir == root or not str(bdir).startswith(str(root) + os.sep):
        return {"ok": False, "error": "Invalid batch"}
    if not bdir.is_dir():
        return {"ok": False, "error": "Batch not found"}
    try:
        shutil.rmtree(str(bdir))
    except OSError as e:
        return {"ok": False, "error": "Failed to purge: " + _err_brief(e)}
    return {"ok": True, "batch": batch}


# ---------------------------------------------------------------------------
# v1.3.1: 归档状态汇总 + 修复(§6(C)-③) —— 对齐 source_rel / 重建 info.json / 标孤立
# ---------------------------------------------------------------------------

def status_summary(archive_dir, output_dir, state, cfg, skip_source_prefixes=None):
    """一次扫描 + 状态汇总: 新增 N / 跳过 M 残留 / K 条归档失效(孤儿)。

    "归档失效" = 库中条目的 source_rel 指向的 output 文件已不存在(不自动删,
    由 repair_archive 标记或由用户在体检里处理)。
    """
    stats = {}
    out = Path(output_dir) if output_dir else None
    if out is not None and not out.is_dir():
        out = None
    n_new = scan_all(output_dir, archive_dir, state, cfg) if output_dir else 0
    # v1.3.1 修正: scan_all 签名冻结(§2.5 A12), 残留计数独立轻量统计(一次 os.walk, 同判据)
    skipped = 0
    if out is not None:
        try:
            hidden = hidden_roots(output_dir, [archive_dir, (cfg or {}).get("backup_dir")])
        except Exception:
            hidden = set()
        for root, dirs, files in os.walk(out):
            dirs[:] = [d for d in dirs
                       if not d.startswith(".") and not _is_hidden(Path(root) / d, hidden)]
            for fn in files:
                if fn.startswith("."):
                    continue
                if is_artifact_name(fn) or is_half_written(fn):
                    skipped += 1
                    continue
                if Path(fn).suffix.lower() not in ALL_EXT:
                    skipped += 1
                    continue
                try:
                    if (Path(root) / fn).stat().st_size == 0:
                        skipped += 1
                except OSError:
                    pass
    # 孤儿 = 可见条目里 source_rel 在 output 已不存在的
    broken = 0
    prefixes = []
    for p in (skip_source_prefixes or []):
        s = str(p or "").replace("\\", "/").strip().strip("/")
        if s:
            prefixes.append(s.lower() + "/")
    for r in list_runs(archive_dir):
        src = (r or {}).get("source_rel") or ""
        if not src:
            continue
        low = src.replace("\\", "/").lower()
        if any(low.startswith(p) for p in prefixes):
            continue
        if out is None or not (out / src.replace("\\", "/")).exists():
            broken += 1
    return {"ok": True, "new": n_new, "skipped": skipped, "broken": broken}


def repair_archive(archive_dir, output_dir, state, skip_source_prefixes=None):
    """修复归档库(幂等, 不删任何文件):

    1) relink: output 里同一文件被改名/移动后, 归档条目的 source_rel 落空 ——
       用"归档媒体副本的字节数 == output 中某无主文件字节数 且 旧 rel 已不存在
       且新 rel 尚无归档条目"三重条件判定, 改写 info.json 的 source_rel + state 键迁移。
    2) rebuild: 条目目录缺 info.json 但有媒体文件 -> 按文件名/时间重建最小 info
       (source_rel 置空 = 视为孤立, 不猜测归属)。
    3) mark-orphan: source_rel 落空的条目在 info.json 写 "orphan": true(不删)。
    """
    arch = Path(archive_dir)
    if not arch.is_dir():
        return {"ok": False, "error": "Directory not found"}
    out = Path(output_dir).resolve() if output_dir else None
    relinked, rebuilt, marked = 0, 0, 0
    details = []
    prefixes = []
    for p in (skip_source_prefixes or []):
        s = str(p or "").replace("\\", "/").strip().strip("/")
        if s:
            prefixes.append(s.lower() + "/")

    index = _archive_index(archive_dir)   # source_rel -> {dir, thumb, media}

    # 收集 output 现存文件清单(rel -> size), 供 relink 匹配
    out_files = {}
    if out is not None and out.is_dir():
        for root, dirs, files in os.walk(out):
            dirs[:] = [d for d in dirs
                       if not d.startswith(".") and not _is_hidden(Path(root) / d, hidden_roots(str(out), [str(arch)]))]
            for fn in files:
                if fn.startswith(".") or is_artifact_name(fn):
                    continue
                fp = Path(root) / fn
                try:
                    out_files[fp.relative_to(out).as_posix()] = fp.stat().st_size
                except OSError:
                    pass

    claimed = set(index.keys())   # 已有归档条目的 source_rel(新版含孤儿)

    for date_dir in sorted(arch.iterdir()):
        if not date_dir.is_dir() or date_dir.name == TRASH_DIR_NAME:
            continue
        for run_dir in sorted(date_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            info_file = run_dir / "info.json"
            media_files = []
            try:
                for p in run_dir.iterdir():
                    if p.is_file() and not is_artifact_name(p.name):
                        media_files.append(p)
            except OSError:
                continue

            # (2) 重建缺失 info.json
            if not info_file.is_file():
                if media_files:
                    m0 = media_files[0]
                    try:
                        st0 = m0.stat()
                    except OSError:
                        continue
                    info = {"run_id": run_dir.name,
                            "archived_at": _iso_ts(st0.st_ctime),
                            "generated_at": _iso_ts(st0.st_mtime),
                            "source_rel": "", "media": m0.name,
                            "kind": _kind_of(m0.name),
                            "file_size": st0.st_size,
                            "positive": "", "negative": "", "prompt_nodes": [],
                            "params": {}, "models": [], "has_workflow": False,
                            "thumb": None, "orphan": True,
                            "rebuilt": True}
                    info_file.write_text(json.dumps(info, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
                    rebuilt += 1
                    details.append({"dir": run_dir.relative_to(arch).as_posix(),
                                    "action": "rebuilt-info"})
                continue

            try:
                info = json.loads(info_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(info, dict):
                continue
            src = (info.get("source_rel") or "").replace("\\", "/").strip("/")
            if not src:
                continue
            low = src.lower()
            if any(low.startswith(p) for p in prefixes):
                continue

            src_path = (out / src.replace("\\", "/")) if out is not None else None
            if src_path is not None and src_path.exists():
                # 一切正常; 若之前标记过孤儿, 摘掉
                if info.get("orphan"):
                    info.pop("orphan", None)
                    info_file.write_text(json.dumps(info, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
                continue

            # (3) 孤儿标记 + (1) 尝试 relink
            msize = None
            try:
                m = run_dir / (info.get("media") or "")
                if m.is_file():
                    msize = m.stat().st_size
            except OSError:
                msize = None
            new_rel = None
            if msize is not None and out is not None:
                for rel_c, sz in out_files.items():
                    if sz != msize or rel_c in claimed:
                        continue
                    new_rel = rel_c
                    break
            if new_rel:
                info["source_rel"] = new_rel
                info.pop("orphan", None)
                info_file.write_text(json.dumps(info, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
                if src in state:
                    state[new_rel] = state.pop(src)
                claimed.add(new_rel)
                relinked += 1
                details.append({"dir": run_dir.relative_to(arch).as_posix(),
                                "action": "relinked", "from": src, "to": new_rel})
            else:
                if not info.get("orphan"):
                    info["orphan"] = True
                    info_file.write_text(json.dumps(info, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
                    marked += 1
                    details.append({"dir": run_dir.relative_to(arch).as_posix(),
                                    "action": "marked-orphan", "source_rel": src})

    if relinked:
        try:
            save_state(archive_dir, state)
        except Exception:
            pass
    return {"ok": True, "relinked": relinked, "rebuilt": rebuilt,
            "marked": marked, "details": details[:50]}


# ---------------------------------------------------------------------------
# v1.3.3: 清理旧产物(§6(C)-⑤) —— 按天数出可勾选清单, 确认后整条目移入回收站
# ---------------------------------------------------------------------------

def cleanup_candidates(archive_dir, max_age_days):
    """按"归档时间早于 max_age_days 天"列出候选条目(只读, 不删)。

    判据用 info.json 的 generated_at(产物生成时间), 缺失时退回 archived_at。
    -> {"ok": True, "max_age_days": N, "count": M, "bytes": B,
        "items": [{"dir", "source_rel", "generated_at", "bytes"}...]}  (旧→新)
    """
    arch = Path(archive_dir)
    if not arch.is_dir():
        return {"ok": False, "error": "Directory not found"}
    try:
        days = float(max_age_days)
    except Exception:
        return {"ok": False, "error": "Invalid max_age_days"}
    if days <= 0:
        return {"ok": False, "error": "Invalid max_age_days"}
    cutoff = time.time() - days * 86400.0
    items = []
    for date_dir in sorted(arch.iterdir()):
        if not date_dir.is_dir() or date_dir.name == TRASH_DIR_NAME:
            continue
        for run_dir in sorted(date_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            info_file = run_dir / "info.json"
            if not info_file.is_file():
                continue
            try:
                info = json.loads(info_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(info, dict):
                continue
            ts_text = info.get("generated_at") or info.get("archived_at") or ""
            try:
                when = datetime.fromisoformat(str(ts_text)).timestamp()
            except Exception:
                continue
            if when > cutoff:
                continue
            items.append({
                "dir": run_dir.relative_to(arch).as_posix(),
                "source_rel": info.get("source_rel") or "",
                "generated_at": ts_text,
                "bytes": _audit_dir_stats(run_dir),
            })
    return {"ok": True, "max_age_days": days, "count": len(items),
            "bytes": sum(i["bytes"] for i in items), "items": items}


def cleanup_execute(archive_dir, output_dir, state, dirs, skip_source_prefixes=None):
    """把勾选的归档条目(逐个 run_rel)移入回收站; 其 output 源文件一并移入同批。

    dirs: [run_rel, ...]; 逐条走 delete_run 的批次逻辑(与手动删除同一安全语义)。
    -> {"ok": True, "cleaned": n, "failed": [run_rel...], "trash": <最后批次名|None>}
    """
    if not isinstance(dirs, list):
        return {"ok": False, "error": "dirs must be an array"}
    cleaned, failed = 0, []
    last_batch = None
    for rd in dirs:
        if not isinstance(rd, str) or not rd.strip():
            failed.append(rd)
            continue
        r = delete_run(archive_dir, output_dir, state, rd)
        if r.get("ok"):
            cleaned += 1
            last_batch = r.get("trash")
        else:
            failed.append(rd)
    return {"ok": not failed, "cleaned": cleaned, "failed": failed, "trash": last_batch}



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


# ---------------------------------------------------------------------------
# v1.2.5: 插件产物 / 隐藏目录守卫
# ---------------------------------------------------------------------------

def is_artifact_name(name):
    """是否是插件自己生成的辅助文件(缩略图 / 元数据 / 状态 / 备份包) —— 不是用户产物"""
    if not isinstance(name, str):
        return False
    n = name.strip()
    if not n:
        return False
    low = n.lower()
    if low in RUN_ARTIFACT_NAMES or low in STATE_ARTIFACT_NAMES:
        return True
    if THUMB_NAME_RE.match(low):
        return True
    if BACKUP_ZIP_RE.match(low):
        return True
    return False


def is_unplayable_video(name):
    """浏览器普遍放不出来的视频容器(如 .mkv) —— 不出现在列表/下载/树里(数据仍会归档)"""
    if not isinstance(name, str):
        return False
    n = name.strip()
    if not n:
        return False
    return Path(n).suffix.lower() in BROWSER_UNPLAYABLE_VIDEO_EXT


# v1.2.7: 半成品后缀(下载中/临时文件) —— 不出现在列表/下载里, 也不归档
HALF_WRITTEN_SUFFIXES = {".part", ".tmp", ".crdownload", ".download"}


def is_half_written(name):
    """是否是写一半的半成品文件(.part / .tmp / .crdownload / .download)"""
    if not isinstance(name, str):
        return False
    n = name.strip()
    if not n:
        return False
    return Path(n).suffix.lower() in HALF_WRITTEN_SUFFIXES


def is_junk_media(name, size):
    """媒体文件但 size==0 —— 写一半崩了留下的残留, 不出现在列表/归档"""
    try:
        return int(size) == 0 and _kind_of(name) != "other"
    except Exception:
        return False


def hidden_roots(output_dir, extra_dirs=None):
    """output 之内需要整体隐藏的绝对路径(归档库 / 备份目录落在 output 里时)

    返回 set[Path]。**只收 output 的严格子目录** —— 若某个目录恰好等于 output 本身,
    这里不收(否则整个 output 会被判隐藏, 列表全空、扫描停摆)。
    "归档目录 == 输出目录"这种极端情况由调用方(scan_all)单独拦。
    """
    root = _output_root(output_dir)
    hidden = set()
    if root is None:
        return hidden
    for d in (extra_dirs or []):
        if not d:
            continue
        try:
            p = Path(d).resolve()
        except Exception:
            continue
        if p == root:
            continue
        if str(p).startswith(str(root) + os.sep):
            hidden.add(p)
    return hidden


def _is_hidden(path_obj, hidden):
    """path 是否等于、或位于某个隐藏根之内"""
    if not hidden:
        return False
    try:
        p = Path(path_obj).resolve()
    except Exception:
        return False
    for h in hidden:
        if p == h or str(p).startswith(str(h) + os.sep):
            return True
    return False


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


def list_output(output_dir, rel="", archive_dir=None, open_state=None, exclude_dirs=None):
    """列出 output 下某目录的直接子项(跳过 . 开头项与插件产物, 不排序)"""
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    hidden = hidden_roots(output_dir, [archive_dir] + list(exclude_dirs or []))
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
        # v1.2.5: 归档 / 备份目录整体不展示
        if _is_hidden(Path(target) / name, hidden):
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
        # v1.2.5: 插件产物(thumb.* / info.json / prompt.txt / workflow.json / 备份 zip)不是资产, 不展示
        if is_artifact_name(name):
            continue
        # v1.2.6: 浏览器放不出来的视频容器(.mkv 等)不在列表/预览里出现
        if is_unplayable_video(name):
            continue
        # v1.2.7: 半成品后缀(.part/.tmp/…)不展示
        if is_half_written(name):
            continue
        size, created, mtime = 0, "", ""
        try:
            st = e.stat(follow_symlinks=False)
            size = int(st.st_size)
            created = _iso_ts(st.st_ctime)
            mtime = _iso_ts(st.st_mtime)
        except OSError:
            pass
        # v1.2.7: 0 字节媒体文件(写一半的残留)不展示
        if is_junk_media(name, size):
            continue
        ext = Path(name).suffix.lower()
        kind = "image" if ext in IMAGE_EXT else ("video" if ext in VIDEO_EXT else "other")
        run = index.get(child_rel) or {}
        # v1.3.1: 归档状态角标 —— archived=库中有该文件的归档条目; missing-info=从未归档。
        # (broken 态不可达: index 来自 list_runs, 坏条目已被 v1.2.7 隐藏, 孤儿检测归体检/修复)
        run_dir_val = run.get("dir") or ""
        arch_state = "archived" if run_dir_val else "missing-info"
        files.append({
            "name": name,
            "rel": child_rel,
            "kind": kind,
            "size": size,
            "created": created,
            "mtime": mtime,
            "opened": open_state.get(open_key_out(child_rel)) or "",
            "run_dir": run_dir_val,
            "thumb": run.get("thumb") or "",
            "media": run.get("media") or "",
            "arch_state": arch_state,
        })
    if rel_n == "":
        parent = None
    else:
        parent = rel_n.rsplit("/", 1)[0] if "/" in rel_n else ""
    return {"ok": True, "path": rel_n, "abs": str(target), "parent": parent,
            "dirs": dirs, "files": files}


def folder_tree(output_dir, open_state=None, max_depth=8, max_nodes=2000, exclude_dirs=None):
    """output 目录的完整文件夹树(只含目录), 供左栏一次拉全(v1.2.1 §2.6)

    - 一趟递归: 每个目录只 os.scandir 一次, 自底向上累计递归 file_count(无 O(n^2))
    - 跳过以 "." 开头的目录; 超 max_depth / max_nodes -> truncated=True 并停止深入(不报错)
    - v1.2.5: 归档 / 备份目录(exclude_dirs, 落在 output 内时)整棵不出现, 其内文件也不计数
    """
    root = _output_root(output_dir)
    if root is None or not root.is_dir():
        return {"ok": False, "error": "Directory not found"}
    hidden = hidden_roots(output_dir, list(exclude_dirs or []))
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
            # v1.2.5: 归档 / 备份目录整棵不出现; 插件产物文件不计数
            if _is_hidden(Path(path) / name, hidden):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    dir_entries.append(e)
                elif e.is_file(follow_symlinks=False):
                    if is_artifact_name(name) or is_unplayable_video(name) or is_half_written(name):
                        continue
                    try:
                        if is_junk_media(name, e.stat(follow_symlinks=False).st_size):
                            continue
                    except OSError:
                        pass
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


def list_output_files(output_dir, rel="", max_files=5000, exclude_dirs=None):
    """递归列出 rel 文件夹下的所有文件(v1.2.2, 供「下载文件夹」用)

    -> {"ok","path","truncated","count","files":[{"rel","name","kind","size","mtime"}]}
    files[].rel 相对 output 根; 跳过 "." 开头的文件与目录; 超 max_files 置 truncated 并停止。
    v1.2.5: 归档 / 备份目录整棵排除, 插件产物文件(thumb.* / info.json / …)不参与下载。
    """
    root = _output_root(output_dir)
    if root is None:
        return {"ok": False, "error": "Directory not found"}
    hidden = hidden_roots(output_dir, list(exclude_dirs or []))
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
        if is_artifact_name(target.name) or is_unplayable_video(target.name) or _is_hidden(target, hidden):
            return {"ok": False, "error": "Directory not found"}
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
        dirs[:] = [d for d in dirs
                   if not d.startswith(".") and not _is_hidden(Path(cur) / d, hidden)]
        for nm in names:
            if nm.startswith(".") or is_artifact_name(nm) or is_half_written(nm):
                continue
            # v1.2.6: 浏览器放不出来的视频容器不参与下载
            if is_unplayable_video(nm):
                continue
            if len(files) >= limit:
                truncated = True
                break
            fp = Path(cur) / nm
            try:
                st = fp.stat()
            except OSError:
                continue
            # v1.2.7: 0 字节媒体不参与下载
            if is_junk_media(nm, st.st_size):
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


def delete_output_dir(output_dir, rel="", recursive=False, archive_dir=None):
    """删除 output 下的文件夹。

    v1.3.0: 传 archive_dir 时移入回收站(可恢复); 不传 archive_dir 时保持旧的两步
    删除语义直接抹盘(向后兼容旧调用, 但路由层恒传 archive_dir)。
    """
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
    # v1.3.0: 传了 archive_dir 就移入回收站(可恢复); 未传 = 旧直接删除语义
    if archive_dir:
        items = [{"name": target.name, "orig_rel": rel_n,
                  "size": n_files, "kind_detail": "output-dir"}]
        batch = _trash_new_batch(archive_dir, "output_dir", items)
        bdir = _trash_root(archive_dir) / batch
        if not _trash_move_one(target, bdir / target.name):
            return {"ok": False, "error": "Failed to move folder to trash"}
        return {"ok": True, "files": n_files, "trash": batch}
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

    # v1.3.0: 传了 archive_dir 就移入回收站(可恢复); 未传 = 旧直接删除语义(向后兼容 v1.2.3 调用)
    if not archive_dir:
        try:
            target.unlink()
        except OSError as e:
            return {"ok": False, "error": "Failed to delete file: " + _err_brief(e)}
        return {"ok": True, "rel": rel_n, "archives_removed": 0}

    items = [{"name": target.name, "orig_rel": rel_n,
              "size": target.stat().st_size,
              "kind_detail": "output-file"}]
    batch = _trash_new_batch(archive_dir, "output_file", items)
    bdir = _trash_root(archive_dir) / batch
    if not _trash_move_one(target, bdir / target.name):
        return {"ok": False, "error": "Failed to move file to trash"}

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
            # v1.3.0: 连带的归档条目也移入回收站(不再直接 rmtree)
            run_dir = fp.parent
            it = [{"name": run_dir.name,
                   "orig_rel": run_dir.relative_to(arch).as_posix(),
                   "size": _audit_dir_stats(run_dir), "kind_detail": "archive-run"}]
            b2 = _trash_new_batch(archive_dir, "run", it)
            _trash_move_one(run_dir, _trash_root(archive_dir) / b2 / run_dir.name)
            removed += 1
    if state is not None:
        state.pop(rel_n, None)
        if archive_dir:
            try:
                save_state(archive_dir, state)
            except Exception:
                pass
    return {"ok": True, "rel": rel_n, "archives_removed": removed, "trash": batch}


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
