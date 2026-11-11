# -*- coding: utf-8 -*-
"""
ComfyUI 资产管理插件
=====================
集成进 ComfyUI 网页的原生 Tab: 浏览/搜索/日历/预览/删除资产,
切换输出目录(重启后自动恢复), 一键备份(资产库+工作流+配置)。
"""

import asyncio
import os
import sys
import threading

# 保证能 import 同目录的核心库
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import assets_core

WEB_DIRECTORY = "web"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

__version__ = "1.3.4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_cfg = assets_core.load_config(BASE_DIR)
_arch_default, _ = assets_core.default_asset_dirs(BASE_DIR)
_arch = os.path.abspath(_cfg.get("archive_dir") or _arch_default)
os.makedirs(_arch, exist_ok=True)
_state = assets_core.load_state(_arch)
_LOCK = threading.Lock()
_stop = threading.Event()

# 启动时应用配置的输出目录(实现"重启后自动恢复")
try:
    import folder_paths
    _out = (_cfg.get("output_dir") or "").strip()
    if _out:
        os.makedirs(_out, exist_ok=True)
        folder_paths.set_output_directory(os.path.abspath(_out))
except Exception:
    folder_paths = None


def _current_output_dir():
    if folder_paths is not None:
        try:
            return folder_paths.get_output_directory()
        except Exception:
            pass
    return (_cfg.get("output_dir") or "").strip()


def _watch_loop():
    while not _stop.is_set():
        if _cfg.get("auto_archive", True):
            try:
                out = _current_output_dir()
                if out:
                    with _LOCK:
                        assets_core.scan_all(out, _arch, _state, _cfg)
            except Exception:
                pass
        _stop.wait(float(_cfg.get("interval_sec", 10)))


if _cfg.get("auto_archive", True):
    threading.Thread(target=_watch_loop, daemon=True).start()


# ---------------------------------------------------------------------------
# API 路由 (ComfyUI 会自动同时注册 /asset/xxx 与 /api/asset/xxx)
# ---------------------------------------------------------------------------

from server import PromptServer  # noqa: E402
from aiohttp import web  # noqa: E402


async def _json_body(request):
    """读取 JSON 请求体; 失败/非 dict 一律返回 {}"""
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return {}
    return body


# --- v1.2.5: 归档 / 备份目录不得出现在任何"资产"视图里 ---------------------------
def _exclude_dirs():
    """需要整体隐藏的目录(绝对路径): 归档库 + 备份目录"""
    dirs = [os.path.abspath(_arch)]
    bak = (_cfg.get("backup_dir") or "").strip()
    if bak:
        dirs.append(os.path.abspath(bak))
    return dirs


def _skip_source_prefixes():
    """归档/备份目录相对 output 的 POSIX 前缀(仅当其落在 output 内), 供 list_runs 过滤自噬条目"""
    out = _current_output_dir()
    if not out:
        return []
    out_abs = os.path.abspath(out)
    res = []
    for p in _exclude_dirs():
        try:
            rel = os.path.relpath(p, out_abs)
        except ValueError:
            continue
        if rel.startswith(".."):
            continue
        rel = rel.replace(os.sep, "/").strip("/")
        if rel:
            res.append(rel)
    return res


@PromptServer.instance.routes.get("/asset/list")
async def asset_list(request):
    def _go():
        return assets_core.list_runs(_arch, assets_core.load_open_state(_arch),
                                     _skip_source_prefixes())

    runs = await asyncio.to_thread(_go)
    return web.json_response({"ok": True, "count": len(runs), "runs": runs})


@PromptServer.instance.routes.get("/asset/audit")
async def asset_audit(request):
    """v1.2.9 归档库体检: 只读清单(重复来源/不可预览/孤儿/同内容), 零删除。"""
    def _go():
        return assets_core.audit_archive(_arch, _current_output_dir(),
                                         _skip_source_prefixes())

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


# --- 输出目录: 文件夹视图 / 文件夹管理 / 剪切粘贴 (v1.2.0) --------------------

@PromptServer.instance.routes.get("/asset/list_output")
async def asset_list_output(request):
    path = request.rel_url.query.get("path", "")

    def _go():
        return assets_core.list_output(_current_output_dir(), path, _arch,
                                       assets_core.load_open_state(_arch),
                                       _exclude_dirs())

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/folder_tree")
async def asset_folder_tree(request):
    """整个 output 的文件夹树(左栏一次拉全, v1.2.1)"""

    def _go():
        return assets_core.folder_tree(_current_output_dir(),
                                       assets_core.load_open_state(_arch),
                                       exclude_dirs=_exclude_dirs())

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/output_files")
async def asset_output_files(request):
    """某个文件夹下的递归文件清单(供「下载文件夹」用, v1.2.2)"""
    path = request.rel_url.query.get("path", "")

    def _go():
        return assets_core.list_output_files(_current_output_dir(), path,
                                             exclude_dirs=_exclude_dirs())

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/mkdir_output")
async def asset_mkdir_output(request):
    body = await _json_body(request)

    def _go():
        with _LOCK:
            return assets_core.mkdir_output(_current_output_dir(),
                                            body.get("path", ""), body.get("name", ""))

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/rename_output")
async def asset_rename_output(request):
    body = await _json_body(request)

    def _go():
        with _LOCK:
            return assets_core.rename_output(_current_output_dir(),
                                             body.get("path", ""), body.get("name", ""),
                                             _arch, _state)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/delete_output_dir")
async def asset_delete_output_dir(request):
    body = await _json_body(request)

    def _go():
        with _LOCK:
            return assets_core.delete_output_dir(_current_output_dir(),
                                                 body.get("path", ""),
                                                 bool(body.get("recursive", False)),
                                                 _arch)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/delete_output_file")
async def asset_delete_output_file(request):
    """删除 output 下的单个文件(可选连带删归档条目, v1.2.3)"""
    body = await _json_body(request)

    def _go():
        with _LOCK:
            return assets_core.delete_output_file(_current_output_dir(),
                                                  body.get("path", ""),
                                                  _arch, _state)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/move_output")
async def asset_move_output(request):
    body = await _json_body(request)
    rels = body.get("from") or []
    dest = body.get("to") or ""

    def _go():
        with _LOCK:
            return assets_core.move_output(_current_output_dir(), rels, dest, _arch, _state)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/output_file")
async def asset_output_file(request):
    rel = request.rel_url.query.get("p", "")
    p = assets_core.safe_output_path(_current_output_dir(), rel)
    if not p:
        return web.Response(status=404, text="not found")
    return web.FileResponse(p)


@PromptServer.instance.routes.post("/asset/touch_open")
async def asset_touch_open(request):
    body = await _json_body(request)

    def _go():
        with _LOCK:
            return assets_core.touch_open(_arch, body.get("key"))

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/config")
async def asset_config(request):
    _, _bak_default = assets_core.default_asset_dirs(BASE_DIR)
    return web.json_response({
        "ok": True,
        "version": __version__,          # v1.2.4: 前端把它显示在面板标题旁, 便于确认真机跑的是哪一版
        "config": _cfg,
        "archive_dir": _arch,
        "current_output_dir": _current_output_dir(),
        "default_backup_dir": _bak_default,
    })


@PromptServer.instance.routes.post("/asset/set_output_dir")
async def asset_set_output_dir(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    path = (body or {}).get("path", "")
    path = (path or "").strip()
    if not path:
        return web.json_response({"ok": False, "error": "Missing output directory path"})
    path = os.path.abspath(path)
    try:
        os.makedirs(path, exist_ok=True)
        if folder_paths is not None:
            folder_paths.set_output_directory(path)
        _cfg["output_dir"] = path
        assets_core.save_config(BASE_DIR, _cfg)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response({"ok": True, "output_dir": path})


@PromptServer.instance.routes.post("/asset/set_config")
async def asset_set_config(request):
    """保存配置(在面板里修改所有设置): 支持 output_dir/archive_dir/backup_dir/
    auto_archive/thumb_width/interval_sec/ffprobe/ffmpeg"""
    try:
        body = await request.json()
    except Exception:
        body = {}
    updates = dict(body or {})
    errors = []
    new_arch = None

    # 目录类: 规范化 + 建目录
    for key in ("archive_dir", "backup_dir", "output_dir"):
        if key in updates:
            val = (updates[key] or "").strip()
            if key == "output_dir" and not val:
                updates[key] = ""  # 空=恢复 ComfyUI 默认 output
                continue
            if val:
                val = os.path.abspath(val)
                try:
                    os.makedirs(val, exist_ok=True)
                    updates[key] = val
                except Exception as e:
                    errors.append(f"Cannot create {key}: {e}")
                    updates.pop(key, None)
            else:
                updates.pop(key, None)

    # 数值类
    for key in ("thumb_width", "interval_sec"):
        if key in updates:
            try:
                updates[key] = int(updates[key])
                if updates[key] <= 0:
                    raise ValueError
            except Exception:
                errors.append(f"{key} must be a positive integer")
                updates.pop(key, None)

    if "auto_archive" in updates:
        updates["auto_archive"] = bool(updates["auto_archive"])
    if "archive_existing" in updates:
        updates["archive_existing"] = bool(updates["archive_existing"])

    global _arch, _state
    with _LOCK:
        _cfg.update(updates)
        assets_core.save_config(BASE_DIR, _cfg)
        if "archive_dir" in updates:
            new_arch = updates["archive_dir"]
            _arch = new_arch
            _state = assets_core.load_state(new_arch)
        if "output_dir" in updates and updates["output_dir"] and folder_paths is not None:
            folder_paths.set_output_directory(updates["output_dir"])

    return web.json_response({
        "ok": True, "config": _cfg, "archive_dir": _arch,
        "current_output_dir": _current_output_dir(), "errors": errors,
    })


@PromptServer.instance.routes.post("/asset/delete")
async def asset_delete(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    run_id = (body or {}).get("run_id")

    def _go():
        with _LOCK:
            return assets_core.delete_run(_arch, _current_output_dir(), _state, run_id)

    result = await asyncio.to_thread(_go)
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/trash_list")
async def asset_trash_list(request):
    """v1.3.0 回收站清单(只读)"""
    def _go():
        return assets_core.trash_list(_arch)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/trash_restore")
async def asset_trash_restore(request):
    """v1.3.0 恢复回收站批次(或单个 item)到原位"""
    body = await _json_body(request)
    batch = body.get("batch")
    item = body.get("item") or None

    def _go():
        with _LOCK:
            return assets_core.trash_restore(_arch, _current_output_dir(), batch, item)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/trash_purge")
async def asset_trash_purge(request):
    """v1.3.0 永久删除一个回收站批次(前端二次确认后调用)"""
    body = await _json_body(request)
    batch = body.get("batch")

    def _go():
        with _LOCK:
            return assets_core.trash_purge(_arch, batch)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/delete_batch")
async def asset_delete_batch(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    run_ids = (body or {}).get("run_ids") or []
    if not isinstance(run_ids, list):
        return web.json_response({"ok": False, "error": "run_ids must be an array"})

    def _go():
        deleted, failed = 0, []
        with _LOCK:
            for rid in run_ids:
                r = assets_core.delete_run(_arch, _current_output_dir(), _state, rid)
                if r.get("ok"):
                    deleted += 1
                else:
                    failed.append(rid)
        return {"ok": True, "deleted": deleted, "failed": failed}

    result = await asyncio.to_thread(_go)
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/scan")
async def asset_scan(request):
    def _go():
        with _LOCK:
            return assets_core.status_summary(_current_output_dir(), _arch, _state, _cfg,
                                              _skip_source_prefixes())

    n = await asyncio.to_thread(_go)
    return web.json_response(n)


@PromptServer.instance.routes.post("/asset/repair")
async def asset_repair(request):
    """v1.3.1 归档修复: 对齐 source_rel / 重建缺失 info.json / 孤儿标记(不删任何文件)"""
    def _go():
        with _LOCK:
            return assets_core.repair_archive(_arch, _current_output_dir(), _state,
                                              _skip_source_prefixes())

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/cleanup_candidates")
async def asset_cleanup_candidates(request):
    """v1.3.3 清理旧产物: 按天数列出候选(只读清单, 不删)"""
    try:
        days = float(request.rel_url.query.get("days", "0") or 0)
    except Exception:
        days = 0.0

    def _go():
        return assets_core.cleanup_candidates(_arch, days)

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/cleanup_execute")
async def asset_cleanup_execute(request):
    """v1.3.3 清理旧产物: 勾选的条目移入回收站(output 源文件同批)"""
    body = await _json_body(request)
    dirs = body.get("dirs") or []
    if not isinstance(dirs, list):
        return web.json_response({"ok": False, "error": "dirs must be an array"})

    def _go():
        with _LOCK:
            return assets_core.cleanup_execute(_arch, _current_output_dir(), _state, dirs,
                                               _skip_source_prefixes())

    try:
        result = await asyncio.to_thread(_go)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
    return web.json_response(result)


@PromptServer.instance.routes.post("/asset/backup")
async def asset_backup(request):
    def _go():
        wdirs = []
        if folder_paths is not None:
            try:
                ud = folder_paths.get_user_directory()
                w = os.path.join(ud, "default", "workflows")
                if os.path.isdir(w):
                    wdirs.append(w)
            except Exception:
                pass
        return assets_core.backup_assets(_cfg, BASE_DIR, wdirs)

    result = await asyncio.to_thread(_go)
    return web.json_response(result)


@PromptServer.instance.routes.get("/asset/file")
async def asset_file(request):
    rel = request.rel_url.query.get("p", "")
    p = assets_core.safe_media_path(_arch, rel)
    if not p:
        return web.Response(status=404, text="not found")
    return web.FileResponse(p)


@PromptServer.instance.routes.get("/asset/workflow")
async def asset_workflow(request):
    rel = request.rel_url.query.get("p", "")
    p = assets_core.safe_media_path(_arch, rel)
    if not p:
        return web.Response(status=404, text="not found")
    name = os.path.basename(p)
    return web.FileResponse(p, headers={
        "Content-Disposition": f'attachment; filename="{name}"',
    })


def _browsable_roots():
    """允许浏览的目录根(输出/归档/备份目录), 防止浏览任意系统目录"""
    roots = []
    out = _current_output_dir()
    if out:
        roots.append(os.path.abspath(out))
    roots.append(os.path.abspath(_arch))
    bak = (_cfg.get("backup_dir") or "").strip() or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "asset_backups")
    roots.append(os.path.abspath(bak))
    return [r.lower() for r in roots]


def _is_browsable(path):
    """path 必须在允许目录内, 或是某个允许目录的父级链上(用于从盘符导航)"""
    p = os.path.abspath(path).lower()
    if len(p) <= 3:  # 驱动器根, 允许作为起点
        return True
    for r in _browsable_roots():
        if p == r or p.startswith(r + os.sep) or r.startswith(p + os.sep):
            return True
    return False


@PromptServer.instance.routes.get("/asset/browse_dir")
async def asset_browse_dir(request):
    """浏览文件系统目录(供设置里的「浏览…」按钮用), 仅限输出/归档/备份目录及其父级链"""
    import string
    path = request.rel_url.query.get("path", "")
    try:
        if not path:
            drives = [d + ":\\" for d in string.ascii_uppercase if os.path.exists(d + ":\\")]
            return web.json_response({"ok": True, "path": "", "parent": None, "dirs": drives})
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return web.json_response({"ok": False, "error": "Directory not found"})
        if not _is_browsable(path):
            return web.json_response({"ok": False, "error": "Directory is outside the allowed browse scope"})
        parent = os.path.dirname(path)
        if parent == path:
            parent = None
        dirs = sorted([n for n in os.listdir(path) if os.path.isdir(os.path.join(path, n))])
        return web.json_response({"ok": True, "path": path, "parent": parent, "dirs": dirs})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})
