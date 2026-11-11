const app = window.comfyAPI.app.app;
const $el = window.comfyAPI.ui.$el;
const ComfyButton = window.comfyAPI.button.ComfyButton;

const STYLE = `
.asm-overlay { position:fixed; inset:0; z-index:9999; background:rgba(0,0,0,.55); display:none; align-items:center; justify-content:center; }
.asm-panel { width:94vw; height:92vh; max-width:1600px; background:var(--comfy-menu-bg, #202020); border:1px solid var(--border-color, #444); border-radius:10px; display:flex; flex-direction:column; overflow:hidden; color:var(--fg-color, #eee); font-family:var(--font-family, sans-serif); }
.asm-header { display:flex; align-items:center; gap:10px; padding:10px 14px; border-bottom:1px solid var(--border-color,#444); }
.asm-header h2 { font-size:15px; margin:0; font-weight:600; }
.asm-header .sp { flex:1; }
.asm-x { background:none; border:none; color:var(--fg-color,#eee); font-size:20px; cursor:pointer; }
.asm-toolbar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; padding:10px 14px; border-bottom:1px solid var(--border-color,#444); }
.asm-search { flex:0 0 170px; background:var(--comfy-input-bg,#333); border:1px solid var(--border-color,#444); color:var(--input-text,#eee); border-radius:6px; padding:6px 10px; font-size:13px; }
.asm-btn { background:var(--comfy-input-bg,#333); border:1px solid var(--border-color,#444); color:var(--fg-color,#eee); border-radius:6px; padding:6px 12px; cursor:pointer; font-size:13px; }
.asm-btn.on { border-color:var(--comfy-menu-bg, #5b8cff); color:#5b8cff; }
.asm-btn.primary { background:#2368b0; border-color:#2368b0; color:#fff; }
.asm-btn.danger { background:#b3372f; border-color:#b3372f; color:#fff; }
.asm-body { flex:1; overflow:auto; padding:14px; }
.asm-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:12px; }
.asm-card { background:var(--comfy-input-bg,#2a2a2a); border:1px solid var(--border-color,#444); border-radius:8px; overflow:hidden; cursor:pointer; }
.asm-card:hover { border-color:#5b8cff; }
.asm-card.selected { border-color:#5b8cff; box-shadow:0 0 0 2px rgba(91,140,255,.45); }
.asm-card .m { position:relative; aspect-ratio:1/1; background:#000; }
.asm-card .selmark { position:absolute; top:6px; right:6px; width:22px; height:22px; border-radius:50%; background:#5b8cff; color:#fff; font-size:13px; display:flex; align-items:center; justify-content:center; z-index:2; }
.asm-card img { width:100%; height:100%; object-fit:cover; display:block; }
.asm-card .play { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:42px; height:42px; border-radius:50%; background:rgba(0,0,0,.6); border:2px solid rgba(255,255,255,.7); color:#fff; display:flex; align-items:center; justify-content:center; font-size:16px; pointer-events:none; }
.asm-card .badge { position:absolute; top:6px; left:6px; background:rgba(0,0,0,.65); color:#fff; font-size:10px; padding:1px 7px; border-radius:10px; }
.asm-card .meta { padding:7px 9px; }
.asm-card .nm { font-size:11px; color:var(--descrip-text,#aaa); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.asm-card .pr { font-size:11px; color:var(--fg-color,#eee); height:2.2em; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.asm-card .mo { font-size:10px; color:#5b8cff; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.asm-empty { color:var(--descrip-text,#aaa); text-align:center; padding:50px 0; }
/* 日历 */
.asm-cal { display:grid; grid-template-columns:minmax(400px,540px) 1fr; gap:28px; align-items:start; }
.asm-calbar { display:flex; gap:8px; align-items:center; margin-bottom:16px; }
.asm-caltitle { font-size:17px; font-weight:700; min-width:130px; text-align:center; letter-spacing:.5px; }
.asm-calnav { background:var(--comfy-input-bg,#2a2a2a); border:1px solid var(--border-color,#3a3a3a); color:var(--fg-color,#eee); border-radius:8px; padding:6px 13px; cursor:pointer; font-size:13px; transition:border-color .15s, background .15s; }
.asm-calnav:hover { border-color:#5b8cff; background:rgba(91,140,255,.1); }
.asm-calnav.latest { color:#5b8cff; border-color:rgba(91,140,255,.45); }
.asm-week, .asm-calgrid { display:grid; grid-template-columns:repeat(7,1fr); gap:6px; }
.asm-week span { text-align:center; color:var(--descrip-text,#8a8a8a); font-size:11px; padding:5px 0 7px; font-weight:600; letter-spacing:1px; }
.asm-week span.we { color:#e88; }
.asm-day { position:relative; min-height:66px; background:var(--comfy-input-bg,#242424); border:1px solid var(--border-color,#3a3a3a); border-radius:10px; padding:7px 8px; font-size:11px; color:var(--descrip-text,#aaa); cursor:pointer; transition:border-color .15s, transform .12s, box-shadow .15s, background .15s; }
.asm-day.blank { background:transparent; border-color:transparent; box-shadow:none; cursor:default; }
.asm-day.has { color:var(--fg-color,#eee); }
.asm-day:hover { border-color:#5b8cff; transform:translateY(-1px); box-shadow:0 3px 10px rgba(0,0,0,.35); }
.asm-day.blank:hover { transform:none; box-shadow:none; border-color:transparent; }
.asm-day.today { background:rgba(91,140,255,.10); }
.asm-day.today .num { color:#5b8cff; }
.asm-day.sel { border-color:#5b8cff; background:linear-gradient(160deg, rgba(91,140,255,.20), rgba(91,140,255,.05)); box-shadow:0 0 0 1px rgba(91,140,255,.5); }
.asm-day .num { font-size:13px; font-weight:700; line-height:1.1; }
.asm-day .cnt { display:flex; flex-wrap:wrap; gap:4px; margin-top:7px; }
.asm-day .tag { font-size:9px; padding:1px 6px; border-radius:10px; line-height:1.5; font-weight:600; }
.asm-day .tag-img { background:rgba(91,140,255,.20); color:#8fb0ff; }
.asm-day .tag-vid { background:rgba(255,150,60,.18); color:#ffa05e; }
.asm-callist h3 { font-size:15px; font-weight:600; margin:0 0 14px; padding-bottom:10px; border-bottom:1px solid var(--border-color,#3a3a3a); }
.asm-callist h3 .sub { font-size:12px; color:var(--descrip-text,#aaa); font-weight:400; margin-left:4px; }
.asm-callist .cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:12px; }
@media (max-width: 1000px){ .asm-cal { grid-template-columns:1fr; gap:20px; } }
/* 弹窗预览 */
.asm-modal { position:fixed; inset:0; z-index:10001; display:none; align-items:center; justify-content:center; }
.asm-modal .bk { position:absolute; inset:0; background:rgba(0,0,0,.72); }
.asm-modal .pn { position:relative; background:var(--comfy-menu-bg,#202020); border:1px solid var(--border-color,#444); border-radius:12px; width:min(1208px,94vw); height:92vh; max-height:92vh; box-sizing:border-box; display:flex; flex-direction:column; overflow:hidden; padding:18px; }
.asm-modal video, .asm-modal img { max-width:100%; border-radius:8px; display:block; margin:0 auto; }
.asm-modal video { max-height:55vh; }
.asm-modal .rows { margin-top:12px; font-size:12px; color:var(--descrip-text,#aaa); }
.asm-modal textarea { width:100%; height:72px; background:var(--comfy-input-bg,#333); border:1px solid var(--border-color,#444); color:var(--input-text,#eee); border-radius:6px; padding:8px; font-size:12px; margin-top:6px; }
.asm-modal .btns { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
.asm-modal .x { position:absolute; top:8px; right:12px; background:none; border:none; color:var(--fg-color,#eee); font-size:20px; cursor:pointer; z-index:2; }
/* 预览翻页(箭头/计数贴图片与面板内缘, 不贴屏幕边) */
.asm-modal .mediaWrap { position:relative; flex:1; min-height:0; margin-top:14px; padding:0 56px; }
.asm-modal .media { display:flex; align-items:center; justify-content:center; width:100%; height:100%; min-height:100px; background:#000; border-radius:8px; overflow:hidden; }
.asm-modal .media img, .asm-modal .media video { max-width:100%; max-height:100%; width:auto; height:auto; object-fit:contain; }
.asm-modal .pvbar { position:absolute; top:2px; left:50%; transform:translateX(-50%); z-index:3; background:rgba(0,0,0,.66); border:1px solid rgba(255,255,255,.16); border-radius:12px; padding:3px 12px; font-size:11px; color:#eee; letter-spacing:.5px; white-space:nowrap; pointer-events:none; }
.asm-modal .nav { position:absolute; top:50%; transform:translateY(-50%); width:48px; height:48px; padding:0; border-radius:50%; border:1px solid rgba(255,255,255,.22); background:rgba(0,0,0,.55); color:#fff; font-size:22px; line-height:1; display:flex; align-items:center; justify-content:center; cursor:pointer; z-index:3; }
.asm-modal .nav:hover { background:rgba(91,140,255,.85); border-color:#5b8cff; }
.asm-modal .nav.prev { left:4px; }
.asm-modal .nav.next { right:4px; }
@media (max-width: 720px){ .asm-modal .nav { width:38px; height:38px; font-size:18px; } .asm-modal .nav.prev { left:2px; } .asm-modal .nav.next { right:2px; } }
/* 设置 */
.asm-set { margin:4px 0; }
.asm-set .row { display:flex; gap:8px; align-items:center; margin:8px 0; font-size:13px; }
.asm-set .row label { min-width:110px; color:var(--descrip-text,#bbb); }
.asm-set input { flex:1; background:var(--comfy-input-bg,#333); border:1px solid var(--border-color,#444); color:var(--input-text,#eee); border-radius:6px; padding:6px 10px; font-size:13px; }
.asm-set input[type="checkbox"] { flex:0 0 auto; width:auto; cursor:pointer; }
.asm-set input[type="number"] { flex:0 0 auto; width:110px; }
.asm-set .chk { display:flex; gap:8px; align-items:center; margin:8px 0; font-size:13px; }
.asm-status { padding:8px 14px; border-top:1px solid var(--border-color,#444); font-size:12px; color:var(--descrip-text,#aaa); min-height:18px; }
/* 排序下拉 / 文件夹视图 */
.asm-sort { background:var(--comfy-input-bg,#333); border:1px solid var(--border-color,#444); color:var(--input-text,#eee); border-radius:6px; padding:6px 8px; font-size:13px; }
.asm-lbl { font-size:12px; color:var(--descrip-text,#aaa); }
/* v1.2.2: 文件夹视图/日历视图下 body 不滚, 左右两栏各自独立滚动 */
.asm-body.asm-noscroll { overflow:hidden; display:flex; flex-direction:column; }
.asm-body.asm-noscroll > .asm-folder, .asm-body.asm-noscroll > .asm-cal { flex:1; min-height:0; }
.asm-folder { display:flex; align-items:stretch; gap:14px; height:100%; min-height:0; }
.asm-fside { flex:0 0 252px; width:252px; min-height:0; overflow:auto; box-sizing:border-box; padding-right:10px; border-right:1px solid var(--border-color,#3a3a3a); }
.asm-fbtns { display:flex; flex-wrap:wrap; gap:6px; }
.asm-fbtns .asm-btn { padding:4px 8px; font-size:12px; }
/* v1.2.3: 导航行常驻并预留固定高度 —— 否则在根目录隐藏它会让整棵树上下跳 */
.asm-crumbs { display:flex; flex-wrap:wrap; align-items:center; font-size:12px; color:var(--descrip-text,#aaa); margin:8px 0 6px; word-break:break-all; line-height:1.7; min-height:22px; }
.asm-crumb { cursor:pointer; color:#5b8cff; }
.asm-crumb:hover { text-decoration:underline; }
.asm-crumbsep { color:var(--descrip-text,#888); }
.asm-tree { border-top:1px solid var(--border-color,#3a3a3a); padding-top:4px; }
/* v1.2.2: 文件夹名自动换行(不再省略号截断) */
.asm-trow { padding:5px 8px; font-size:12px; cursor:pointer; border-radius:6px; white-space:normal; word-break:break-all; line-height:1.35; color:var(--descrip-text,#bbb); }
.asm-trow:hover { background:rgba(91,140,255,.15); color:var(--fg-color,#eee); }
.asm-trow.cur { background:rgba(91,140,255,.22); color:#5b8cff; font-weight:600; }
.asm-trow.sel { background:rgba(91,140,255,.16); }
.asm-trow.sel .asm-ttick { color:#5b8cff; font-weight:700; }
.asm-ttick { display:inline-block; width:14px; color:transparent; }
.asm-fempty { color:var(--descrip-text,#888); font-size:12px; padding:10px 8px; white-space:normal; }
.asm-fmain { flex:1; min-width:0; min-height:0; overflow:auto; }
.asm-cal { display:grid; grid-template-columns:minmax(400px,540px) 1fr; gap:28px; align-items:stretch; height:100%; min-height:0; }
.asm-cal > * { min-height:0; overflow:auto; }
.asm-fgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:12px; }
.asm-fcard .pico { display:flex; align-items:center; justify-content:center; height:100%; font-size:34px; color:var(--descrip-text,#999); }
.asm-fcard .m video { width:100%; height:100%; object-fit:cover; display:block; }
.asm-fgrid .asm-empty { grid-column:1 / -1; }
.asm-btn[disabled] { opacity:.45; cursor:not-allowed; }
`;

app.registerExtension({
  name: "ComfyUI.AssetManager",
  async setup() {
    // ---------- 国际化: 跟随 ComfyUI 语言 ----------
    let LANG = "zh";
    function detectLang() {
      try {
        const loc = window.comfyAPI.app.app.ui.settings.getSettingValue("Comfy.Locale");
        LANG = (loc && String(loc).toLowerCase().startsWith("zh")) ? "zh" : "en";
      } catch (e) { LANG = "zh"; }
    }
    const L10N = {
      "资产管理": "Asset Manager",
      "浏览/搜索/删除产物, 切换输出目录, 下载": "Browse / search / delete assets, switch output directory, download",
      "搜索提示词 / 模型 / 文件名 / 日期…": "Search prompts / models / filename / date…",
      "🗂 资产管理": "🗂 Asset Manager",
      "‹ 上月": "‹ Prev",
      "下月 ›": "Next ›",
      "回到最新": "Latest",
      "网格": "Grid",
      "日历": "Calendar",
      "全部": "All types",
      "图片": "Images",
      "视频": "Videos",
      "☑ 多选": "☑ Multi-select",
      "🗑 删除选中": "🗑 Delete selected",
      "⬇ 下载选中": "⬇ Download selected",
      "⚙ 资产设置": "⚙ Settings",
      "⬇ 下载": "⬇ Download",
      "⟳ 扫描": "⟳ Scan",
      "图": "Img",
      "(未检测到提示词)": "(no prompt detected)",
      "没有匹配的产物": "No matching assets",
      "当天没有归档产物": "No assets on this day",
      "当天没有匹配当前筛选的产物": "No matching assets on this day",
      "点选日期查看当天产物": "Click a date to view its assets",
      "来源: ": "Source: ",
      "时间: ": "Time: ",
      "模型/LoRA: ": "Models/LoRA: ",
      "参数: ": "Params: ",
      "提示词": "Prompt text",
      "复制提示词": "Copy prompt",
      "下载 workflow.json": "Download workflow.json",
      "🗑 从硬盘删除": "🗑 Delete from disk",
      "💡 下载 workflow.json 后拖进 ComfyUI 画布, 即可完整还原整套工作流(节点+连线)。": "💡 Drag the downloaded workflow.json onto the ComfyUI canvas to fully restore the workflow (nodes + links).",
      "上一张 (←)": "Previous (←)",
      "下一张 (→)": "Next (→)",
      "多选模式: 点击切换选中, Shift+点击连选一段": "Multi-select: click to toggle, Shift+click to select a range",
      "已退出多选": "Exited multi-select",
      "下载包含 json/txt 元数据": "Include json/txt metadata in downloads",
      "下载保留每张图的文件夹": "Keep one folder per asset in downloads",
      "• 当前列表中的图片/视频 + json/txt 元数据": "• images/videos in the current list + json/txt metadata",
      "• 当前列表中的图片/视频（不含 json/txt/缩略图）": "• images/videos in the current list (no json/txt/thumbnails)",
      "，每张图一个文件夹": ", one folder per asset",
      "，全部平铺在同一目录": ", everything flattened into one folder",
      "，打包为单个 ZIP": ", packed into a single ZIP",
      "，逐个原样保存": ", saved one by one",
      "💡 ← / → 切换上/下一张图片, Esc 关闭; 下载 workflow.json 后拖进 ComfyUI 画布, 即可完整还原整套工作流(节点+连线)。": "💡 ← / → to switch images, Esc to close; drag the downloaded workflow.json onto the ComfyUI canvas to fully restore the workflow.",
      "已复制": "Copied",
      "该产物未携带 workflow 元数据": "This asset has no workflow metadata",
      "下载失败": "Download failed",
      "已从硬盘删除": "Deleted from disk",
      "未知错误": "unknown error",
      "留空=使用 ComfyUI 默认 output": "Leave empty = ComfyUI default output",
      "输出目录": "Output directory",
      "归档库目录": "Archive directory",
      "下载目录": "Download directory",
      "自动归档新产物": "Auto-archive new assets",
      "自动下载新产物": "Auto-download new assets",
      "归档安装前已有的产物": "Archive assets already present on install",
      "缩略图宽度(px)": "Thumbnail width (px)",
      "扫描间隔(秒)": "Scan interval (sec)",
      "浏览…": "Browse…",
      "保存设置": "Save settings",
      "改归档/下载目录后新产物进入新目录, 旧数据保留; 输出目录切换重启 ComfyUI 后仍生效; 自动归档/自动下载开关和扫描间隔即时生效。下载目录: 点「浏览…」可在系统对话框选择本地目录（授权后下载/自动下载直接写入该目录, 无需经过浏览器下载; 未授权时使用浏览器默认下载目录）。": "After changing the archive/download directory, new assets go to the new directory (old data stays). Output directory changes persist across ComfyUI restarts. Auto-archive/auto-download and scan interval take effect immediately. Download folder: click Browse to pick a local folder in the system dialog (after grant, downloads/auto-downloads are written directly into it, bypassing the browser download flow; otherwise the browser default folder is used).",
      "✅ 设置已保存": "✅ Settings saved",
      "📁 选择目录": "📁 Select directory",
      "（请选择磁盘）": "(select a drive)",
      "（无子目录）": "(no subdirectories)",
      "⬆ 上一级": "⬆ Up",
      "✅ 选择此目录": "✅ Select this folder",
      "取消": "Dismiss",
      "⬇ 下载确认": "⬇ Download confirmation",
      "将打包下载以下内容:": "Will package and download:",
      "• 当前列表中的全部资产（图片/视频/元数据/工作流）": "• All assets in the current list (images / videos / metadata / workflows)",
      "下载数量: ": "Items to download: ",
      "确定下载": "Download",
      "正在打包下载…": "Preparing download…",
      "✅ 已开始下载: ": "✅ Download started: ",
      " 个文件, 保存到本地浏览器下载目录": " files, saved to the browser download folder",
      "扫描中…": "Scanning…",
      "扫描失败": "Scan failed",
      "下载方式": "Download mode",
      "原样保存(不打包)": "Save as-is (no ZIP)",
      "打包为 ZIP": "Package as ZIP",
      "将逐个保存以下文件:": "Will save the following files individually:",
      "正在保存…": "Saving…",
      "✅ 已保存 ": "✅ Saved ",
      "（浏览器下载目录）": "(browser download folder)",
      "• 当前列表中的全部资产（图片/视频/元数据/工作流）, 打包为单个 ZIP": "• All assets in the current list (images / videos / metadata / workflows), packaged as a single ZIP",
      "• 当前列表中的全部资产（图片/视频/元数据/工作流）, 逐个原样保存": "• All assets in the current list (images / videos / metadata / workflows), saved individually as-is",
      "该资产下载失败": "Failed to download this asset",
      "（为空时使用浏览器默认下载目录, 如 C:\\Users\\Administrator\\Downloads\\）": "(leave empty to use the browser default download folder, e.g. C:\\Users\\Administrator\\Downloads\\)",
      "自动下载已启用: 新产物将自动保存到浏览器下载目录": "Auto-download enabled: new assets will be saved to the browser download folder",
      "已连接本地目录: ": "Linked local folder: ",
      "选择目录失败: ": "Pick folder failed: ",
      "当前浏览器不支持直接选择本地目录, 将使用浏览器默认下载目录": "The browser does not support picking a local folder; will use the browser default download folder",
      "加载中…": "Loading…",
      "共 ": "Total: ",
      " 条资产": " assets",
      "已自动更新: 共 ": "Auto-updated: ",
      "文件夹": "Folders",
      "排序": "Sort",
      "新建时间↓": "Created ↓",
      "新建时间↑": "Created ↑",
      "打开时间↓": "Opened ↓",
      "打开时间↑": "Opened ↑",
      "名称 A→Z": "Name A→Z",
      "名称 Z→A": "Name Z→A",
      "新建": "New",
      "改名": "Rename",
      "删除": "Delete",
      "多选": "Multi-select",
      "剪切": "Cut",
      "粘贴": "Paste",
      "刷新": "Refresh",
      "此文件夹没有图片": "No images in this folder",
      "没有匹配当前筛选的图片": "No images match the current filter",
      "（请先选中要移动的项）": "(select the items to move first)",
      "剪贴板为空": "Clipboard is empty",
      "新建文件夹": "New folder",
      "新名称:": "New name:",
      "文件夹加载失败: ": "Failed to load folder: ",
      "文件夹树加载失败: ": "Failed to load folder tree: ",
      "（文件夹过多，仅显示部分）": "(too many folders — list truncated)",
      "新建失败: ": "Create failed: ",
      "改名失败: ": "Rename failed: ",
      "移动失败: ": "Move failed: ",
      "其他": "Other",
      "文件名: ": "File: ",
      "大小: ": "Size: ",
      "路径: ": "Path: ",
      "打开: ": "Opened: ",
      "关闭": "Close",
      "该文件无法预览": "This file cannot be previewed",
      "该文件未归档，没有提示词元数据": "Not archived — no prompt metadata",
      "下载文件": "Download file",
      "浏览器无法播放该视频": "The browser cannot play this video",
      "可用「下载文件」保存后用本地播放器打开": "Use Download file to save it, then open it with a local player",
      "该产物未携带媒体文件": "This asset has no media file",
      "该文件不支持预览，可用「下载文件」保存": "Preview is not supported for this file — use Download file to save it",
      "保存 workflow.json": "Save workflow.json",
      "该产物未携带工作流元数据": "This asset has no workflow metadata",
      "✅ 已保存 workflow.json": "✅ workflow.json saved",
      "体检": "Audit",
      "归档库体检": "Archive audit",
      "体检中…": "Auditing…",
      "体检失败": "Audit failed",
      "重复来源": "Duplicate sources",
      "不可预览条目": "Non-previewable entries",
      "孤儿条目": "Orphaned entries",
      "同内容疑似重复": "Same-content suspects",
      "条目": "entries",
      "占用": "disk usage",
      "最早": "oldest",
      "最新": "newest",
      "媒体缺失": "media missing",
      "媒体 0 字节": "media is 0 bytes",
      "容器不可播放": "unplayable container",
      "output 文件已不存在": "output file no longer exists",
      "（无）": "(none)",
      "体检只读不改任何文件; 删除属后续版本。": "The audit is read-only and changes nothing; deletion comes in a later release.",
      "根": "Root",
      "下载": "Download",
      "（根目录不能改名）": "(the root folder cannot be renamed)",
      "（根目录不能删除）": "(the root folder cannot be deleted)",
      "已选 ": "Selected ",
      " 个文件夹": " folder(s)",
      " 个文件": " file(s)",
      "正在读取文件夹清单…": "Reading folder contents…",
      "正在下载 N 个文件": "Downloading N file(s)",
      "没有选中要下载的内容": "Nothing selected to download",
      "文件夹文件过多，已中止下载": "Folder has too many files; download aborted",
      "该文件下载失败": "This file could not be downloaded",
      "删除失败: ": "Delete failed: ",
      "已删除 ": "Deleted ",
    };
    function t(zh) { return LANG === "zh" ? zh : (L10N[zh] !== undefined ? L10N[zh] : zh); }
    const ERR_L10N = {
      "Missing output directory path": "缺少输出目录路径",
      "run_ids must be an array": "run_ids 必须是数组",
      "Directory not found": "目录不存在",
      "Directory is outside the allowed browse scope": "该目录不在允许浏览范围内",
      "Missing run_id": "缺少 run_id",
      "Invalid archive path": "非法的归档路径",
      "Archive entry not found": "未找到该归档条目",
      "Invalid folder name": "文件夹名非法",
      "Already exists": "已存在同名的文件夹或文件",
      "Cannot rename the output root": "不能改名 output 根目录",
      "Cannot delete the output root": "不能删除 output 根目录",
      "Folder is not empty": "文件夹不为空",
      "Folders cannot be moved": "文件夹不能移动",
      "Missing key": "缺少 key",
    };
    function terr(en) { return LANG === "zh" ? (ERR_L10N[en] || en) : en; }
    detectLang();
    // 语言变化时动态更新所有静态文本
    const relabelers = [];
    function bindText(el, zh, prop) {
      prop = prop || "textContent";
      el.dataset.i18n = zh;
      el.dataset.i18nProp = prop;
      el[prop] = t(zh);
      return el;
    }
    function relabel() {
      document.querySelectorAll("[data-i18n]").forEach((el) => {
        el[el.dataset.i18nProp || "textContent"] = t(el.dataset.i18n);
      });
      for (const f of relabelers) f();
    }
    function labeledRow(parts) {
      const d = $el("div");
      for (const p of parts) {
        if (p.zh) { const s = $el("span"); bindText(s, p.zh); d.appendChild(s); }
        if (p.text) d.appendChild(document.createTextNode(p.text));
      }
      return d;
    }

    const styleEl = $el("style", { textContent: STYLE });
    (document.head || document.documentElement).appendChild(styleEl);

    // 自动修复: 连线渲染模式被设成 Hidden(-1) 时改回 Spline(2)
    function fixLinkRenderMode() {
      try {
        const g = window.comfyAPI.app.app.rootGraphInternal;
        if (!g) return;
        const arr = Array.isArray(g.list_of_graphcanvas) ? g.list_of_graphcanvas : Object.values(g.list_of_graphcanvas || {});
        for (const gc of arr) {
          if (gc && gc.links_render_mode === -1) {
            gc.links_render_mode = 2;  // SPLINE_LINK
            if (gc.setDirty) gc.setDirty(false, true);
          }
        }
      } catch (e) {}
    }
    setTimeout(fixLinkRenderMode, 1500);
    setTimeout(fixLinkRenderMode, 6000);

    let runs = [];
    let view = "grid", kind = "all", selDate = null, calYear = 0, calMonth = 0;
    let multi = false;
    const selected = new Set();
    let selAnchor = null; // 多选连选锚点(上次点中的 dir)
    // v1.2.2: 文件夹选中集合(与文件 selected 互斥; 同一时刻只有一种选中类型)
    const selFolders = new Set();
    let folAnchor = null;  // 文件夹连选锚点
    let pollTimer = null;
    let curConfig = {};

    // ---------- 排序(工具栏共用下拉, 4 处共用同一 sortMode) ----------
    const SORT_MODES = ["created_desc", "created_asc", "opened_desc", "opened_asc", "name_asc", "name_desc"];
    const SORT_LABELS = {
      created_desc: "新建时间↓",
      created_asc: "新建时间↑",
      opened_desc: "打开时间↓",
      opened_asc: "打开时间↑",
      name_asc: "名称 A→Z",
      name_desc: "名称 Z→A",
    };
    let sortMode = "created_desc";
    try {
      const sm = localStorage.getItem("am_sort_mode") || "created_desc";
      if (SORT_MODES.indexOf(sm) >= 0) sortMode = sm;
    } catch (e) {}

    // ---------- 文件夹视图状态 ----------
    let folderPath = "";                                        // 当前文件夹 rel
    let folderData = { path: "", parent: null, dirs: [], files: [] };
    let clipboard = null;                                       // { items: [rel, ...] } 剪切语义
    let folderTree = { nodes: [], truncated: false };            // GET /asset/folder_tree 的全量树
    let flatTree = [];                                          // 已排序 + 已扁平化的树列表(↑/↓ 用)
    let treeRowEls = {};                                        // rel -> 树行元素
    let treeCurEl = null;                                       // 当前高亮的树行

    const byDate = {};
    function rebuildByDate() {
      for (const k in byDate) delete byDate[k];
      for (const r of runs) (byDate[r.date] || (byDate[r.date] = [])).push(r);
    }

    function pad(n) { return String(n).padStart(2, "0"); }
    function mediaUrl(dir, f) { return "./asset/file?p=" + encodeURIComponent(dir + "/" + f); }
    // v1.2.6: .gif 是动图, 必须按 <img> 渲染 —— 塞进 <video> 浏览器直接放不出来(黑屏), 即"无法预览的视频"
    function isGifName(n) { return /\.gif$/i.test(String(n || "")); }
    function isVideoRender(r) { return r.kind === "video" && !isGifName(r.media); }

    function matches(r, kw) {
      kw = kw.toLowerCase();
      return ((r.positive + " " + (r.negative || "") + " " + (r.models || []).join(" ") + " " + r.name + " " + (r.date || "")).toLowerCase()).includes(kw);
    }
    function filtered(list) {
      const kw = q.value.trim();
      return list.filter(r => (kind === "all" || r.kind === kind) && (!kw || matches(r, kw)));
    }

    async function postJSON(url, payload) {
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      return await res.json();
    }
    function outUrl(rel) { return "./asset/output_file?p=" + encodeURIComponent(rel); }
    // v1.2.6: 文件夹视图里以文件名判定(卡片/预览用), gif 同样按图片渲染
    function isGifRel(n) { return isGifName(n); }
    function isVideoRenderF(f) { return f.kind === "video" && !isGifName(f.name); }
    function fmtSize(n) {
      n = Number(n) || 0;
      if (n < 1024) return n + " B";
      const units = ["KB", "MB", "GB", "TB"];
      let i = -1;
      do { n = n / 1024; i++; } while (n >= 1024 && i < units.length - 1);
      return (Math.round(n * 10) / 10) + " " + units[i];
    }
    // 时间缺失("")一律排最后(与升降序无关); ISO 字符串直接比较, 不解析 Date
    function timeCmp(x, y, desc) {
      const a = x || "", b = y || "";
      if (!a && !b) return 0;
      if (!a) return 1;
      if (!b) return -1;
      if (a === b) return 0;
      const r = a < b ? -1 : 1;
      return desc ? -r : r;
    }
    function sortItems(list, mode, nameOf, createdOf, openedOf) {
      const m = SORT_MODES.indexOf(mode) >= 0 ? mode : "created_desc";
      const arr = (list || []).slice();
      arr.sort((a, b) => {
        let r = 0;
        if (m === "created_desc") r = timeCmp(createdOf(a), createdOf(b), true);
        else if (m === "created_asc") r = timeCmp(createdOf(a), createdOf(b), false);
        else if (m === "opened_desc") r = timeCmp(openedOf(a), openedOf(b), true);
        else if (m === "opened_asc") r = timeCmp(openedOf(a), openedOf(b), false);
        else if (m === "name_asc") r = String(nameOf(a) || "").localeCompare(String(nameOf(b) || ""));
        else r = String(nameOf(b) || "").localeCompare(String(nameOf(a) || ""));
        if (r === 0) r = String(nameOf(a) || "").localeCompare(String(nameOf(b) || ""));
        return r;
      });
      return arr;
    }
    function sortRuns(list) {
      return sortItems(list, sortMode, (r) => r.name, (r) => r.created, (r) => r.opened);
    }
    // 打开时间上报: 失败静默, 绝不弹错
    function reportOpen(key) {
      try {
        fetch("./asset/touch_open", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key: key }),
        }).catch(function () {});
      } catch (e) {}
    }

    // ---------- 面板骨架 ----------
    const overlay = $el("div.asm-overlay");
    const body = $el("div.asm-body");
    const status = $el("div.asm-status", { textContent: "" });
    const q = $el("input.asm-search", { type: "text" });
    bindText(q, "搜索提示词 / 模型 / 文件名 / 日期…", "placeholder");
    const countEl = $el("span", { textContent: "", style: { fontSize: "12px", color: "var(--descrip-text,#aaa)" } });
    const calGrid = $el("div.asm-calgrid");
    const calListTitle = $el("h3");
    const calListCards = $el("div.cards");
    const calTitle = $el("span.asm-caltitle");

    const gridEl = $el("div.asm-grid");
    const calWrap = $el("div.asm-cal", { style: { display: "none" } });
    const weekdayEls = [];
    function renderWeekdays() {
      const wd = LANG === "zh" ? ["一", "二", "三", "四", "五", "六", "日"] : ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
      weekdayEls.forEach((el, i) => { el.textContent = wd[i]; });
    }
    relabelers.push(renderWeekdays);
    const prevMonthBtn = $el("button.asm-calnav", { onclick: () => { calMonth--; if (calMonth < 0) { calMonth = 11; calYear--; } selDate = null; renderCal(); } });
    bindText(prevMonthBtn, "‹ 上月");
    const nextMonthBtn = $el("button.asm-calnav", { onclick: () => { calMonth++; if (calMonth > 11) { calMonth = 0; calYear++; } selDate = null; renderCal(); } });
    bindText(nextMonthBtn, "下月 ›");
    const latestBtn = $el("button.asm-calnav.latest", { onclick: () => { goLatest(); } });
    bindText(latestBtn, "回到最新");
    calWrap.appendChild($el("div", {}, [
      $el("div.asm-calbar", {}, [prevMonthBtn, calTitle, nextMonthBtn, latestBtn]),
      $el("div.asm-week", {}, Array.from({ length: 7 }, (_, idx) => {
        const s = $el("span" + (idx >= 5 ? ".we" : ""));
        weekdayEls.push(s);
        return s;
      })),
      calGrid,
    ]));
    renderWeekdays();
    calWrap.appendChild($el("div.asm-callist", {}, [calListTitle, calListCards]));

    function goLatest() {
      if (runs.length) {
        const d = runs[0].date;
        calYear = Number(d.slice(0, 4)); calMonth = Number(d.slice(5, 7)) - 1; selDate = d;
      }
      renderCal();
    }

    // ---------- 文件夹视图骨架(左栏: 按钮区 → 面包屑 → 文件夹树; 右栏: 纯图片网格) ----------
    const fCrumbs = $el("div.asm-crumbs");
    const fTreeEl = $el("div.asm-tree");
    // 新增按钮一律无图标(契约 §6.3); 顺序: 新建 改名 删除 多选 剪切 粘贴 下载 刷新
    const fNewBtn = bindText($el("button.asm-btn", { onclick: () => newFolder() }), "新建");
    const fRenBtn = bindText($el("button.asm-btn", { onclick: () => renameFolder() }), "改名");
    const fDelBtn = bindText($el("button.asm-btn.danger", { onclick: () => deleteFolder() }), "删除");
    // 「多选」复用现有 multi/selected 状态, 与工具栏的「☑ 多选」同步高亮
    const fMultiBtn = bindText($el("button.asm-btn", { onclick: () => toggleMulti() }), "多选");
    const fCutBtn = bindText($el("button.asm-btn", { onclick: () => cutSelected() }), "剪切");
    const fPasteBtn = bindText($el("button.asm-btn", { onclick: () => pasteClipboard() }), "粘贴");
    // v1.2.2: 下载选中(文件或文件夹, 文件夹递归含子目录)
    const fDlBtn = bindText($el("button.asm-btn", { onclick: () => downloadOutputSelection() }), "下载");
    const fRefreshBtn = bindText($el("button.asm-btn", { onclick: () => reloadFolderView() }), "刷新");
    // v1.2.3: 分两行 —— 行1「文件夹」(新建/改名/删除/刷新), 行2「选中项」(多选/剪切/粘贴/下载)
    const fRowFolder = $el("div.asm-fbtns", {}, [fNewBtn, fRenBtn, fDelBtn, fRefreshBtn]);
    const fRowPick = $el("div.asm-fbtns", {}, [fMultiBtn, fCutBtn, fPasteBtn, fDlBtn]);
    const fSide = $el("div.asm-fside", {}, [
      fRowFolder,
      fRowPick,
      fCrumbs,
      fTreeEl,
    ]);
    const fGrid = $el("div.asm-fgrid");
    const folderWrap = $el("div.asm-folder", { style: { display: "none" } }, [
      fSide,
      $el("div.asm-fmain", {}, [fGrid]),
    ]);
    function setMultiBtns() {
      [multiBtn, fMultiBtn].forEach((b) => { if (b) b.classList.toggle("on", multi); });
    }

    // ---------- 视图切换 ----------
    const viewBtns = {};
    function mkViewBtn(zh, v) {
      const b = $el("button.asm-btn" + (view === v ? ".on" : ""));
      bindText(b, zh);
      b.onclick = () => {
        const prev = view;
        view = v;
        Object.values(viewBtns).forEach(x => x.classList.remove("on"));
        b.classList.add("on");
        // 文件夹视图的选中集合存 rel, 网格/日历存 dir, 二者不通用 → 进出文件夹视图时清空选中
        // 文件夹视图的选中集合存 rel(与网格/日历的 run dir 不同键空间) → 进出文件夹视图时清空两类选中
        if (prev === "folder" || v === "folder") { selected.clear(); selAnchor = null; selFolders.clear(); folAnchor = null; }
        refresh();
        if (v === "folder") { loadFolderTree(); loadFolder(folderPath); }
      };
      viewBtns[v] = b;
      return b;
    }
    const kindBtns = {};
    function mkKindBtn(zh, k) {
      const b = $el("button.asm-btn" + (kind === k ? ".on" : ""));
      bindText(b, zh);
      b.onclick = () => { kind = k; Object.values(kindBtns).forEach(x => x.classList.remove("on")); b.classList.add("on"); refresh(); };
      kindBtns[k] = b;
      return b;
    }

    const multiBtn = $el("button.asm-btn", { onclick: toggleMulti });
    bindText(multiBtn, "☑ 多选");
    const batchBtn = $el("button.asm-btn.danger", { onclick: batchDelete, style: { display: "none" } });
    bindText(batchBtn, "🗑 删除选中");

    const settingsBtn = $el("button.asm-btn", { onclick: openSettings });
    bindText(settingsBtn, "⚙ 资产设置");
    const batchDownloadBtn = $el("button.asm-btn", { onclick: downloadSelected, style: { display: "none" } });
    bindText(batchDownloadBtn, "⬇ 下载选中");
    const downloadBtn = $el("button.asm-btn", { onclick: confirmDownload });
    bindText(downloadBtn, "⬇ 下载");
    const scanBtn = $el("button.asm-btn", { onclick: doScan });
    bindText(scanBtn, "⟳ 扫描");
    // v1.2.9: 归档库体检(只读清单, 零删除) —— §6(C)-①
    const auditBtn = $el("button.asm-btn", { onclick: openAudit });
    bindText(auditBtn, "体检");
    // 工具栏共用排序下拉: 文件夹列表 / 文件夹网格 / 网格 runs / 日历当天列表 共用同一 sortMode
    const sortSel = $el("select.asm-sort");
    function fillSortSel() {
      sortSel.innerHTML = "";
      for (const m of SORT_MODES) {
        sortSel.appendChild($el("option", { value: m, textContent: t(SORT_LABELS[m]) }));
      }
      sortSel.value = sortMode;
    }
    fillSortSel();
    sortSel.onchange = () => {
      sortMode = sortSel.value;
      try { localStorage.setItem("am_sort_mode", sortMode); } catch (e) {}
      refresh();
      if (view === "folder") renderTree();   // 左栏树列表也按新 sortMode 重排
    };
    relabelers.push(fillSortSel);
    const toolbar = $el("div.asm-toolbar", {}, [
      q,
      mkViewBtn("网格", "grid"),
      mkViewBtn("日历", "cal"),
      mkViewBtn("文件夹", "folder"),
      mkKindBtn("全部", "all"),
      mkKindBtn("图片", "image"),
      mkKindBtn("视频", "video"),
      bindText($el("span.asm-lbl"), "排序"),
      sortSel,
      multiBtn,
      batchBtn,
      batchDownloadBtn,
      settingsBtn,
      downloadBtn,
      scanBtn,
      auditBtn,
      countEl,
    ]);

    const panelTitle = $el("h2");
    bindText(panelTitle, "🗂 资产管理");
    // v1.2.4: 标题旁常显运行版本 —— 部署靠 pull + Ctrl+F5, 一眼就能确认浏览器跑的是哪一版
    const verEl = $el("span", { textContent: "", style: { fontSize: "11px", color: "var(--descrip-text,#999)" } });
    const panel = $el("div.asm-panel", {}, [
      $el("div.asm-header", {}, [
        panelTitle,
        verEl,
        $el("span.sp"),
        $el("button.asm-x", { textContent: "✕", onclick: closePanel }),
      ]),
      toolbar,
      body,
      status,
    ]);
    body.appendChild(gridEl);
    body.appendChild(calWrap);
    body.appendChild(folderWrap);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    // ---------- 渲染 ----------
    function renderCard(r, container, list) {
      const card = $el("div.asm-card");
      if (selected.has(r.dir)) card.classList.add("selected");
      const thumb = r.thumb ? mediaUrl(r.dir, r.thumb) : mediaUrl(r.dir, r.media);
      const isVid = isVideoRender(r);
      card.appendChild($el("div.m", {}, [
        $el("img", { src: thumb, loading: "lazy" }),
        isVid ? $el("div.play", { textContent: "▶" }) : null,
        $el("span.badge", { textContent: isVid ? t("视频") : t("图") }),
        selected.has(r.dir) ? $el("div.selmark", { textContent: "✓" }) : null,
      ].filter(Boolean)));
      card.appendChild($el("div.meta", {}, [
        $el("div.nm", { textContent: r.name }),
        $el("div.pr", { textContent: (r.positive || "").slice(0, 160) || t("(未检测到提示词)") }),
        r.models && r.models.length ? $el("div.mo", { textContent: r.models.join(" · ") }) : null,
      ].filter(Boolean)));
      card.onclick = (e) => {
        const shift = !!(e && e.shiftKey);
        // Shift+点击: 没开多选就自动进多选; 已开则从锚点连选到这一张
        if (shift && !multi) { multi = true; setMultiBtns(); statusMsg(t("多选模式: 点击切换选中, Shift+点击连选一段")); }
        if (!multi) { openPreview(r, list); return; }
        if (shift && selAnchor) {
          const i0 = list.findIndex(x => x.dir === selAnchor);
          const i1 = list.findIndex(x => x.dir === r.dir);
          if (i0 >= 0 && i1 >= 0) {
            const a = Math.min(i0, i1), b = Math.max(i0, i1);
            for (let i = a; i <= b; i++) selected.add(list[i].dir);
            selAnchor = r.dir;
            updateBatchBtn();
            refresh();
            return;
          }
        }
        if (selected.has(r.dir)) selected.delete(r.dir); else selected.add(r.dir);
        selAnchor = r.dir;
        card.classList.toggle("selected", selected.has(r.dir));
        const m = card.querySelector(".m");
        const mark = card.querySelector(".selmark");
        if (selected.has(r.dir) && !mark) m.appendChild($el("div.selmark", { textContent: "✓" }));
        if (!selected.has(r.dir) && mark) mark.remove();
        updateBatchBtn();
      };
      container.appendChild(card);
    }

    function renderGrid() {
      const list = sortRuns(filtered(runs));
      gridEl.innerHTML = "";
      countEl.textContent = list.length + " / " + runs.length;
      if (!list.length) { gridEl.appendChild($el("div.asm-empty", { textContent: t("没有匹配的产物") })); return; }
      for (const r of list) renderCard(r, gridEl, list);
    }

    function countOf(d) {
      const l = byDate[d] || [];
      return { all: l.length, img: l.filter(r => r.kind === "image").length, vid: l.filter(r => r.kind === "video").length };
    }

    function renderCal() {
      calTitle.textContent = LANG === "zh" ? (calYear + "年" + (calMonth + 1) + "月") : (calYear + "-" + pad(calMonth + 1));
      const first = (new Date(calYear, calMonth, 1).getDay() + 6) % 7;
      const days = new Date(calYear, calMonth + 1, 0).getDate();
      const now = new Date();
      const tKey = now.getFullYear() + "-" + pad(now.getMonth() + 1) + "-" + pad(now.getDate());
      calGrid.innerHTML = "";
      for (let i = 0; i < 42; i++) {
        const d = i - first + 1;
        if (d < 1 || d > days) { calGrid.appendChild($el("div.asm-day.blank")); continue; }
        const dk = calYear + "-" + pad(calMonth + 1) + "-" + pad(d);
        const c = countOf(dk);
        const has = c.all > 0;
        const day = $el("div.asm-day" + (has ? ".has" : "") + (dk === tKey ? ".today" : "") + (dk === selDate ? ".sel" : ""), {}, [
          $el("div.num", { textContent: String(d) }),
        ]);
        if (has) {
          const cnt = $el("div.cnt");
          if (kind === "all") {
            if (c.img) cnt.appendChild($el("span.tag.tag-img", { textContent: c.img + (LANG === "zh" ? " 图" : " img") }));
            if (c.vid) cnt.appendChild($el("span.tag.tag-vid", { textContent: c.vid + (LANG === "zh" ? " 视" : " vid") }));
          } else {
            const n = kind === "image" ? c.img : c.vid;
            const cls = kind === "image" ? "tag-img" : "tag-vid";
            const label = LANG === "zh" ? (kind === "image" ? " 图" : " 视") : (kind === "image" ? " img" : " vid");
            cnt.appendChild($el("span.tag." + cls, { textContent: n + label }));
          }
          day.appendChild(cnt);
        }
        day.onclick = () => { selDate = dk; renderCal(); };
        calGrid.appendChild(day);
      }
      const base = (selDate && byDate[selDate]) ? byDate[selDate].length : 0;
      const list = selDate ? sortRuns(filtered(byDate[selDate] || [])) : [];
      let title;
      if (selDate) {
        title = LANG === "zh" ? (selDate + " · 当天归档 " + base + " 条") : (selDate + " · " + base + " assets");
      } else {
        title = t("点选日期查看当天产物");
      }
      if (selDate && (kind !== "all" || q.value.trim())) {
        title += LANG === "zh" ? " <span class='sub'>（当前筛选 " + list.length + " 条）</span>" : " <span class='sub'>(filtered: " + list.length + ")</span>";
      }
      calListTitle.innerHTML = title;
      calListCards.innerHTML = "";
      if (selDate && base === 0) calListCards.appendChild($el("div.asm-empty", { textContent: t("当天没有归档产物") }));
      else if (!list.length && selDate) calListCards.appendChild($el("div.asm-empty", { textContent: t("当天没有匹配当前筛选的产物") }));
      else for (const r of list) renderCard(r, calListCards, list);
    }

    // ---------- 文件夹视图: 树 / 渲染 / 交互 ----------
    function dirNameOf(rel) {
      const i = rel.lastIndexOf("/");
      return i >= 0 ? rel.slice(i + 1) : rel;
    }
    function parentOf(rel) {
      return rel.indexOf("/") >= 0 ? rel.slice(0, rel.lastIndexOf("/")) : "";
    }
    function buildFlatTree(nodes, out) {
      const sorted = sortItems(nodes || [], sortMode, (n) => n.name, (n) => n.created, (n) => n.opened);
      for (const n of sorted) {
        out.push(n);
        buildFlatTree(n.children || [], out);
      }
      return out;
    }
    function treeSig(flat) {
      return flat.map((n) => n.rel + ":" + (n.file_count || 0)).join("|");
    }
    // v1.2.2: 面包屑不再显示 "output 根" 说明文字; v1.2.3: 该行**常驻**(根目录时为空但占位),
    // 否则"点根→隐藏→整棵树上移 / 点文件夹→出现→整棵树下移"会上下跳动
    function renderCrumbs() {
      fCrumbs.innerHTML = "";
      const parts = folderPath ? folderPath.split("/") : [];
      let acc = "";
      for (let i = 0; i < parts.length; i++) {
        acc = acc ? acc + "/" + parts[i] : parts[i];
        const rel = acc;
        if (i > 0) fCrumbs.appendChild($el("span.asm-crumbsep", { textContent: " / " }));
        fCrumbs.appendChild($el("span.asm-crumb", { textContent: parts[i], onclick: () => goToFolder(rel) }));
      }
    }
    // 左栏文件夹树: v1.2.2 顶部固定一行「根」(取代已删除的面包屑根说明);
    // 每行 = 勾选位 + 名称(文件数); 缩进 12px/级; 当前项高亮
    function mkTreeRow(rel, name, depth, count) {
      const row = $el("div.asm-trow");
      row.style.paddingLeft = (4 + (depth || 0) * 12) + "px";
      row.title = rel || t("根");
      const sel = selFolders.has(rel);
      row.appendChild($el("span.asm-ttick", { textContent: sel ? "✓" : "" }));
      row.appendChild($el("span", { textContent: (count === null || count === undefined) ? name : (name + " (" + count + ")") }));
      if (sel) row.classList.add("sel");
      row.onclick = (ev) => pickFolder(rel, ev);
      treeRowEls[rel] = row;
      fTreeEl.appendChild(row);
      return row;
    }
    function renderTree() {
      flatTree = [{ rel: "", name: t("根"), depth: 0, file_count: null, children: [] }]
        .concat(buildFlatTree((folderTree && folderTree.nodes) || [], []));
      fTreeEl.innerHTML = "";
      treeRowEls = {};
      treeCurEl = null;
      for (const n of flatTree) mkTreeRow(n.rel, n.name, n.depth || 0, n.file_count);
      if (folderTree && folderTree.truncated) {
        fTreeEl.appendChild(bindText($el("div.asm-fempty"), "（文件夹过多，仅显示部分）"));
      }
      updateTreeHighlight(false);
    }
    function updateTreeHighlight(scroll) {
      if (treeCurEl) treeCurEl.classList.remove("cur");
      treeCurEl = treeRowEls[folderPath] || null;
      if (treeCurEl) {
        treeCurEl.classList.add("cur");
        if (scroll && treeCurEl.scrollIntoView) treeCurEl.scrollIntoView({ block: "nearest" });
      }
    }
    // 点树行: 立刻切右侧(不重排树, 只挪高亮)
    function goToFolder(rel, scroll) {
      enterFolder(rel || "");
      updateTreeHighlight(scroll !== false);
    }
    // v1.2.2: 树行点击 —— 多选关 → 进入该文件夹; 多选开(或 Shift) → 勾选该文件夹(与文件选中互斥)
    function pickFolder(rel, ev) {
      const shift = !!(ev && ev.shiftKey);
      if (shift && !multi) { multi = true; setMultiBtns(); statusMsg(t("多选模式: 点击切换选中, Shift+点击连选一段")); }
      if (!multi) { goToFolder(rel); return; }
      if (selected.size) { selected.clear(); selAnchor = null; updateBatchBtn(); }  // 互斥
      if (shift && folAnchor) {
        const i0 = flatTree.findIndex((n) => n.rel === folAnchor);
        const i1 = flatTree.findIndex((n) => n.rel === rel);
        if (i0 >= 0 && i1 >= 0) {
          const a = Math.min(i0, i1), b = Math.max(i0, i1);
          for (let i = a; i <= b; i++) selFolders.add(flatTree[i].rel);
          folAnchor = rel;
          renderTree(); updateFolderBtns(); updateBatchBtn();
          statusMsg(t("已选 ") + selFolders.size + t(" 个文件夹"));
          return;
        }
      }
      if (selFolders.has(rel)) selFolders.delete(rel); else selFolders.add(rel);
      folAnchor = rel;
      renderTree();
      updateFolderBtns();
      updateBatchBtn();
      statusMsg(t("已选 ") + selFolders.size + t(" 个文件夹"));
    }
    async function loadFolderTree() {
      try {
        const res = await fetch("./asset/folder_tree");
        const d = await res.json();
        if (!d.ok) { statusMsg(t("文件夹树加载失败: ") + (terr(d.error) || "")); return; }
        folderTree = d;
        renderTree();
      } catch (e) {
        statusMsg(t("文件夹树加载失败: ") + (e && e.message ? e.message : e));
      }
    }
    async function reloadFolderView() {
      await loadFolderTree();
      await loadFolder(folderPath);
    }
    // ↑/↓: 在已排序已扁平化的树列表里移动高亮并立刻切右侧; 到顶/到底不回绕
    function moveTreeSel(d) {
      if (!flatTree.length) return;
      let idx = flatTree.findIndex((n) => n.rel === folderPath);
      if (idx < 0) {
        if (d < 0) return;   // 当前在根(不在树列表里): ↑ 不动
        idx = -1;            // ↓ 从第一行开始
      }
      const next = idx + d;
      if (next < 0 || next >= flatTree.length) return;
      goToFolder(flatTree[next].rel, true);
    }
    function renderFileCard(f) {
      const on = selected.has(f.rel);
      const isVid = isVideoRenderF(f);
      const card = $el("div.asm-card.asm-fcard" + (on ? ".selected" : ""));
      const thumbSrc = (f.run_dir && f.thumb) ? mediaUrl(f.run_dir, f.thumb) : outUrl(f.rel);
      let thumbEl;
      if (f.kind === "other") thumbEl = $el("div.pico", { textContent: "📄" });
      else if (isVid && !(f.run_dir && f.thumb)) thumbEl = $el("video", { src: thumbSrc, muted: true, playsinline: true, preload: "metadata" });
      else thumbEl = $el("img", { src: thumbSrc, loading: "lazy" });
      card.appendChild($el("div.m", {}, [
        thumbEl,
        isVid ? $el("div.play", { textContent: "▶" }) : null,
        $el("span.badge", { textContent: isVid ? t("视频") : (f.kind === "image" ? t("图") : t("其他")) }),
        on ? $el("div.selmark", { textContent: "✓" }) : null,
      ].filter(Boolean)));
      card.appendChild($el("div.meta", {}, [
        $el("div.nm", { textContent: f.name }),
        $el("div.pr", { textContent: (f.created || "") + (f.size ? " · " + fmtSize(f.size) : "") }),
        f.opened ? $el("div.mo", { textContent: t("打开: ") + f.opened }) : null,
      ].filter(Boolean)));
      card.onclick = (ev) => {
        const shift = !!(ev && ev.shiftKey);
        if (!multi && !shift) {
          // v1.2.7: 非媒体文件(📄)没有可预览的内容 —— 不再打开预览弹窗, 只提示可下载
          if (f.kind === "other") { statusMsg(t("该文件不支持预览，可用「下载文件」保存")); return; }
          openOutputFile(f);
          return;
        }
        pickInFolder(f.rel, ev);
      };
      fGrid.appendChild(card);
    }
    // 右栏文件: 复用搜索框 + 全部/图片/视频 筛选, 再按同一 sortMode 排
    function filterFolderFiles() {
      const kw = q.value.trim().toLowerCase();
      let list = (folderData.files || []).filter((f) => kind === "all" || f.kind === kind);
      if (kw) list = list.filter((f) => String(f.name || "").toLowerCase().indexOf(kw) >= 0);
      return sortItems(list, sortMode, (f) => f.name, (f) => f.created, (f) => f.opened);
    }
    // 右栏 = 纯图片网格(无按钮条, 无文件夹磁贴)
    function renderFolder() {
      renderCrumbs();
      const files = filterFolderFiles();
      const total = (folderData.files || []).length;
      fGrid.innerHTML = "";
      if (!files.length) {
        let msg;
        if (total) msg = t("没有匹配当前筛选的图片");
        else {
          const sub = (folderData.dirs || []).length;   // 当前目录的直接子文件夹数(list_output 同源)
          msg = t("此文件夹没有图片");
          if (sub > 0) msg += LANG === "zh" ? ("，共 " + sub + " 个子文件夹，点左侧进入") : (" — " + sub + " sub-folder(s), pick one on the left");
        }
        fGrid.appendChild($el("div.asm-empty", { textContent: msg }));
        return;
      }
      for (const f of files) renderFileCard(f);
    }
    // 文件夹视图里的点选(多选): 复用 multi / selected(存 rel), 支持 Shift 连选
    function pickInFolder(rel, ev) {
      const shift = !!(ev && ev.shiftKey);
      if (shift && !multi) { multi = true; setMultiBtns(); statusMsg(t("多选模式: 点击切换选中, Shift+点击连选一段")); }
      if (!multi) return;
      // v1.2.2: 互斥 —— 选文件即清空文件夹选中
      if (selFolders.size) { selFolders.clear(); folAnchor = null; renderTree(); }
      const order = filterFolderFiles().map((f) => f.rel);   // Shift 连选按「当前显示顺序」
      if (shift && selAnchor) {
        const i0 = order.indexOf(selAnchor), i1 = order.indexOf(rel);
        if (i0 >= 0 && i1 >= 0) {
          const a = Math.min(i0, i1), b = Math.max(i0, i1);
          for (let i = a; i <= b; i++) selected.add(order[i]);
          selAnchor = rel;
          renderFolder();
          updateBatchBtn();
          updateFolderBtns();
          return;
        }
      }
      if (selected.has(rel)) selected.delete(rel); else selected.add(rel);
      selAnchor = rel;
      renderFolder();
      updateBatchBtn();
      updateFolderBtns();
    }
    function enterFolder(rel) {
      const next = rel || "";
      if (next !== folderPath) { selected.clear(); selAnchor = null; updateBatchBtn(); }
      folderPath = next;
      renderCrumbs();   // 面包屑立刻跟随, 不等右侧 fetch
      loadFolder(next);
    }
    async function loadFolder(rel) {
      const target = (typeof rel === "string") ? rel : folderPath;
      try {
        const res = await fetch("./asset/list_output?path=" + encodeURIComponent(target));
        const d = await res.json();
        if (!d.ok) { statusMsg(t("文件夹加载失败: ") + (terr(d.error) || "")); return; }
        const next = d.path || "";
        if (next !== folderPath) { selected.clear(); selAnchor = null; }
        folderPath = next;
        folderData = d;
        renderFolder();
        updateTreeHighlight(false);
        updateBatchBtn();
        updateFolderBtns();
        reportOpen("out:" + folderPath); // 进入文件夹(根 "" 也上报, key = "out:")
      } catch (e) {
        statusMsg(t("文件夹加载失败: ") + (e && e.message ? e.message : e));
      }
    }
    async function newFolder() {
      const nm = prompt(t("新建文件夹") + (folderPath ? (" — " + folderPath) : ""), "");
      if (nm === null) return;
      const name = String(nm).trim();
      if (!name) return;
      try {
        const d = await postJSON("./asset/mkdir_output", { path: folderPath, name: name });
        if (d.ok) {
          statusMsg(LANG === "zh" ? ("已新建文件夹: " + name) : ("Folder created: " + name));
          await reloadFolderView();
        } else statusMsg(t("新建失败: ") + (terr(d.error) || ""));
      } catch (e) { statusMsg(t("新建失败: ") + (e && e.message ? e.message : e)); }
    }
    // 改名作用于「当前文件夹」(根目录提示并中止)
    async function renameFolder() {
      if (!folderPath) { statusMsg(t("（根目录不能改名）")); return; }
      const oldName = dirNameOf(folderPath);
      const nm = prompt(t("新名称:"), oldName);
      if (nm === null) return;
      const name = String(nm).trim();
      if (!name) return;
      try {
        const d = await postJSON("./asset/rename_output", { path: folderPath, name: name });
        if (d.ok) {
          folderPath = d.rel || folderPath;   // 用返回的新 rel 继续停留在这个文件夹
          statusMsg(LANG === "zh" ? ("已改名: " + oldName + " → " + name) : ("Renamed: " + oldName + " → " + name));
          await reloadFolderView();
        } else statusMsg(t("改名失败: ") + (terr(d.error) || ""));
      } catch (e) { statusMsg(t("改名失败: ") + (e && e.message ? e.message : e)); }
    }
    // v1.2.2: 有文件夹选中 → 删这些文件夹(逐个走「先报文件数→二次确认→recursive」);
    //          没有文件夹选中 → 删当前文件夹(v1.2.1 行为)。根目录永不可删。
    async function deleteFolder() {
      const targets = selFolders.size ? [...selFolders].filter((r) => r !== "") : (folderPath ? [folderPath] : []);
      if (!targets.length) { statusMsg(t("（根目录不能删除）")); return; }
      const ask = targets.length === 1
        ? (LANG === "zh" ? ("确定删除文件夹「" + dirNameOf(targets[0]) + "」吗？") : ("Delete folder \"" + dirNameOf(targets[0]) + "\"?"))
        : (LANG === "zh" ? ("确定删除选中的 " + targets.length + " 个文件夹吗？") : ("Delete the " + targets.length + " selected folder(s)?"));
      if (!confirm(ask)) return;
      try {
        // 先非递归探测: 空文件夹会被直接删掉, 非空的收进 blocked 等二次确认
        const blocked = [];
        let deleted = 0;
        for (const rel of targets) {
          const d = await postJSON("./asset/delete_output_dir", { path: rel, recursive: false });
          if (d.ok) { deleted++; continue; }
          if (d.error === "Folder is not empty") blocked.push({ rel, files: typeof d.files === "number" ? d.files : 0 });
          else statusMsg(t("删除失败: ") + (terr(d.error) || ""));
        }
        if (blocked.length) {
          const totalFiles = blocked.reduce((s, x) => s + x.files, 0);
          const list = blocked.map((x) => "• " + dirNameOf(x.rel) + " (" + x.files + ")").join("\n");
          const more = LANG === "zh"
            ? ("以下文件夹不为空, 共 " + totalFiles + " 个文件, 连带一起删除？\n\n" + list)
            : ("These folders are not empty (" + totalFiles + " files in total). Delete the files as well?\n\n" + list);
          if (!confirm(more)) {
            statusMsg(LANG === "zh" ? ("已删除 " + deleted + " 个空文件夹，其余已取消") : ("Deleted " + deleted + " empty folder(s); the rest was cancelled"));
            await loadRuns();
            await reloadFolderView();
            return;
          }
          for (const x of blocked) {
            const d = await postJSON("./asset/delete_output_dir", { path: x.rel, recursive: true });
            if (d.ok) deleted++;
            else statusMsg(t("删除失败: ") + (terr(d.error) || ""));
          }
        }
        selFolders.clear();
        folAnchor = null;
        statusMsg(LANG === "zh" ? ("已删除 " + deleted + " 个文件夹") : ("Deleted " + deleted + " folder(s)"));
        await loadRuns();
        const wasCurrent = targets.indexOf(folderPath) >= 0;
        if (wasCurrent) goToFolder(parentOf(folderPath));
        else await reloadFolderView();
      } catch (e) { statusMsg(t("删除失败: ") + (e && e.message ? e.message : e)); }
    }
    function cutSelected() {
      if (!selected.size) { statusMsg(t("（请先选中要移动的项）")); return; }
      clipboard = { items: [...selected] };
      updateFolderBtns();
      statusMsg(LANG === "zh"
        ? ("已剪切 " + clipboard.items.length + " 项, 进入目标文件夹后点「粘贴」")
        : ("Cut " + clipboard.items.length + " item(s); open the target folder and click Paste"));
    }
    async function pasteClipboard() {
      if (!clipboard || !clipboard.items.length) { statusMsg(t("剪贴板为空")); return; }
      const items = clipboard.items.slice();
      try {
        const d = await postJSON("./asset/move_output", { from: items, to: folderPath });
        if (!d.ok) { statusMsg(t("移动失败: ") + (terr(d.error) || "")); return; }
        const moved = d.moved_count || 0;
        const failed = d.failed_count || 0;
        const renamed = (d.moved || []).filter((x) => x.renamed).length;
        clipboard = null;
        selected.clear();
        selAnchor = null;
        updateBatchBtn();
        updateFolderBtns();
        await loadRuns();
        await loadFolderTree();
        await loadFolder(folderPath);
        const base = LANG === "zh" ? ("已移动 " + moved + " 项") : ("Moved " + moved + " item(s)");
        const extra = failed ? (LANG === "zh" ? ("（失败 " + failed + " 项）") : (" (" + failed + " failed)")) : "";
        const rn = renamed ? (LANG === "zh" ? ("；" + renamed + " 项因同名已自动改名") : ("; " + renamed + " renamed to avoid collision")) : "";
        statusMsg(base + extra + rn);
      } catch (e) { statusMsg(t("移动失败: ") + (e && e.message ? e.message : e)); }
    }
    function openOutputFile(f) {
      // v1.2.2: 传入当前显示列表 → 文件夹视图里也能 ←/→ 翻页(与网格/日历一致)
      // v1.2.7: 翻页列表只含可预览的媒体(图/视频) —— 📄 其他文件不进翻页序列
      openOutputPreview(f, previewFolderFiles());
    }
    // 可预览列表 = 当前显示列表(含搜索/kind 筛选)去掉「其他」文件
    function previewFolderFiles() {
      return filterFolderFiles().filter((f) => f.kind !== "other");
    }
    // 整份可预览列表 = 当前文件夹里全部可预览媒体(**忽略筛选**) —— 供"筛选后剩1项"的回退
    function allPreviewFolderFiles() {
      return sortItems((folderData.files || []).filter((f) => f.kind !== "other"), sortMode,
                       (x) => x.name, (x) => x.created, (x) => x.opened);
    }
    // v1.2.2: 按钮启用规则 —— 剪切/粘贴仅「文件」类型; 下载任一类型; 删除看文件夹选中或当前文件夹
    function updateFolderBtns() {
      const nf = selected.size, nd = selFolders.size;
      fCutBtn.textContent = t("剪切") + (nf ? "(" + nf + ")" : "");
      fCutBtn.disabled = nf === 0;
      const c = (clipboard && clipboard.items) ? clipboard.items.length : 0;
      fPasteBtn.textContent = t("粘贴") + (c ? "(" + c + ")" : "");
      fPasteBtn.disabled = c === 0;
      const dl = nd || nf;
      fDlBtn.textContent = t("下载") + (dl ? "(" + dl + ")" : "");
      fDlBtn.disabled = dl === 0;
      fRenBtn.disabled = !folderPath;
      fDelBtn.textContent = t("删除") + (nd ? "(" + nd + ")" : "");
      fDelBtn.disabled = !nd && !folderPath;
    }
    // ↑/↓ 键盘导航: 作用域严格限定, 其余情况一律不拦截(不抢 ComfyUI 画布按键)
    function onFolderKey(e) {
      if (overlay.style.display !== "flex") return;
      if (view !== "folder") return;
      if (pv) return;                                   // 大图预览打开 → 交给预览的 ←/→/Esc
      const el = e.target || {};
      const tag = String(el.tagName || "").toUpperCase();
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable) return;
      if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
      e.preventDefault();
      e.stopPropagation();
      moveTreeSel(e.key === "ArrowDown" ? 1 : -1);
    }
    document.addEventListener("keydown", onFolderKey, true);

    function refresh() {
      // v1.2.2: 文件夹/日历视图下 body 不滚, 左右两栏各自独立滚动; 网格视图保持整页滚动
      body.classList.toggle("asm-noscroll", view !== "grid");
      if (view === "grid") { gridEl.style.display = ""; calWrap.style.display = "none"; folderWrap.style.display = "none"; renderGrid(); }
      else if (view === "cal") { gridEl.style.display = "none"; calWrap.style.display = ""; folderWrap.style.display = "none"; renderCal(); }
      else {
        gridEl.style.display = "none"; calWrap.style.display = "none"; folderWrap.style.display = "";
        renderFolder();
        updateTreeHighlight(false);
      }
      updateBatchBtn();
      updateFolderBtns();
    }

    // ---------- 多选 / 批量删除 ----------
    function updateBatchBtn() {
      // 文件夹视图的选中集合存 rel(非 run dir), 批量删除/下载只对归档条目有效 → 该视图下隐藏这两个按钮
      // v1.2.3: 顶部工具栏的「多选」也在此视图隐藏(左栏行2 有唯一入口), 消除重复按钮
      if (view === "folder") {
        batchBtn.style.display = "none";
        batchDownloadBtn.style.display = "none";
        multiBtn.style.display = "none";
      } else if (multi && selected.size > 0) {
        multiBtn.style.display = "";
        batchBtn.style.display = "";
        batchBtn.textContent = t("🗑 删除选中") + "(" + selected.size + ")";
        batchDownloadBtn.style.display = "";
        batchDownloadBtn.textContent = t("⬇ 下载选中") + "(" + selected.size + ")";
      } else {
        multiBtn.style.display = "";
        batchBtn.style.display = "none";
        batchDownloadBtn.style.display = "none";
      }
    }
    function toggleMulti() {
      multi = !multi;
      setMultiBtns();
      selected.clear();
      selAnchor = null;
      selFolders.clear();
      folAnchor = null;
      updateBatchBtn();
      updateFolderBtns();
      refresh();
      statusMsg(multi ? t("多选模式: 点击切换选中, Shift+点击连选一段") : t("已退出多选"));
    }
    async function batchDelete() {
      if (!selected.size) return;
      const ids = [...selected];
      const msg = LANG === "zh"
        ? ("确定要从硬盘永久删除选中的 " + ids.length + " 项产物吗?\n\n将同时删除归档副本和 output 中的原始文件, 无法恢复。")
        : ("Permanently delete the selected " + ids.length + " items from disk?\n\nThis also deletes the archive copies and the original files in output. This cannot be undone.");
      if (!confirm(msg)) return;
      const res = await fetch("./asset/delete_batch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_ids: ids }) });
      const d = await res.json();
      if (d.ok) {
        const delSet = new Set(ids);
        runs = runs.filter(x => !delSet.has(x.dir));
        selected.clear();
        selAnchor = null;
        rebuildByDate();
        refresh();
        const done = LANG === "zh" ? ("已删除 " + d.deleted + " 项") : ("Deleted " + d.deleted + " items");
        const extra = d.failed && d.failed.length ? (LANG === "zh" ? ("（失败 " + d.failed.length + " 项）") : (" (failed: " + d.failed.length + ")")) : "";
        statusMsg(done + extra);
      } else {
        statusMsg(t("批量删除失败: ") + (terr(d.error) || ""));
      }
    }

    // ---------- 预览(大图内 ←/→ 快速切换) ----------
    let pv = null; // { m, step } —— 当前打开的大图预览

    function previewMedia(r) {
      const full = mediaUrl(r.dir, r.media);
      // v1.2.6: .gif 是动图, 必须按 <img> 渲染(塞进 <video> 会黑屏)
      return isVideoRender(r)
        ? $el("video", { src: full, controls: true, autoplay: true, muted: true, playsinline: true })
        : $el("img", { src: full });
    }

    // v1.2.6: 视频在浏览器里放不出来(编码/容器不支持)时的明确提示面板
    function unplayableBox(name) {
      return $el("div", { style: { textAlign: "center", color: "var(--descrip-text,#aaa)", padding: "30px 20px" } }, [
        $el("div", { textContent: "⚠", style: { fontSize: "34px", marginBottom: "10px" } }),
        $el("div", { textContent: t("浏览器无法播放该视频"), style: { fontSize: "14px", color: "var(--fg-color,#eee)", marginBottom: "6px" } }),
        $el("div", { textContent: name || "", style: { fontSize: "12px", wordBreak: "break-all", marginBottom: "4px" } }),
        $el("div", { textContent: t("可用「下载文件」保存后用本地播放器打开"), style: { fontSize: "12px" } }),
      ]);
    }

    function closePreview() {
      if (pv && pv.m) pv.m.remove();
      pv = null;
    }

    function openPreview(r, listArg) {
      // 切换范围 = 用户当前看到的那一批(网格=筛选结果; 日历=当天列表)
      const list = (Array.isArray(listArg) && listArg.length ? listArg : sortRuns(filtered(runs))).slice();
      let idx = list.findIndex(x => x.dir === r.dir);
      if (idx < 0) return;
      if (pv) closePreview();
      reportOpen("run:" + r.dir); // 打开归档资产的打开时间上报(失败静默)

      const m = $el("div.asm-modal");
      m.style.display = "flex";
      const mediaBox = $el("div.media");
      const rowsEl = $el("div.rows");
      const ta = $el("textarea");
      const pagerEl = $el("div.pvbar");
      const prevBtn = $el("button.nav.prev", { textContent: "‹" });
      const nextBtn = $el("button.nav.next", { textContent: "›" });
      prevBtn.title = t("上一张 (←)");
      nextBtn.title = t("下一张 (→)");
      prevBtn.onclick = () => step(-1);
      nextBtn.onclick = () => step(1);

      function paramsOf(x) {
        return Object.keys(x.params || {}).map(k => k + "=" + x.params[k]).join(" · ") || "—";
      }
      // 预加载相邻图片, 切换时基本无等待
      function preload(i) {
        for (const k of [i - 1, i + 1]) {
          const x = list[(k + list.length) % list.length];
          if (x && x.kind === "image") { try { const im = new Image(); im.src = mediaUrl(x.dir, x.media); } catch (e) {} }
        }
      }
      function show(i) {
        idx = ((i % list.length) + list.length) % list.length;
        const cur = list[idx];
        mediaBox.innerHTML = "";
        const media = previewMedia(cur);
        mediaBox.appendChild(media);
        // v1.2.6: 视频放不出来(编码/容器不支持)时给明确提示, 不再黑屏
        if (media.tagName === "VIDEO") {
          media.addEventListener("error", () => {
            mediaBox.innerHTML = "";
            mediaBox.appendChild(unplayableBox(cur.name));
          });
        }
        ta.value = (cur.positive || "") + (cur.negative ? "\n\nNegative prompt: " + cur.negative : "");
        rowsEl.innerHTML = "";
        rowsEl.appendChild(labeledRow([{ zh: "来源: ", text: cur.name }]));
        rowsEl.appendChild(labeledRow([{ zh: "时间: ", text: cur.time + " | " }, { zh: "模型/LoRA: ", text: (cur.models || []).join(", ") || "—" }]));
        rowsEl.appendChild(labeledRow([{ zh: "参数: ", text: paramsOf(cur) }]));
        pagerEl.textContent = (idx + 1) + " / " + list.length;
        const solo = list.length < 2;
        prevBtn.style.display = solo ? "none" : "";
        nextBtn.style.display = solo ? "none" : "";
        pagerEl.style.display = solo ? "none" : "";
        delBtn.onclick = () => doDelete(cur, m, () => {
          const at = list.indexOf(cur);
          if (at >= 0) list.splice(at, 1);
          if (!list.length) { closePreview(); return; }
          show(Math.min(at, list.length - 1));
        });
        preload(idx);
      }
      function step(d) { if (list.length > 1) show(idx + d); }

      const copyBtn = bindText($el("button.asm-btn", { onclick: () => { ta.select(); navigator.clipboard?.writeText(ta.value).then(() => statusMsg(t("已复制"))); } }), "复制提示词");
      const dlBtn = bindText($el("button.asm-btn.primary", { onclick: () => downloadMediaFile(list[idx]) }), "下载文件");
      // v1.2.8: 工作流不落散落文件, 需要时从 info.json 重组下载
      const wfBtn = bindText($el("button.asm-btn", { onclick: async () => {
        const cur = list[idx];
        if (!cur || !cur.dir) return;
        const info = await fetchRunInfo(cur.dir);
        await saveWorkflowJson(info, cur.media);
      } }), "保存 workflow.json");
      const delBtn = bindText($el("button.asm-btn.danger"), "🗑 从硬盘删除");

      const mediaWrap = $el("div.mediaWrap", {}, [mediaBox, prevBtn, nextBtn]);
      const pn = $el("div.pn", {}, [
        $el("button.x", { textContent: "✕", onclick: () => closePreview() }),
        pagerEl,
        mediaWrap,
        rowsEl,
        bindText($el("label", { style: { fontSize: "12px" } }), "提示词"),
        ta,
        $el("div.btns", {}, [copyBtn, dlBtn, wfBtn, delBtn]),
      ]);
      m.appendChild($el("div.bk", { onclick: () => closePreview() }));
      m.appendChild(pn);
      document.body.appendChild(m);
      pv = { m, step };
      show(idx);
    }

    // 文件夹视图里预览 output 文件; v1.2.2: 与网格/日历一致, ←/→ 翻页(循环 / n 总数 / 预加载)
    function openOutputPreview(f, listArg) {
      let list = (Array.isArray(listArg) && listArg.length ? listArg : previewFolderFiles()).slice();
      // v1.2.4: 若翻页列表只剩一项、但当前文件夹里其实有多张可预览的媒体, 则改用整份
      // 可预览列表来翻页 —— 否则一侧的箭头会跟着消失(用户反馈"看不到左右箭头"的常见触发)。
      if (list.length < 2) {
        const all = allPreviewFolderFiles();
        if (all.length > list.length) list = all;
      }
      let idx = list.findIndex((x) => x.rel === f.rel);
      if (idx < 0) { list.unshift(f); idx = 0; }
      if (pv) closePreview();

      const m = $el("div.asm-modal");
      m.style.display = "flex";
      const mediaBox = $el("div.media");
      const rowsEl = $el("div.rows");
      const pagerEl = $el("div.pvbar");
      const prevBtn = $el("button.nav.prev", { textContent: "‹" });
      const nextBtn = $el("button.nav.next", { textContent: "›" });
      prevBtn.title = t("上一张 (←)");
      nextBtn.title = t("下一张 (→)");
      prevBtn.onclick = () => step(-1);
      nextBtn.onclick = () => step(1);

      function mediaFor(x) {
        // v1.2.6: .gif 按图片渲染(塞进 <video> 会黑屏); 视频用 <video>
        if (isGifRel(x.name)) return $el("img", { src: outUrl(x.rel) });
        if (isVideoRenderF(x)) return $el("video", { src: outUrl(x.rel), controls: true, autoplay: true, muted: true, playsinline: true });
        if (x.kind === "image") return $el("img", { src: outUrl(x.rel) });
        return $el("div", { textContent: t("该文件无法预览") });
      }
      function preload(i) {
        for (const k of [i - 1, i + 1]) {
          const x = list[(k + list.length) % list.length];
          if (x && x.kind === "image") { try { const im = new Image(); im.src = outUrl(x.rel); } catch (e) {} }
        }
      }
      function show(i) {
        idx = ((i % list.length) + list.length) % list.length;
        const cur = list[idx];
        mediaBox.innerHTML = "";
        const media = mediaFor(cur);
        mediaBox.appendChild(media);
        // v1.2.6: 视频放不出来(编码/容器不支持)时给明确提示, 不再黑屏
        if (media.tagName === "VIDEO") {
          media.addEventListener("error", () => {
            mediaBox.innerHTML = "";
            mediaBox.appendChild(unplayableBox(cur.name));
          });
        }
        rowsEl.innerHTML = "";
        rowsEl.appendChild(labeledRow([{ zh: "文件名: ", text: cur.name }]));
        rowsEl.appendChild(labeledRow([{ zh: "时间: ", text: (cur.created || "") + " | " + (cur.mtime || "") }]));
        rowsEl.appendChild(labeledRow([{ zh: "大小: ", text: fmtSize(cur.size) }]));
        rowsEl.appendChild(labeledRow([{ zh: "路径: ", text: cur.rel }]));
        pagerEl.textContent = (idx + 1) + " / " + list.length;
        const solo = list.length < 2;
        prevBtn.style.display = solo ? "none" : "";
        nextBtn.style.display = solo ? "none" : "";
        pagerEl.style.display = solo ? "none" : "";
        preload(idx);
                reportOpen("out:" + cur.rel); // 翻页也上报打开时间
        // v1.2.3: 已归档的文件可复制提示词; v1.2.6: 「下载文件」对任何文件都可用
        ta.value = "";
        copyBtn.disabled = true;
        // v1.2.8: 未归档的文件没有 info.json, 无工作流可重组
        wfBtn.disabled = !cur.run_dir;
        if (!cur.run_dir) {
          bindText(ta, "该文件未归档，没有提示词元数据", "placeholder");
          return;
        }
        bindText(ta, "提示词", "placeholder");
        fetchRunInfo(cur.run_dir).then((info) => {
          if (list[idx] !== cur) return; // 翻页了就别回填
          if (!info) { bindText(ta, "该文件未归档，没有提示词元数据", "placeholder"); return; }
          ta.value = (info.positive || "") + (info.negative ? "\n\nNegative prompt: " + info.negative : "");
          copyBtn.disabled = !ta.value;
        });
      }
      function step(d) { if (list.length > 1) show(idx + d); }

      const ta = $el("textarea");
      bindText(ta, "提示词", "placeholder");
      const copyBtn = bindText($el("button.asm-btn", { onclick: () => { ta.select(); navigator.clipboard?.writeText(ta.value).then(() => statusMsg(t("已复制"))); } }), "复制提示词");
      const dlBtn = bindText($el("button.asm-btn.primary", { onclick: () => downloadOutputFile(list[idx]) }), "下载文件");
      // v1.2.8: 工作流不落散落文件, 需要时从归档 info.json 重组下载(未归档的文件禁用)
      const wfBtn = bindText($el("button.asm-btn", { onclick: async () => {
        const cur = list[idx];
        if (!cur || !cur.run_dir) return;
        const info = await fetchRunInfo(cur.run_dir);
        await saveWorkflowJson(info, cur.name);
      } }), "保存 workflow.json");
      const delBtn = bindText($el("button.asm-btn.danger", { onclick: () => deleteOutputFile(list[idx]) }), "🗑 从硬盘删除");
      const mediaWrap = $el("div.mediaWrap", {}, [mediaBox, prevBtn, nextBtn]);
      const pn = $el("div.pn", {}, [
        $el("button.x", { textContent: "✕", onclick: () => closePreview() }),
        pagerEl,
        mediaWrap,
        rowsEl,
        bindText($el("label", { style: { fontSize: "12px" } }), "提示词"),
        ta,
        $el("div.btns", {}, [copyBtn, dlBtn, wfBtn, delBtn,
          bindText($el("button.asm-btn", { onclick: () => closePreview() }), "关闭"),
        ]),
      ]);
      m.appendChild($el("div.bk", { onclick: () => closePreview() }));
      m.appendChild(pn);
      document.body.appendChild(m);
      pv = { m, step };
      show(idx);
    }
    // 归档 info.json 缓存 + 取用(v1.2.3, 供文件夹视图预览对齐其它视图)
    const runInfoCache = {};
    async function fetchRunInfo(dir) {
      if (dir in runInfoCache) return runInfoCache[dir];
      let info = null;
      try {
        const res = await fetch("./asset/file?p=" + encodeURIComponent(dir + "/info.json"), { cache: "no-store" });
        if (res.ok) info = await res.json();
      } catch (e) { info = null; }
      runInfoCache[dir] = info;
      return info;
    }
    // v1.2.6: 「下载文件」—— 把 output 里的原始文件本体存下来(视频/图/其他都行)
    async function downloadOutputFile(f) {
      if (!f || !f.rel) return;
      try {
        const res = await fetch("./asset/output_file?p=" + encodeURIComponent(f.rel), { cache: "no-store" });
        if (!res.ok) { statusMsg(t("下载失败")); return; }
        const blob = await res.blob();
        const mode = await saveBlobToLocal(blob, safeName(f.name));
        statusMsg(mode === "dir" && dlDirHandle && dlDirHandle.name
          ? (LANG === "zh" ? ("✅ 已保存 " + safeName(f.name) + " → 本地目录: " + dlDirHandle.name) : ("✅ Saved " + safeName(f.name) + " → local folder: " + dlDirHandle.name))
          : (LANG === "zh" ? ("✅ 已开始下载: " + safeName(f.name)) : ("✅ Download started: " + safeName(f.name))));
      } catch (e) {
        statusMsg(t("下载失败") + (e && e.message ? "  " + e.message : ""));
      }
    }
    // 删除单个 output 文件(已归档的连带删归档条目, 与网格预览的删除同语义)
    async function deleteOutputFile(f) {
      if (!f) return;
      const archived = !!f.run_dir;
      const msg = LANG === "zh"
        ? ("确定要从硬盘删除该文件吗?\n\n" + f.rel + (archived ? "\n\n将同时删除它的归档副本, 无法恢复。" : "\n\n无法恢复。"))
        : ("Delete this file from disk?\n\n" + f.rel + (archived ? "\n\nIts archive copy will be deleted as well. This cannot be undone." : "\n\nThis cannot be undone."));
      if (!confirm(msg)) return;
      const d = await postJSON("./asset/delete_output_file", { path: f.rel });
      if (!d.ok) { statusMsg(t("删除失败: ") + (terr(d.error) || "")); return; }
      statusMsg(t("已从硬盘删除"));
      const at = list.indexOf(f);
      if (at >= 0) list.splice(at, 1);
      if (!list.length) closePreview();
      else show(Math.min(at < 0 ? 0 : at, list.length - 1));
      await loadRuns();
      await loadFolderTree();
      await loadFolder(folderPath);
    }

    // 预览打开时: ←/→ 翻页, Esc 关闭(文本域内方向键仍用于移光标)
    function onPreviewKey(e) {
      if (!pv) return;
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closePreview(); return; }
      const tag = (e.target && e.target.tagName) || "";
      if (tag === "TEXTAREA" || tag === "INPUT" || tag === "SELECT") return;
      if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); pv.step(-1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); pv.step(1); }
    }
    document.addEventListener("keydown", onPreviewKey, true);

    // v1.2.6: 「下载文件」—— 把归档库里的媒体副本本体存下来(原文件名)
    async function downloadMediaFile(r) {
      if (!r || !r.media) { statusMsg(t("该产物未携带媒体文件")); return; }
      try {
        const res = await fetch("./asset/file?p=" + encodeURIComponent(r.dir + "/" + r.media), { cache: "no-store" });
        if (!res.ok) { statusMsg(t("下载失败")); return; }
        const blob = await res.blob();
        const mode = await saveBlobToLocal(blob, safeName(r.media));
        statusMsg(mode === "dir" && dlDirHandle && dlDirHandle.name
          ? (LANG === "zh" ? ("✅ 已保存 " + safeName(r.media) + " → 本地目录: " + dlDirHandle.name) : ("✅ Saved " + safeName(r.media) + " → local folder: " + dlDirHandle.name))
          : (LANG === "zh" ? ("✅ 已开始下载: " + safeName(r.media)) : ("✅ Download started: " + safeName(r.media))));
      } catch (e) {
        statusMsg(t("下载失败") + (e && e.message ? "  " + e.message : ""));
      }
    }

    // v1.2.8: 「保存 workflow.json」—— 从归档 info.json 的 workflow_json 字段重组下载(不再依赖磁盘散落文件)。
    // 文件名 = <媒体名>.workflow.json, 解决"工作流文件难以直观配对"的原始痛点。
    async function saveWorkflowJson(info, mediaName) {
      const wf = info && info.workflow_json;
      if (!wf || typeof wf !== "object") { statusMsg(t("该产物未携带工作流元数据")); return; }
      const base = safeName(mediaName || "workflow").replace(/\.[^.]+$/, "");
      const blob = new Blob([JSON.stringify(wf, null, 1)], { type: "application/json" });
      try {
        await saveBlobToLocal(blob, base + ".workflow.json");
        statusMsg(t("✅ 已保存 workflow.json"));
      } catch (e) {
        statusMsg(t("下载失败") + (e && e.message ? "  " + e.message : ""));
      }
    }

    async function doDelete(r, modal, onDone) {
      const msg = LANG === "zh"
        ? ("确定要从硬盘永久删除该产物吗?\n\n" + r.name + "\n\n将同时删除归档副本和 output 中的原始文件, 无法恢复。")
        : ("Permanently delete this asset from disk?\n\n" + r.name + "\n\nThis also deletes the archive copy and the original file in output. This cannot be undone.");
      if (!confirm(msg)) return;
      const res = await fetch("./asset/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_id: r.dir }) });
      const d = await res.json();
      if (d.ok) {
        runs = runs.filter(x => x.dir !== r.dir);
        rebuildByDate(); refresh(); statusMsg(t("已从硬盘删除"));
        if (typeof onDone === "function") onDone();
        else if (modal) modal.remove();
      } else statusMsg(t("删除失败: ") + (terr(d.error) || t("未知错误")));
    }

    // ---------- 设置 ----------
    async function openSettings() {
      try { curConfig = await (await fetch("./asset/config")).json(); } catch (e) {}
      const c = curConfig.config || {};
      const m = $el("div.asm-modal");
      m.style.display = "flex";
      const fOut = $el("input", { value: curConfig.current_output_dir || "" });
      bindText(fOut, "留空=使用 ComfyUI 默认 output", "placeholder");
      const fArch = $el("input", { value: curConfig.archive_dir || c.archive_dir || "" });
      const fDlDir = $el("input", { value: c.download_dir || "C:\\Users\\Administrator\\Downloads\\" });
      bindText(fDlDir, "C:\\Users\\Administrator\\Downloads\\", "placeholder");
      const fAuto = $el("input", { type: "checkbox" });
      fAuto.checked = c.auto_archive !== false;
      const fAutoDl = $el("input", { type: "checkbox" });
      fAutoDl.checked = c.auto_download === true;
      const fExisting = $el("input", { type: "checkbox" });
      fExisting.checked = c.archive_existing === true;
      await loadDlHandle();
      if (dlDirHandle && dlDirHandle.name && !fDlDir.value) fDlDir.value = dlDirHandle.name;
      const fThumb = $el("input", { type: "number", min: 100, max: 2000, value: String(c.thumb_width || 480) });
      const fInterval = $el("input", { type: "number", min: 3, max: 3600, value: String(c.interval_sec || 10) });
      const fMode = $el("select");
      const oRaw = $el("option", { value: "raw" });
      oRaw.textContent = t("原样保存(不打包)");
      const oZip = $el("option", { value: "zip" });
      oZip.textContent = t("打包为 ZIP");
      fMode.appendChild(oRaw);
      fMode.appendChild(oZip);
      fMode.value = c.download_mode === "zip" ? "zip" : "raw";
      const fMeta = $el("input", { type: "checkbox" });
      fMeta.checked = c.download_include_metadata === true;
      const fKeepFolders = $el("input", { type: "checkbox" });
      fKeepFolders.checked = c.download_keep_folders === true;

      const row = (zh, input, browse) => $el("div.row", {}, [
        bindText($el("label"), zh), input,
        browse ? bindText($el("button.asm-btn", { onclick: () => browseDir(input) }), "浏览…") : null,
      ].filter(Boolean));

      const pn = $el("div.pn", {}, [
        $el("button.x", { textContent: "✕", onclick: () => m.remove() }),
        bindText($el("h2", { style: { margin: "0 0 10px", fontSize: "15px" } }), "⚙ 资产设置"),
        $el("div.asm-set", {}, [
          row("输出目录", fOut, true),
          row("归档库目录", fArch, true),
          $el("div.row", {}, [
            bindText($el("label"), "下载目录"),
            fDlDir,
            bindText($el("button.asm-btn", { onclick: () => pickDlDir(fDlDir) }), "浏览…"),
          ]),
          $el("div.row", {}, [
            bindText($el("label"), "下载方式"),
            fMode,
          ]),
          $el("div.chk", {}, [fMeta, bindText($el("span"), "下载包含 json/txt 元数据")]),
          $el("div.chk", {}, [fKeepFolders, bindText($el("span"), "下载保留每张图的文件夹")]),
          $el("div.chk", {}, [fAuto, bindText($el("span"), "自动归档新产物")]),
          $el("div.chk", {}, [fAutoDl, bindText($el("span"), "自动下载新产物")]),
          $el("div.chk", {}, [fExisting, bindText($el("span"), "归档安装前已有的产物")]),
          row("缩略图宽度(px)", fThumb),
          row("扫描间隔(秒)", fInterval),
        ]),
        $el("div.btns", {}, [
          bindText($el("button.asm-btn.primary", { onclick: saveSettings }), "保存设置"),
        ]),
        bindText($el("div", { style: { fontSize: "11px", color: "var(--descrip-text,#aaa)", marginTop: "10px" } }), "下载默认只保存图片/视频本体并全部平铺（缩略图始终不下载, 不建每张图的文件夹）; 需要元数据或文件夹时勾选上面的两个开关。改归档/下载目录后新产物进入新目录, 旧数据保留; 输出目录切换重启 ComfyUI 后仍生效; 自动归档/自动下载开关和扫描间隔即时生效。下载目录: 点「浏览…」可在系统对话框选择本地目录（授权后下载/自动下载直接写入该目录, 无需经过浏览器下载; 未授权时使用浏览器默认下载目录）。"),
      ]);
      m.appendChild($el("div.bk", { onclick: () => m.remove() }));
      m.appendChild(pn);
      document.body.appendChild(m);

      async function saveSettings() {
        const payload = {
          output_dir: fOut.value.trim(),
          archive_dir: fArch.value.trim(),
          download_dir: fDlDir.value.trim(),
          auto_archive: fAuto.checked,
          auto_download: fAutoDl.checked,
          archive_existing: fExisting.checked,
          download_mode: fMode.value,
          download_include_metadata: fMeta.checked,
          download_keep_folders: fKeepFolders.checked,
          thumb_width: Number(fThumb.value),
          interval_sec: Number(fInterval.value),
        };
        const r = await fetch("./asset/set_config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        const d = await r.json();
        if (d.ok) {
          curConfig = { config: d.config, archive_dir: d.archive_dir, current_output_dir: d.current_output_dir };
          m.remove();
          const extra = (d.errors && d.errors.length) ? (LANG === "zh" ? ("（部分项未生效: " + d.errors.join("; ") + "）") : (" (some failed: " + d.errors.join("; ") + ")")) : "";
          statusMsg(t("✅ 设置已保存") + extra);
          await loadRuns(); refresh();
        } else {
          statusMsg(t("保存失败: ") + (terr(d.error) || ""));
        }
      }
    }

    // ---------- 目录浏览选择器 ----------
    async function browseDir(inputEl) {
      const m = $el("div.asm-modal");
      m.style.display = "flex";
      const pathEl = $el("div", { style: { fontSize: "12px", color: "var(--descrip-text,#aaa)", marginBottom: "8px", wordBreak: "break-all" } });
      const listEl = $el("div", { style: { maxHeight: "320px", overflowY: "auto", border: "1px solid var(--border-color,#444)", borderRadius: "6px" } });
      let curPath = inputEl.value.trim() || "";

      async function load(path) {
        try {
          const res = await fetch("./asset/browse_dir?path=" + encodeURIComponent(path));
          const d = await res.json();
          if (!d.ok) { pathEl.textContent = t("错误: ") + (terr(d.error) || ""); listEl.innerHTML = ""; return; }
          curPath = d.path || "";
          pathEl.textContent = t("当前: ") + (curPath || t("（请选择磁盘）"));
          listEl.innerHTML = "";
          if (!d.dirs.length) {
            listEl.appendChild($el("div", { textContent: t("（无子目录）"), style: { padding: "12px", color: "var(--descrip-text,#aaa)", fontSize: "12px" } }));
          }
          for (const dir of d.dirs) {
            const full = curPath ? curPath.replace(/[\\/]$/, "") + "\\" + dir : dir;
            const item = $el("div", { textContent: "📁 " + dir, style: { padding: "7px 12px", cursor: "pointer", fontSize: "13px", borderBottom: "1px solid rgba(0,0,0,.2)" } });
            item.onmouseenter = () => { item.style.background = "rgba(91,140,255,.18)"; };
            item.onmouseleave = () => { item.style.background = ""; };
            item.onclick = () => load(full);
            listEl.appendChild(item);
          }
        } catch (e) {
          pathEl.textContent = t("加载失败: ") + e;
        }
      }

      const pn = $el("div.pn", {}, [
        $el("button.x", { textContent: "✕", onclick: () => m.remove() }),
        bindText($el("h2", { style: { margin: "0 0 10px", fontSize: "15px" } }), "📁 选择目录"),
        pathEl,
        $el("div.btns", { style: { margin: "8px 0" } }, [
          bindText($el("button.asm-btn", { onclick: async () => {
            try {
              const res = await fetch("./asset/browse_dir?path=" + encodeURIComponent(curPath));
              const d = await res.json();
              if (d.ok) load(d.parent || "");
            } catch (e) {}
          } }), "⬆ 上一级"),
        ]),
        listEl,
        $el("div.btns", { style: { marginTop: "12px" } }, [
          bindText($el("button.asm-btn.primary", { onclick: () => { inputEl.value = curPath; m.remove(); } }), "✅ 选择此目录"),
          bindText($el("button.asm-btn", { onclick: () => m.remove() }), "取消"),
        ]),
      ]);
      m.appendChild($el("div.bk", { onclick: () => m.remove() }));
      m.appendChild(pn);
      document.body.appendChild(m);
      await load(curPath);
    }

    // ---------- 下载 / 扫描 ----------
    // ---- 纯前端 ZIP（store 无压缩）----
    const CRC_TABLE = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1); t[n] = c >>> 0; } return t; })();
    function crc32(u8) { let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = CRC_TABLE[(c ^ u8[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
    function dosDateNow() { const n = new Date(); return ((n.getFullYear() - 1980) << 9) | ((n.getMonth() + 1) << 5) | n.getDate(); }
    function dosTimeNow() { const n = new Date(); return (n.getHours() << 11) | (n.getMinutes() << 5) | Math.floor(n.getSeconds() / 2); }
    function u16(v) { return [v & 255, (v >>> 8) & 255]; }
    function u32(v) { return [v & 255, (v >>> 8) & 255, (v >>> 16) & 255, (v >>> 24) & 255]; }
    async function makeZip(entries) {
      // entries: [{path, bytes: Uint8Array}]
      const enc = new TextEncoder();
      const parts = [];
      const central = [];
      let offset = 0;
      const dt = dosDateNow(), tm = dosTimeNow();
      for (const e of entries) {
        const nameB = enc.encode(e.subdir ? e.subdir + "/" + e.path : e.path);
        const data = e.bytes;
        const crc = crc32(data);
        const lh = new Uint8Array(30 + nameB.length);
        lh.set([0x50, 0x4B, 0x03, 0x04], 0);
        // 本地头字段偏移: 10=time 12=date 14=crc 18=csize 22=usize 26=namelen 28=extralen
        lh.set(u16(20), 4);
        lh.set(u16(0x0800), 6);
        lh.set(u16(0), 8);
        lh.set(u16(tm), 10);
        lh.set(u16(dt), 12);
        lh.set(u32(crc), 14);
        lh.set(u32(data.length), 18);
        lh.set(u32(data.length), 22);
        lh.set(u16(nameB.length), 26);
        lh.set(u16(0), 28);
        lh.set(nameB, 30);
        const lhBlob = new Blob([lh, data]);
        central.push({ nameB, crc, size: data.length, offset });
        offset += lhBlob.size;
        parts.push(lhBlob);
      }
      const cdStart = offset;
      for (const c of central) {
        const ch = new Uint8Array(46 + c.nameB.length);
        ch.set([0x50, 0x4B, 0x01, 0x02], 0);
        ch.set(u16(20), 4); ch.set(u16(20), 6); ch.set(u16(0x0800), 8); ch.set(u16(0), 10);
        ch.set(u16(tm), 12); ch.set(u16(dt), 14);
        ch.set(u32(c.crc), 16); ch.set(u32(c.size), 20); ch.set(u32(c.size), 24);
        ch.set(u16(c.nameB.length), 28); ch.set(u16(0), 30); ch.set(u16(0), 32); ch.set(u16(0), 34); ch.set(u16(0), 36);
        ch.set(u32(c.offset), 42);
        ch.set(c.nameB, 46);
        parts.push(new Blob([ch]));
        offset += ch.length; // Uint8Array 只有 length；用 .size 会得 undefined → NaN → EOCD cd_size 写成 0
      }
      const cdSize = offset - cdStart;
      const eocd = new Uint8Array(22);
      eocd.set([0x50, 0x4B, 0x05, 0x06], 0);
      eocd.set(u16(0), 4); eocd.set(u16(0), 6); eocd.set(u16(entries.length), 8); eocd.set(u16(entries.length), 10);
      eocd.set(u32(cdSize), 12); eocd.set(u32(cdStart), 16); eocd.set(u16(0), 20);
      parts.push(new Blob([eocd]));
      return new Blob(parts, { type: "application/zip" });
    }
    function triggerDownload(blob, filename) {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 30000);
    }
    // ---- 本地下载目录 (File System Access API) ----
    let dlDirHandle = null;
    const DL_DB = "am_dl_handle";
    function idbOpen() {
      return new Promise((res, rej) => {
        if (!window.indexedDB) return rej(new Error("no indexedDB"));
        const r = indexedDB.open(DL_DB, 1);
        r.onupgradeneeded = () => r.result.createObjectStore("kv");
        r.onsuccess = () => res(r.result);
        r.onerror = () => rej(r.error);
      });
    }
    async function idbGet(k) {
      const db = await idbOpen();
      return new Promise((res, rej) => {
        const tx = db.transaction("kv", "readonly");
        const q = tx.objectStore("kv").get(k);
        q.onsuccess = () => res(q.result);
        q.onerror = () => rej(q.error);
      });
    }
    async function idbSet(k, v) {
      const db = await idbOpen();
      return new Promise((res, rej) => {
        const tx = db.transaction("kv", "readwrite");
        tx.objectStore("kv").put(v, k);
        tx.oncomplete = () => res();
        tx.onerror = () => rej(tx.error);
      });
    }
    async function loadDlHandle() {
      try {
        const h = await idbGet("dir");
        if (!h || !h.queryPermission) { dlDirHandle = null; return; }
        let st = await h.queryPermission({ mode: "readwrite" });
        if (st !== "granted") {
          try { st = await h.requestPermission({ mode: "readwrite" }); } catch (e) { st = "denied"; }
        }
        dlDirHandle = st === "granted" ? h : null;
      } catch (e) { dlDirHandle = null; }
    }
    async function pickDlDir(inputEl) {
      if (!window.showDirectoryPicker) { statusMsg("当前浏览器不支持直接选择本地目录, 将使用浏览器默认下载目录"); return; }
      try {
        const h = await window.showDirectoryPicker({ mode: "readwrite" });
        dlDirHandle = h;
        try { await idbSet("dir", h); } catch (e) {}
        if (inputEl) inputEl.value = h.name || "";
        statusMsg(LANG === "zh" ? ("✅ 已连接本地目录: " + (h.name || "")) : ("✅ Linked local folder: " + (h.name || "")));
      } catch (e) {
        if (e && (e.name === "AbortError" || e.name === "SecurityError")) return;
        statusMsg(LANG === "zh" ? ("选择目录失败: " + (e && e.message ? e.message : e)) : ("Pick folder failed: " + (e && e.message ? e.message : e)));
      }
    }
    async function saveBlobToLocal(blob, fileName, subdir) {
      // 优先写入已授权的本地目录（File System Access API），否则回退浏览器下载
      if (dlDirHandle && dlDirHandle.getFileHandle) {
        try {
          let dir = dlDirHandle;
          if (subdir && dlDirHandle.getDirectoryHandle) {
            try { dir = await dlDirHandle.getDirectoryHandle(subdir, { create: true }); } catch (e) { dir = dlDirHandle; }
          }
          const fh = await dir.getFileHandle(fileName, { create: true });
          const w = await fh.createWritable();
          await w.write(blob);
          await w.close();
          return "dir";
        } catch (e) { console.warn("AssetManager local dir write failed, fallback to browser download:", e); }
      }
      triggerDownload(blob, fileName);
      return "browser";
    }
    function baseName(p) { const i = Math.max(p.lastIndexOf("/"), p.lastIndexOf("\\")); return i >= 0 ? p.slice(i + 1) : p; }
    function safeName(n) { return String(n || "asset").replace(/[\\/:*?"<>|]/g, "_"); }
    async function fetchAssetBytes(relPath, tries) {
      tries = tries || 3;
      let lastErr = null;
      for (let i = 0; i < tries; i++) {
        try {
          const res = await fetch("./asset/file?p=" + encodeURIComponent(relPath), { cache: "no-store" });
          if (res.status === 404) return null; // 该目录没有此文件, 正常跳过
          if (!res.ok) throw new Error("HTTP " + res.status);
          return new Uint8Array(await res.arrayBuffer());
        } catch (e) {
          lastErr = e;
          if (i < tries - 1) await new Promise((r) => setTimeout(r, 300 * (i + 1)));
        }
      }
      throw lastErr || new Error("fetch failed");
    }
    const RUN_FILE_CANDIDATES = ["workflow.json", "info.json", "prompt.txt"];
    const THUMB_NAME_RE = /^thumb\.(jpe?g|png|webp|gif|bmp)$/i;
    // 缩略图永远不下载（无论开关），主图之外的同名缩略图按 r.thumb / thumb.* 识别
    function isThumbName(fn, run) {
      const base = baseName(fn).toLowerCase();
      const runThumb = String((run && run.thumb) || "").toLowerCase();
      return THUMB_NAME_RE.test(base) || (!!runThumb && base === runThumb);
    }
    async function gatherEntries(list) {
      const cfg = (curConfig && curConfig.config) || {};
      // 默认：只下图片/视频本体、全部平铺（不带 json/txt，缩略图永不下载，不建每张图的文件夹）。
      // 两个开关分别对应「下载包含 json/txt 元数据」「下载保留每张图的文件夹」。
      const includeMeta = cfg.download_include_metadata === true;
      const keepFolders = cfg.download_keep_folders === true;
      const entries = [];
      const used = new Set();
      const failed = [];
      const push = (base, bytes, subdir) => {
        if (!bytes || !bytes.length) return;
        let nm = base, dup = 1;
        const keyOf = (n) => (subdir ? subdir + "/" : "") + n;
        while (used.has(keyOf(nm))) { nm = base.replace(/(\.\w+)?$/, "_" + (dup++) + "$1"); }
        used.add(keyOf(nm));
        entries.push({ path: nm, bytes: bytes, subdir: subdir || "" });
      };
      for (const r of list) {
        const runBase = safeName(r.name);
        const subdir = keepFolders ? runBase : "";
        // 默认只下这一条产物的主图/主视频本体（r.media）。
        // 开启「下载包含 json/txt 元数据」后按 r.files（或已知候选名）抓取，但缩略图始终排除。
        const names = includeMeta
          ? ((Array.isArray(r.files) && r.files.length)
              ? r.files.filter((fn) => !isThumbName(fn, r))
              : [r.media].concat(RUN_FILE_CANDIDATES).filter(Boolean))
          : [r.media].filter(Boolean);
        for (const fn of names) {
          if (!fn) continue;
          const rel = r.dir + "/" + fn;
          try {
            const fileName = keepFolders ? baseName(fn) : runBase + "_" + baseName(fn);
            push(fileName, await fetchAssetBytes(rel), subdir);
          } catch (e) {
            failed.push(rel + "  （" + (e && e.message ? e.message : e) + "）");
          }
        }
        if (includeMeta) {
          try {
            const info = [
              "Name: " + r.name,
              "Time: " + (r.time || ""),
              (r.positive ? "\nPrompt:\n" + r.positive : ""),
              (r.negative ? "\nNegative:\n" + r.negative : ""),
              (r.models && r.models.length ? "\nModels: " + r.models.join(", ") : ""),
              (r.params ? "\nParams: " + Object.keys(r.params).map(k => k + "=" + r.params[k]).join(" · ") : ""),
            ].filter(Boolean).join("\n");
            const infoName = runBase + "_info.txt";
            push(infoName, new TextEncoder().encode(info), subdir);
          } catch (e) {}
        }
      }
      return { entries, failed };
    }
    function dlLabel() { return (curConfig && curConfig.config && curConfig.config.download_mode === "zip") ? t("正在打包下载…") : t("正在保存…"); }
    async function downloadRuns(list) {
      if (!list || !list.length) { statusMsg(t("没有匹配的产物")); return; }
      const cfg = curConfig && curConfig.config;
      let zipMode = !!(cfg && cfg.download_mode === "zip");
      // 「逐个保存」需要本地目录授权：浏览器会拦截连续多次下载。
      // 这里在用户点击后第一时间弹目录选择（保住用户手势），授权成功就不必打包了。
      if (!zipMode && list.length > 1 && !(dlDirHandle && dlDirHandle.getFileHandle)) {
        if (!dlDirHandle) { try { await loadDlHandle(); } catch (e) {} } // 刷新后先尝试恢复已授权目录
      }
      if (!zipMode && list.length > 1 && !(dlDirHandle && dlDirHandle.getFileHandle) && window.showDirectoryPicker) {
        try {
          const h = await window.showDirectoryPicker({ mode: "readwrite" });
          if (h) { dlDirHandle = h; try { await idbSet("dir", h); } catch (e) {} }
        } catch (e) { /* 用户取消/浏览器不允许 → 下面回退为单个 ZIP */ }
      }
      const gathered = await gatherEntries(list);
      await saveEntries(gathered.entries, gathered.failed);
    }
    // v1.2.2: 「下载选中」(文件夹视图) —— 文件夹递归取清单, 文件直接取; 两者共用下面的保存管线
    async function downloadOutputSelection() {
      const rels = [];
      for (const rel of selected) rels.push({ rel: rel, name: dirNameOf(rel), subdir: "" });
      const failed = [];
      if (selFolders.size) {
        statusMsg(t("正在读取文件夹清单…"));
        for (const rel of selFolders) {
          let d = null;
          try { d = await (await fetch("./asset/output_files?path=" + encodeURIComponent(rel))).json(); } catch (e) {}
          if (!d || !d.ok) { failed.push((rel || t("根")) + "（" + terr((d && d.error) || "Directory not found") + "）"); continue; }
          if (d.truncated) {
            statusMsg(t("文件夹文件过多，已中止下载") + ": " + (rel || t("根")) +
              (LANG === "zh" ? ("（超过 5000 个文件，请分批或改用网格视图下载）") : (" (>5000 files; split it or use the grid view)")));
            return;
          }
          for (const f of d.files) rels.push({ rel: f.rel, name: f.name, subdir: rel });
        }
      }
      if (!rels.length) { statusMsg(t("没有选中要下载的内容")); return; }
      const cfg = curConfig && curConfig.config;
      let zipMode = !!(cfg && cfg.download_mode === "zip");
      if (!zipMode && rels.length > 1 && !(dlDirHandle && dlDirHandle.getFileHandle)) {
        if (!dlDirHandle) { try { await loadDlHandle(); } catch (e) {} }
      }
      if (!zipMode && rels.length > 1 && !(dlDirHandle && dlDirHandle.getFileHandle) && window.showDirectoryPicker) {
        try {
          const h = await window.showDirectoryPicker({ mode: "readwrite" });
          if (h) { dlDirHandle = h; try { await idbSet("dir", h); } catch (e) {} }
        } catch (e) { /* 回退 ZIP */ }
      }
      const keepFolders = !!(cfg && cfg.download_keep_folders === true);
      const entries = [];
      const used = new Set();
      statusMsg(t("正在下载 N 个文件").replace("N", String(rels.length)) + (LANG === "zh" ? "…" : "…"));
      for (const it of rels) {
        try {
          const res = await fetch("./asset/output_file?p=" + encodeURIComponent(it.rel), { cache: "no-store" });
          if (res.status === 404) { failed.push(it.rel + "  (404)"); continue; }
          if (!res.ok) throw new Error("HTTP " + res.status);
          const bytes = new Uint8Array(await res.arrayBuffer());
          const subdir = keepFolders ? (it.subdir || "") : "";
          let nm = safeName(it.name), dup = 1;
          const keyOf = (n) => (subdir ? subdir + "/" : "") + n;
          while (used.has(keyOf(nm))) { nm = safeName(it.name).replace(/(\.\w+)?$/, "_" + (dup++) + "$1"); }
          used.add(keyOf(nm));
          entries.push({ path: nm, bytes: bytes, subdir: subdir });
        } catch (e) {
          failed.push(it.rel + "  （" + (e && e.message ? e.message : e) + "）");
        }
      }
      if (!entries.length) { statusMsg(t("没有选中要下载的内容")); return; }
      await saveEntries(entries, failed);
    }
    // 把 entries 落到本地(ZIP 或逐个保存) —— downloadRuns 与 downloadOutputSelection 共用
    async function saveEntries(entries, failed) {
      failed = failed || [];
      if (!entries.length) { statusMsg(t("该资产下载失败")); return; }
      if (failed.length) {
        entries.push({ path: "_download_errors.txt", bytes: new TextEncoder().encode("以下文件未能下载，未包含在内：\n\n" + failed.join("\n") + "\n") });
      }
      // 浏览器会拦截"连续多次自动下载"（只放行第一个），没授权本地目录时裸模式必然丢文件 → 强制单包 ZIP
      const canWriteDir = !!(dlDirHandle && dlDirHandle.getFileHandle);
      let zipMode = !!(curConfig && curConfig.config && curConfig.config.download_mode === "zip");
      let forcedZip = false;
      if (!zipMode && !canWriteDir) { zipMode = true; forcedZip = true; }
      const fileCount = entries.length - (failed.length ? 1 : 0);
      statusMsg(zipMode ? (dlLabel() + fileCount + (LANG === "zh" ? " 个文件, 保存到本地浏览器下载目录" : " files")) : (dlLabel() + fileCount + (LANG === "zh" ? " 个文件" : " files")));
      if (zipMode) {
        const blob = await makeZip(entries);
        const zipName = "comfyui_assets_" + new Date().toISOString().slice(0, 10) + ".zip";
        const mode = await saveBlobToLocal(blob, zipName);
        const warn = failed.length ? (LANG === "zh" ? ("（另有 " + failed.length + " 个失败，见包内 _download_errors.txt）") : (" (" + failed.length + " failed, see _download_errors.txt)")) : "";
        if (mode === "dir" && dlDirHandle && dlDirHandle.name) {
          statusMsg(LANG === "zh" ? ("✅ 已保存 " + fileCount + " 个文件到本地目录: " + dlDirHandle.name + warn) : ("✅ Saved " + fileCount + " files to local folder: " + dlDirHandle.name + warn));
        } else if (forcedZip) {
          statusMsg(LANG === "zh" ? ("⚠ 浏览器拦截连续多次下载，已自动改为单个 ZIP（" + fileCount + " 个文件）" + warn) : ("⚠ Browser blocks repeated downloads; saved one ZIP (" + fileCount + " files)" + warn));
        } else {
          statusMsg((LANG === "zh" ? ("✅ 已开始下载: " + fileCount + " 个文件, 保存到本地浏览器下载目录") : ("✅ Download started: " + fileCount + " files, saved to the browser download folder")) + warn);
        }
      } else {
        let ok = 0, lastMode = "browser";
        const saveFailed = [];
        for (const e of entries) {
          if (e.path === "_download_errors.txt") continue;
          try {
            const mode = await saveBlobToLocal(new Blob([e.bytes]), e.path, e.subdir);
            if (mode === "dir") lastMode = "dir";
            ok++;
          } catch (err) { saveFailed.push(e.path); console.error("AssetManager save failed:", e.path, err); }
          await new Promise((r) => setTimeout(r, 60)); // 给文件系统/浏览器一点喘息
        }
        const dest = (lastMode === "dir" && dlDirHandle && dlDirHandle.name)
          ? (LANG === "zh" ? ("本地目录: " + dlDirHandle.name) : ("local folder: " + dlDirHandle.name))
          : t("（浏览器下载目录）");
        const total = fileCount;
        const bad = entries.length - fileCount + saveFailed.length;
        if (bad === 0) {
          statusMsg(t("✅ 已保存 ") + ok + (LANG === "zh" ? " 个文件到" : " files to ") + dest);
        } else {
          statusMsg(LANG === "zh" ? ("⚠️ 已保存 " + ok + "/" + total + " 个文件到 " + dest + "，失败 " + bad + " 个") : ("⚠️ Saved " + ok + "/" + total + " files to " + dest + ", " + bad + " failed"));
        }
      }
    }
    async function confirmDownload() {
      const list = filtered(runs);
      if (!list.length) { statusMsg(t("没有匹配的产物")); return; }
      const zipMode = !!(curConfig && curConfig.config && curConfig.config.download_mode === "zip");
      const dlCfg = (curConfig && curConfig.config) || {};
      const includeMeta = dlCfg.download_include_metadata === true;
      const keepFolders = dlCfg.download_keep_folders === true;
      const what = includeMeta
        ? t("• 当前列表中的图片/视频 + json/txt 元数据")
        : t("• 当前列表中的图片/视频（不含 json/txt/缩略图）");
      const layout = (keepFolders ? t("，每张图一个文件夹") : t("，全部平铺在同一目录")) + (zipMode ? t("，打包为单个 ZIP") : t("，逐个原样保存"));
      const m = $el("div.asm-modal");
      m.style.display = "flex";
      const pn = $el("div.pn", {}, [
        $el("button.x", { textContent: "✕", onclick: () => m.remove() }),
        bindText($el("h2", { style: { margin: "0 0 12px", fontSize: "15px" } }), "⬇ 下载确认"),
        bindText($el("div", { style: { fontSize: "13px", marginBottom: "6px" } }), zipMode ? "将打包下载以下内容:" : "将逐个保存以下文件:"),
        $el("div", { style: { fontSize: "13px", color: "var(--descrip-text,#aaa)", marginBottom: "12px", lineHeight: "1.8" } }, [
          document.createTextNode(what + layout),
        ]),
        bindText($el("div", { style: { fontSize: "13px", marginBottom: "14px", wordBreak: "break-all" } }), t("下载数量: ") + list.length),
        $el("div.btns", {}, [
          bindText($el("button.asm-btn.primary", { onclick: () => { m.remove(); downloadRuns(list); } }), "确定下载"),
          bindText($el("button.asm-btn", { onclick: () => m.remove() }), "取消"),
        ]),
      ]);
      m.appendChild($el("div.bk", { onclick: () => m.remove() }));
      m.appendChild(pn);
      document.body.appendChild(m);
    }
    async function downloadSelected() {
      if (!selected.size) return;
      const set = new Set(selected);
      const list = runs.filter(r => set.has(r.dir));
      await downloadRuns(list);
    }
    async function doScan() {
      statusMsg(t("扫描中…"));
      const res = await fetch("./asset/scan", { method: "POST" });
      const d = await res.json();
      statusMsg(d.ok ? (LANG === "zh" ? ("扫描完成, 新增 " + d.new + " 条") : ("Scan done, " + d.new + " new")) : t("扫描失败"));
      await loadRuns(); refresh();
    }

    // ---------- v1.2.9 归档库体检(只读, 零删除) ----------
    function fmtBytes(n) {
      if (!n && n !== 0) return "—";
      if (n < 1024) return n + " B";
      if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
      if (n < 1024 * 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + " MB";
      return (n / (1024 * 1024 * 1024)).toFixed(2) + " GB";
    }
    const AUDIT_REASON_LABELS = {
      "media-missing": "媒体缺失",
      "media-zero-byte": "媒体 0 字节",
      "unplayable-container": "容器不可播放",
      "output-missing": "output 文件已不存在",
    };
    function auditSection(title, count, rows) {
      const head = $el("h3", { style: { margin: "14px 0 6px", fontSize: "13px" } });
      head.textContent = title + (count ? "（" + count + "）" : "（0）");
      const box = $el("div", { style: { fontSize: "12px", lineHeight: "1.7", maxHeight: "180px", overflow: "auto",
        background: "var(--comfy-input-bg,#222)", borderRadius: "6px", padding: "8px 10px" } });
      if (!count) {
        box.textContent = t("（无）");
        return [head, box];
      }
      for (const r of rows) box.appendChild(r);
      return [head, box];
    }
    async function openAudit() {
      statusMsg(t("体检中…"));
      let d;
      try {
        const res = await fetch("./asset/audit", { cache: "no-store" });
        d = await res.json();
      } catch (e) { d = { ok: false, error: e && e.message }; }
      if (!d || !d.ok) { statusMsg(t("体检失败") + " " + terr(d && d.error)); return; }
      statusMsg(t("归档库体检"));
      if (pv) closePreview();
      const m = $el("div.asm-modal");
      m.style.display = "flex";
      const pn = $el("div.pn", { style: { maxHeight: "86vh", overflow: "auto", width: "min(760px, 92vw)" } });
      const ttl = bindText($el("h2", { style: { margin: "0 0 6px", fontSize: "15px" } }), "归档库体检");
      const tot = $el("div", { style: { fontSize: "12px", color: "var(--descrip-text,#aaa)" } });
      tot.textContent = LANG === "zh"
        ? ("共 " + (d.totals.runs || 0) + " 个条目, " + t("占用") + " " + fmtBytes(d.totals.bytes || 0))
        : ((d.totals.runs || 0) + " " + t("条目") + ", " + t("占用") + " " + fmtBytes(d.totals.bytes || 0));
      pn.appendChild(ttl);
      pn.appendChild(tot);

      // 1) 重复来源
      pn.appendChild(...auditSection(t("重复来源"), (d.dup_source || []).length,
        (d.dup_source || []).map((g) => $el("div", { textContent:
          g.source_rel + "  ×" + g.count + "  " + fmtBytes(g.bytes) +
          "  " + t("最早") + " " + (g.oldest || "—") + " / " + t("最新") + " " + (g.newest || "—") +
          "\n　" + g.dirs.join(" | ") }))));
      // 2) 不可预览
      pn.appendChild(...auditSection(t("不可预览条目"), (d.unplayable || []).length,
        (d.unplayable || []).map((u) => $el("div", { textContent:
          u.dir + "  [" + t(AUDIT_REASON_LABELS[u.reason] || u.reason) + "]  " + (u.media || "") }))));
      // 3) 孤儿
      pn.appendChild(...auditSection(t("孤儿条目"), (d.orphans || []).length,
        (d.orphans || []).map((o) => $el("div", { textContent:
          o.dir + "  →  " + o.source_rel + "  [" + t(AUDIT_REASON_LABELS[o.reason] || o.reason) + "]" }))));
      // 4) 同内容
      pn.appendChild(...auditSection(t("同内容疑似重复"), (d.same_content || []).length,
        (d.same_content || []).map((g) => $el("div", { textContent:
          fmtBytes(g.size) + "  hash64k " + String(g.hash64k || "").slice(0, 16) +
          "  ×" + g.dirs.length + "  " + fmtBytes(g.bytes) +
          "\n　" + g.dirs.join(" | ") }))));
      pn.appendChild(bindText($el("div", { style: { fontSize: "11px", color: "var(--descrip-text,#999)", marginTop: "12px" } }),
        "体检只读不改任何文件; 删除属后续版本。"));
      pn.appendChild($el("div.btns", { style: { marginTop: "10px" } }, [
        bindText($el("button.asm-btn", { onclick: () => m.remove() }), "关闭"),
      ]));
      m.appendChild($el("div.bk", { onclick: () => m.remove() }));
      m.appendChild(pn);
      document.body.appendChild(m);
    }

    function statusMsg(s) { status.textContent = s; }

    // ---------- 打开/关闭 ----------
    async function loadRuns() {
      const res = await fetch("./asset/list");
      const d = await res.json();
      if (d.ok) { runs = d.runs || []; rebuildByDate(); }
      try { curConfig = await (await fetch("./asset/config")).json(); } catch (e) {}
      // v1.2.4: 把插件版本显示在标题旁(拿不到就留空, 不影响其它功能)
      try { if (curConfig && curConfig.version) verEl.textContent = "v" + curConfig.version; } catch (e) {}
    }
    async function openPanel() {
      detectLang();
      relabel();
      overlay.style.display = "flex";
      statusMsg(t("加载中…"));
      fixLinkRenderMode();
      await loadRuns();
      if (runs.length) {
        const d = runs[0].date;
        calYear = Number(d.slice(0, 4)); calMonth = Number(d.slice(5, 7)) - 1; selDate = d;
      }
      refresh();
      if (view === "folder") { await loadFolderTree(); await loadFolder(folderPath); }
      statusMsg(t("共 ") + runs.length + t(" 条资产"));
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(pollRefresh, 8000);
    }
    function closePanel() {
      closePreview();
      overlay.style.display = "none";
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }
    function checkLang() {
      const prev = LANG;
      detectLang();
      if (LANG !== prev) {
        relabel();
        if (overlay.style.display === "flex") refresh();
      }
    }
    async function pollRefresh() {
      checkLang();
      try {
        const res = await fetch("./asset/list");
        const d = await res.json();
        if (d.ok) {
          const newDirs = new Set((d.runs || []).map(r => r.dir));
          const oldDirs = new Set(runs.map(r => r.dir));
          const changed = newDirs.size !== oldDirs.size || [...newDirs].some(x => !oldDirs.has(x));
          if (changed) {
            runs = d.runs || [];
            rebuildByDate();
            // 清除已不存在的选中项
            for (const s of [...selected]) if (!newDirs.has(s)) selected.delete(s);
            refresh();
            statusMsg(t("已自动更新: 共 ") + runs.length + t(" 条资产"));
            await autoDownloadNew(newDirs, d.runs || []);
          }
        }
      } catch (e) {}
      // 文件夹视图: 轻量刷新当前目录 + 文件夹树(不打断进行中的多选, 只清掉已不存在的选中项)
      if (overlay.style.display === "flex" && view === "folder") { await pollFolder(); await pollFolderTree(); }
    }
    async function pollFolder() {
      try {
        const res = await fetch("./asset/list_output?path=" + encodeURIComponent(folderPath));
        const d = await res.json();
        if (!d.ok) return;
        const nFile = (d.files || []).length;
        const oFile = (folderData.files || []).length;
        if ((d.path || "") !== folderPath || nFile !== oFile) {
          folderPath = d.path || folderPath;
          folderData = d;
          // 选中集合只存右栏文件 rel → 已不存在的清掉
          const live = new Set((d.files || []).map((x) => x.rel));
          for (const s of [...selected]) if (!live.has(s)) selected.delete(s);
          renderFolder();
          updateBatchBtn();
          updateFolderBtns();
        }
      } catch (e) {}
    }
    async function pollFolderTree() {
      try {
        const res = await fetch("./asset/folder_tree");
        const d = await res.json();
        if (!d.ok) return;
        if (treeSig(buildFlatTree(d.nodes || [], [])) !== treeSig(flatTree)) {
          folderTree = d;
          renderTree();
        }
      } catch (e) {}
    }

    // ---------- 自动下载新产物 ----------
    async function autoDownloadNew(newDirs, allRuns) {
      try {
        const cfg = curConfig && curConfig.config;
        if (!cfg || cfg.auto_download !== true) return;
        let done = [];
        try { done = JSON.parse(localStorage.getItem("am_auto_dl_done") || "[]"); } catch (e) {}
        const doneSet = new Set(Array.isArray(done) ? done : []);
        const fresh = (allRuns || []).filter(r => newDirs.has(r.dir) && !doneSet.has(r.dir));
        if (!fresh.length) return;
        for (const r of fresh) doneSet.add(r.dir);
        localStorage.setItem("am_auto_dl_done", JSON.stringify([...doneSet]));
        statusMsg(t("自动下载已启用: 新产物将自动保存到浏览器下载目录"));
        await downloadRuns(fresh);
      } catch (e) { console.error("AssetManager auto-download failed:", e); }
    }

    q.addEventListener("input", refresh);

    // ---------- 入口 ----------
    // 菜单栏按钮(图标用 archive 以区分「显示图像流」)
    try {
      const btn = new ComfyButton({
        icon: "archive",
        content: t("资产管理"),
        tooltip: t("浏览/搜索/删除产物, 切换输出目录, 下载"),
        action: () => openPanel(),
      });
      if (app.menu && app.menu.settingsGroup) app.menu.settingsGroup.append(btn);
      relabelers.push(() => {
        try {
          const span = btn.element && btn.element.querySelector("span");
          if (span) span.textContent = t("资产管理");
          if (btn.element) btn.element.title = t("浏览/搜索/删除产物, 切换输出目录, 下载");
        } catch (e) {}
      });
    } catch (e) {
      console.error("AssetManager 菜单按钮注册失败:", e);
    }

    // 全局语言轮询: 始终跟随 ComfyUI 语言(含菜单按钮), 无需面板打开
    setInterval(checkLang, 1000);
  },
});