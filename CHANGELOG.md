# Changelog

All notable changes to **ComfyUI-AssetManager** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> 本文件记录 **ComfyUI-AssetManager** 的所有重要改动，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.3.2] - 2026-11-11

### Added · 新增

- **Download progress with cancel.** The `下载文件` button (both previews) now streams the file and shows a live percentage progress bar in the status line, with a `取消` button that aborts mid-transfer ("已取消下载", not an error). Small files without length headers fall back to the old whole-blob path. Backend is unchanged — aiohttp's FileResponse was already streaming with `Content-Length`; progress is computed in the browser from the response stream.<br>
  **下载进度与取消。** 两个预览的「下载文件」按钮现在流式下载并在状态栏显示实时百分比进度条，带「取消」按钮可中途中止（状态栏显示"已取消下载"，不算失败）。无长度头的小文件自动退回整段下载。后端零改动——aiohttp 的 FileResponse 本就是流式带 `Content-Length`，百分比在浏览器侧从响应流计算。

## [1.3.1] - 2026-11-11

### Added · 新增

- **Archive status at a glance + one-click repair.** Folder-view cards show a `未归档` badge for files that have never been archived (archived files show nothing — no noise). The scan button's status line now summarizes: `新增 N 条, 跳过 M 残留, K 条归档失效`. A new no-icon `修复` button runs a safe repair pass: it **relinks** archive entries whose source file was renamed/moved (byte-size match against unclaimed output files, rewriting `source_rel` and migrating the state key), **rebuilds** a missing `info.json` from the media file itself (marked `orphan`/`rebuilt`), and **marks** orphaned entries with an `orphan` flag — **it never deletes anything**.<br>
  **归档状态一眼可见 + 一键修复。** 文件夹视图卡片为从未归档的文件显示 `未归档` 角标（已归档不显示，常态不噪）。扫描按钮的状态栏现在汇总：`新增 N 条, 跳过 M 残留, K 条归档失效`。新增无图标「修复」按钮执行安全修复：**对齐**（源文件被改名/移动后，按字节匹配未占用文件改写 `source_rel` 并迁移状态键）、**重建**（条目缺 `info.json` 时从媒体文件重建并标 `orphan`/`rebuilt`）、**标孤立**（`source_rel` 落空的条目写 `orphan` 标记）——**不删任何文件**。

## [1.3.0] - 2026-11-11

### Added · 新增

- **Trash view — deleting is now reversible.** All three delete paths (grid/calendar preview "delete from disk", folder-view file delete, folder-view folder delete) now move things into a trash folder under the archive library (`_trash/<timestamp>_<n>/`, with a manifest recording original paths) instead of wiping them. A new `回收站` button opens the trash view: every batch shows its time, kind, item count and disk usage, with `恢复` (restore to the original location) and `彻底删除` (permanent delete, confirmed) per batch, plus `清空回收站` for everything (double-confirmed). Deleting an asset still takes both its archive copy and the original output file — but now into the same batch, so restoring puts both back.<br>
  **回收站 —— 删除从此可回滚。** 三条删除路径（网格/日历预览「从硬盘删除」、文件夹视图删文件、删文件夹）统一改为移入归档库下的回收站（`_trash/<时间戳>_<序号>/`，manifest 记录原始路径）。新增「回收站」按钮：每批显示时间/类型/件数/占用，可整批「恢复」（回原位）或「彻底删除」（二次确认），顶部「清空回收站」二次确认全清。删资产仍会同时移走归档副本与 output 原始文件——但进同一批次，恢复时一起回来。
- Deleting no longer claims "cannot be undone": confirmation dialogs now say the items go to the trash and can be restored from there. Legacy callers that omit the archive directory keep the old direct-delete behavior (backwards compatible).<br>
  删除确认框不再说"无法恢复"，改为"移入回收站，可在回收站恢复"。未传归档目录的旧调用保持原直接删除语义（向后兼容）。

## [1.2.9] - 2026-11-11

### Added · 新增

- **Archive audit — a read-only health check for your library.** A new `体检` button in the toolbar scans every archive entry (including ones hidden by earlier releases) and reports four kinds of bookkeeping debt: duplicate `source_rel` groups (with counts, disk usage, oldest/newest), non-previewable entries (media missing / 0-byte / unplayable container), orphaned entries (the source file in output no longer exists), and same-content suspects (same size + identical first 64 KB hash). Each section shows what it found and how much disk it occupies; the dialog has **no delete buttons** — cleanup comes in a later release after you review the list.<br>
  **归档库体检 —— 只读的资产库健康检查。** 工具栏新增「体检」按钮，扫描**全部**归档条目（含此前被隐藏的），分四类报告坏账：重复 `source_rel` 组（份数/占用/最早最新）、不可预览条目（媒体缺失 / 0 字节 / 容器不可播放）、孤儿条目（output 源文件已不存在）、同内容疑似重复（同大小 + 前 64KB 哈希一致）。每节列出发现与占用；弹窗**没有任何删除按钮**——等你过目清单后，清理属后续版本。

## [1.2.8] - 2026-11-11

### Changed · 改动

- **The archive no longer writes a `workflow.json` file per entry.** The workflow is already embedded in every PNG/MP4 (verified on real data: the embedded metadata and the archived `workflow.json` compared key-by-key and matched), so the loose file added nothing — and its filename made pairing awkward. Existing entries keep their `workflow.json` on disk untouched; new entries simply don't get one. Nothing is lost: the full workflow stays inside each entry's `info.json` (`workflow_json`) and the PNG/MP4 itself.<br>
  **归档不再为每个条目写 `workflow.json` 散落文件。** 工作流本就内嵌在每个 PNG/MP4 里（真机对拍：内嵌元数据与归档 `workflow.json` 逐键一致），散落文件没有增量价值、文件名还难以配对。存量条目的 `workflow.json` 原样保留；新条目不再生成。数据不丢：完整工作流仍保存在每条的 `info.json`（`workflow_json` 字段）与 PNG/MP4 本体里。
- **The previews gain a `保存 workflow.json` button.** Grid/calendar and folder previews can now reassemble and download the workflow from the entry's `info.json` on demand, named `<媒体名>.workflow.json` so it always pairs with its asset (disabled for files that were never archived). This is the replacement for the loose file — the UI never offers a raw scattered `workflow.json`, but the workflow is always one click away.<br>
  **两个预览弹窗新增「保存 workflow.json」按钮。** 网格/日历与文件夹视图的预览可随时从归档 `info.json` 重组下载工作流，文件名为 `<媒体名>.workflow.json`、永远和资产配对（未归档的文件该按钮置灰）。这就是散落文件的替代品——界面不再提供散落的 `workflow.json`，但工作流永远一键可取。

## [1.2.7] - 2026-11-11

### Fixed · 修复

- **Half-written files no longer pollute the library.** Partial-download suffixes (`.part` / `.tmp` / `.crdownload` / `.download`) are skipped by the scanner and hidden from every list, the folder tree and folder downloads. 0-byte media files (a generation that died mid-write) are likewise never archived, never listed, not counted in the folder tree and excluded from folder downloads. Once the file exists with real content, the next scan admits it normally.<br>
  **写一半的文件不再污染资产库。** 半成品后缀（`.part` / `.tmp` / `.crdownload` / `.download`）被扫描器跳过、不出现在任何列表/左栏树/文件夹下载里；0 字节媒体文件（写一半崩掉的残留）同样不归档、不显示、不计入树的文件数、不参与下载。等文件有了真实内容，下一次扫描自然入库。
- **Broken archive entries no longer show up as un-previewable cards.** Runs whose media file was deleted from the archive, or whose media copy is 0 bytes, are hidden from the grid and calendar views (the entry stays on disk, untouched).<br>
  **坏掉的归档条目不再以无法预览的卡片出现。** 归档条目的媒体文件已被删除、或媒体副本是 0 字节时，网格/日历不再显示该条目（条目数据保留在盘上，不动）。

### Changed · 改动

- **Files without a preview (📄 "other") no longer open an empty preview dialog.** Clicking one in the folder view shows a status hint instead ("该文件不支持预览，可用「下载文件」保存"), and the folder-view paging sequence (`←` / `→`) now contains only previewable media; the "filter leaves 1 item" paging fallback still ignores the filter but only counts previewable media.<br>
  **无预览能力的文件（📄「其他」类）不再弹出空预览窗。** 在文件夹视图点它只给状态提示（"该文件不支持预览，可用「下载文件」保存"）；文件夹视图预览的翻页序列（`←` / `→`）只含可预览媒体；"筛选后剩 1 项"的翻页回退照旧忽略筛选，但只统计可预览媒体。

## [1.2.6] - 2026-11-11

### Fixed · 修复

- **Animated `.gif` outputs are now previewable.** `.gif` was classified as a video, so it was handed to a `<video>` element — which browsers refuse to play, showing a black box instead of the animation. GIFs are now rendered as images everywhere (cards and previews in all views).<br>
  **`.gif` 产物现在可以预览了。** `.gif` 此前被归为视频，被塞进 `<video>` 元素——浏览器直接拒绝播放，只显示黑框。现在所有视图（卡片与大图预览）都按图片渲染动图。
- **Videos the browser cannot play no longer show up as unplayable black boxes.** Non-browser containers like `.mkv` are now excluded from every list, the folder tree, folder downloads and the grid/calendar views (the files themselves are still archived — just not shown). And if a video still fails to load in the preview (e.g. HEVC), the dialog now shows a clear "the browser cannot play this video" panel with the filename instead of a black screen.<br>
  **浏览器放不出来的视频不再以黑框形式出现。** `.mkv` 这类非浏览器容器已从所有列表、左栏树、整文件夹下载与网格/日历视图中排除（文件本体仍会归档，只是不展示）；若预览里仍有视频加载失败（如 HEVC），弹窗会明确显示"浏览器无法播放该视频"和文件名，而不是黑屏。

### Changed · 改动

- **The preview's `下载 workflow.json` button is now `下载文件`.** It downloads the file itself — the original output file in the folder view, the archived media copy in the grid/calendar views — for videos, images and everything else. (The `workflow.json` file is still kept in the archive on disk; the UI no longer offers a button for it.)<br>
  **预览里的 `下载 workflow.json` 按钮改为 `下载文件`。** 它下载文件本体——文件夹视图里是 output 的原始文件，网格/日历里是归档库中的媒体副本——视频、图片、其他文件都可以。（`workflow.json` 仍保留在归档库磁盘上，只是界面不再提供该按钮。）

## [1.2.5] - 2026-11-07

### Fixed · 修复

- **Preview thumbnails and archive/backup files no longer show up as browsable assets.** Every archive entry carries `thumb.jpg` / `info.json` / `prompt.txt` / `workflow.json`; the folder view used to list those as if they were your images and let you open them. They are now excluded from the folder list, the folder tree, folder downloads and the asset scan.
  **预览用缩略图与归档/备份文件不再作为资产出现。** 每个归档条目都带 `thumb.jpg` / `info.json` / `prompt.txt` / `workflow.json`；文件夹视图以前会把它们当成你的图片列出来、还能点开。现在这些文件已从文件夹列表、左栏树、整文件夹下载与扫描中排除。

- **The archive and backup directories are never browsed or scanned.** If `archive_dir` or `backup_dir` lives inside the output directory, they used to appear as ordinary folders (so you could walk into the library and see its internals), and — worse — the scanner **re-archived the archive itself**: in a reproduction, one scan produced six bogus entries (including a `thumb.jpg` "asset") and kept chaining. Those roots are now hidden entirely and skipped by the scanner.
  **归档目录与备份目录不再被浏览或扫描。** 当 `archive_dir` / `backup_dir` 落在输出目录内时，它们以前会作为普通文件夹出现（于是你能走进库里看到它的内部文件），更糟的是扫描器会**把归档库自己再归档一遍**：复现中一次扫描产生了 6 条假条目（其中一条是 `thumb.jpg`"资产"）并持续连锁。现在这两个根目录被整体隐藏、扫描也跳过。

- **Legacy bogus entries are hidden (not deleted).** Library entries already created by that self-archiving bug — ones whose `media` is a preview thumbnail or whose `source_rel` points inside the archive — are filtered out of every view. **No file is removed from disk**, so nothing is lost if you want to inspect them manually.
  **历史遗留的假条目只隐藏、不删除。** 那个自噬缺陷已经产生的条目（`media` 是预览缩略图、或 `source_rel` 指向归档库内部）会从所有视图里过滤掉，**磁盘上一个文件都不删**，想人工检查随时能看到。

### Notes · 说明

- The rules are deliberately narrow: only the plugin's own fixed filenames (`thumb.<image ext>`, `info.json`, `prompt.txt`, `workflow.json`, `archive_state.json`, `open_state.json`, `ComfyUI_asset_backup_*.zip`) are treated as artifacts. A normal file such as `my_thumb.jpg` or `thumbnail.png` is still listed as your asset.
  规则刻意收窄：只有插件自己的固定文件名（`thumb.<图片扩展名>`、`info.json`、`prompt.txt`、`workflow.json`、`archive_state.json`、`open_state.json`、`ComfyUI_asset_backup_*.zip`）被当作产物。`my_thumb.jpg`、`thumbnail.png` 这类正常文件仍作为你的资产列出。
- Edge case: if `archive_dir` **is** the output directory itself, scanning is skipped entirely (it would otherwise archive itself forever); if `backup_dir` is the output directory, only the backup zips are hidden and browsing still works.
  边界：若 `archive_dir` **就是**输出目录本身，扫描会被直接跳过（否则会永久自我归档）；若 `backup_dir` 就是输出目录，只隐藏备份 zip，浏览仍正常。

## [1.2.4] - 2026-11-03

### Added · 新增

- **The running version is now shown in the panel.** Next to the panel title you'll see `v1.2.4`, so after a `git pull` + hard refresh you can tell at a glance whether the browser has picked up the new build (the `version` field is served by `GET /asset/config`).<br>
  **面板标题旁现在显示运行版本。** 标题右侧会显示 `v1.2.4`，`git pull` + 硬刷新之后一眼就能确认浏览器是否已经加载新版本（`GET /asset/config` 响应里新增 `version` 字段）。

### Fixed · 修复

- **Folder-view paging arrows no longer vanish when a filter leaves a single item.** Paging normally follows the list you're looking at (same as the grid and calendar views). But if the search box or the image/video filter narrowed the folder down to one item while the folder actually holds more, the left/right arrows were hidden — the folder view now falls back to the **whole folder's file list** for paging in exactly that case.<br>
  **筛选后只剩一张时，文件夹视图的翻页箭头不再消失。** 翻页正常遵循"你正在看的那一批"（与网格/日历一致）；但如果搜索框或图片/视频筛选把文件夹收窄到只剩一项、而文件夹里其实还有别的，左右箭头就会被隐藏——现在遇到这种情况会改用**整个文件夹的文件列表**来翻页。
  > 说明：`←`/`→` 箭头自 **1.2.2** 起就已存在于文件夹视图的大图预览（`1.2.1` 确实没有）；若你在界面上看不到，请先确认标题旁的版本号并 Ctrl+F5 硬刷新。<br>
  > Note: the `←`/`→` arrows have existed in the folder view's preview since **1.2.2** (they were genuinely missing in 1.2.1); if you don't see them, check the version next to the title and hard-refresh with Ctrl+F5.

## [1.2.3] - 2026-11-03

### Fixed · 修复

- **The folder tree no longer jumps up and down.** The breadcrumb row used to be hidden entirely while you were at the root, so clicking `根` / any folder made the whole tree shift by about 30px. That row now keeps a fixed height and stays in place, so the tree stays put.<br>
  **文件夹树不再上下跳动。** 以前在根目录时面包屑整行被隐藏，于是点 `根` 或点文件夹都会让整棵树挪动约 30px。现在该行保留固定高度、始终占位，树不再移动。
- **Folder view: files now have the same buttons as the other views.** The large preview in the folder view previously offered only `关闭`; it now has the same `复制提示词` / `下载 workflow.json` / `🗑 从硬盘删除` as the grid and calendar previews (plus the existing `←` / `→` paging). Files that were never archived have the prompt / workflow buttons greyed out, and the delete confirmation says when the archive copy will be removed too.<br>
  **文件夹视图里的文件现在和其他视图有相同的按钮。** 文件夹视图的大图预览以前只有 `关闭`；现在与网格/日历预览一样有 `复制提示词` / `下载 workflow.json` / `🗑 从硬盘删除`（外加原有的 `←` / `→` 翻页）。从未归档过的文件，提示词与 workflow 两个按钮置灰；删除确认框会说明是否会连带删掉归档副本。

### Changed · 改动

- **Left panel buttons regrouped into two rows.** Row 1 is folder actions (`新建` / `改名` / `删除` / `刷新`) and row 2 is selection actions (`多选` / `剪切` / `粘贴` / `下载`); the duplicated `多选` is no longer shown in the top toolbar while the folder view is active, so no action appears twice.<br>
  **左栏按钮重新分两行。** 行1 是文件夹操作（`新建` / `改名` / `删除` / `刷新`），行2 是选中项操作（`多选` / `剪切` / `粘贴` / `下载`）；文件夹视图下顶部工具栏不再显示重复的 `多选`，同一个功能不会出现两次。

### Added · 新增

- New route `POST /asset/delete_output_file` deletes a single file from the output directory, removing its archive entry too when it has one (same behaviour as deleting an asset from the grid), so both views agree on what deleting means.<br>
  新增路由 `POST /asset/delete_output_file`，删除输出目录里的单个文件；若它有归档条目则一并删除（与在网格里删除资产的行为一致），两个视图对"删除"的语义保持统一。

## [1.2.2] - 2026-11-03

### Changed · 改动

- **Independent scrolling · 滚动独立** — in the folder and calendar views the left panel and the right image area now scroll **independently**; the tree / calendar no longer drags the images along with it.<br>
  **滚动独立** —— 文件夹视图与日历视图里，左栏与右侧图片区**各自独立滚动**；翻树 / 看日历不再把图片一起带走。
- **Folder view polish · 文件夹视图细节** — the `output 根` caption at the top of the left panel is gone, and a `根` (Root) row now sits at the top of the folder tree; long folder names **wrap** instead of being cut off with an ellipsis.<br>
  去掉左栏顶部的 `output 根` 说明，改在文件夹树顶加一行 `根`；文件夹名过长**自动换行**，不再用省略号截断。
- **Folder preview paging · 文件夹视图翻页** — previewing an image in the folder view now supports `←` / `→` paging (wraps around, shows `n / total`, preloads neighbours), matching the grid and calendar views.<br>
  在文件夹视图里预览图片现在支持 `←` / `→` 翻页（循环、`n / 总数`、相邻预加载），与网格 / 日历视图一致。
- **Folder multi-select with visible ticks · 多选文件夹且勾选可见** — one multi-select mode whose selection type is **mutually exclusive** (files vs folders), with a visible `✓` on tree rows. `剪切` / `粘贴` are file-only, `下载` works for either type, and `删除` removes the ticked folders (one combined confirmation listing each file count) or the current folder when nothing is ticked.<br>
  **多选文件夹且勾选可见** —— 一套多选模式，文件与文件夹选中**互斥**，树行显示可见的 `✓`；`剪切` / `粘贴` 只对文件，`下载` 两者都行，`删除` 删掉勾选的文件夹（一次性确认框列出各自文件数），没勾选时删当前文件夹。
- **Download whole folders · 下载整个文件夹** — tick folders and press `下载` to save everything inside them, **sub-folders included**. New route `GET /asset/output_files` returns the recursive file list in a single request; the download is capped at 5000 files and stops with a message above that, instead of silently dropping files.<br>
  **下载整个文件夹** —— 勾选文件夹后点 `下载`，会把里面的东西**连子目录**一起存下来。新增路由 `GET /asset/output_files`，一次请求返回递归文件清单；上限 5000 个文件，超过则提示并中止，不会静默少下。

## [1.2.1] - 2026-11-03

### Changed · 改动

- **Folder view layout reworked · 文件夹视图布局重排** — folder actions moved to the **top of the left panel** as one compact button row, and the right panel is now a **pure image grid with no button bar**, so nothing eats into the viewing area. The left panel holds a clickable breadcrumb plus the **whole folder tree** of the output directory (indented, with a file count per folder).<br>
  **文件夹视图布局重排** —— 文件夹相关按钮全部移到**左栏顶部**的紧凑按钮行，右栏变成**纯图片网格**（去掉按钮条），不再挤占看图区域。左栏是可点面包屑 + 输出目录的**整棵文件夹树**（按层级缩进，带每个文件夹的文件数）。
- **Keyboard navigation · 键盘导航** — click any folder in the tree, or walk it with `↑` / `↓`, and the right panel switches to that folder's images immediately. The clickable breadcrumb replaces the old "up" button, so jumping to any parent takes one click. The keys are strictly scoped (panel open + folder view + no preview open + focus not in a text field), so ComfyUI's canvas shortcuts are unaffected.<br>
  **键盘导航** —— 点树中任一文件夹，或用 `↑` / `↓` 走树，右侧立刻切到该文件夹的图片。可点面包屑取代原来的「上级」按钮，回任一层只要一次点击。按键有严格作用域（面板已打开 + 文件夹视图 + 未开预览 + 焦点不在输入框），不影响 ComfyUI 画布自身的快捷键。
- **Space savings · 省空间** — the search box is now a fixed, narrower width, and the buttons added in 1.2.0 (`文件夹` / `新建` / `改名` / `删除` / `多选` / `剪切` / `粘贴` / `刷新`) carry **no icons**.<br>
  **省空间** —— 搜索框改为固定窄宽度；1.2.0 新增的按钮（`文件夹` / `新建` / `改名` / `删除` / `多选` / `剪切` / `粘贴` / `刷新`）全部**不带图标**。
- `改名` / `删除` now act on the **current folder** (previously on a separately selected sub-folder), and `新建` creates inside the current folder. The search box and the image/video filter now also apply to the folder view's image grid.<br>
  `改名` / `删除` 改为作用于**当前文件夹**（此前作用于单独选中的子文件夹），`新建` 建在当前文件夹内；搜索框与图片/视频筛选在文件夹视图里也开始生效。
- New route `GET /asset/folder_tree` returns the whole folder tree in a single request (the folder view no longer needs one request per folder).<br>
  新增路由 `GET /asset/folder_tree`，一次请求返回整棵文件夹树（文件夹视图不再需要每个文件夹发一次请求）。

## [1.2.0] - 2026-11-03

### Added · 新增

- **Folder view · 文件夹视图** — a third view alongside grid and calendar that browses the ComfyUI output directory as a folder tree, laid out as a folder list on the left and an asset grid on the right (same idea as [ComfyUI-Load-Image-Media-Browser](https://github.com/wardenlee/ComfyUI-Load-Image-Media-Browser)). It lists sub-folders with an asset count and files with thumbnails (archive thumbnails are reused when the asset is archived), plus breadcrumbs and an *Up* button for navigation.<br>
  在网格、日历之外新增第三个视图，把 ComfyUI 输出目录当文件夹树浏览，左栏文件夹列表 + 右栏资产网格（思路同 [ComfyUI-Load-Image-Media-Browser](https://github.com/wardenlee/ComfyUI-Load-Image-Media-Browser)）。子文件夹带资产数量，文件带缩略图（已归档的复用归档缩略图），并提供面包屑与「上级」导航。
- **Folder management · 文件夹管理** — create, rename and delete folders at any level of the output directory. Empty folders are removed right away; deleting a non-empty folder is a two-step confirmation that first reports how many files are inside. Names are validated, and the output root can neither be renamed nor deleted.<br>
  可在输出目录任意层级**新建 / 改名 / 删除**文件夹。空文件夹直接删；删非空文件夹走两步确认，先告诉你里面有几个文件。名字会做合法性校验，输出根目录既不能改名也不能删除。
- **Cut & paste to move assets · 剪切粘贴搬资产** — multi-select assets in the folder view, press `✂ Cut`, enter the target folder and press `📋 Paste`. The move is **whole-entry**: the file on disk is moved, the archive entry's recorded source path is rewritten, and the archive state key is migrated. As a result the asset keeps its prompt / params / models / workflow / thumbnail after the move, deleting it still removes both the archive copy and the original file, and the moved file is **not archived a second time**. Name collisions in the destination are resolved with an `_1`, `_2`… suffix instead of overwriting.<br>
  文件夹视图里多选资产 → `✂ 剪切` → 进入目标文件夹 → `📋 粘贴`。搬移是**整条目**的：磁盘文件搬走、归档条目记录的来源路径改写、归档状态键迁移。因此搬完后提示词/参数/模型/工作流/缩略图依然挂着，删除时归档副本与原始文件仍会一起删掉，并且**不会被当成新产物重复归档**。目标里同名冲突自动加 `_1`、`_2`… 后缀，不覆盖任何文件。

- **Renaming keeps everything attached · 改名同样不脱链** — renaming a folder relinks **every** asset inside it, recursively (its archive entry's source path *and* the archive state key), so a renamed folder never gets re-archived and its thumbnails stay attached. The recorded "last opened" time follows moves and renames too, so sorting by it stays correct.<br>
  文件夹改名会把里面**每一个**资产（递归含子目录）的归档链接一起改写（归档条目的来源路径**与**归档状态键），所以改过名的文件夹不会被重复归档、缩略图也不会掉。记录的「打开时间」同样跟着搬移与改名一起迁移，按它排序依然正确。

### Changed · 改动

- **Unified sorting · 统一排序** — a single Sort dropdown in the toolbar now applies to the folder list, the folder view grid, the grid view and the calendar day list. Options: created time ↓/↑, last-opened time ↓/↑, name A→Z / Z→A; **the default is newest created first**. Items with no timestamp always sort last. The choice is remembered in the browser.<br>
  工具栏新增一个共用的「排序」下拉，同时作用于文件夹列表、文件夹视图网格、网格视图与日历当天列表。选项：新建时间 ↓/↑、打开时间 ↓/↑、名称 A→Z / Z→A，**默认最近新建在前**；没有时间戳的项一律排在最后；选择会被浏览器记住。
- **"Last opened" is tracked by the plugin · 「打开时间」由插件记录** — opening an asset in the preview (or entering a folder) records that moment in `open_state.json` inside the archive directory, so "last-opened" sorting reflects how *you* actually use the library instead of the OS access time (which Windows usually does not maintain).<br>
  在预览里打开资产（或进入某个文件夹）时，插件把这一刻记到归档目录下的 `open_state.json`，所以「打开时间」反映的是**你**实际的使用顺序，而不是操作系统访问时间（Windows 通常不维护它）。
- Asset listings now also expose `source_rel`, `created`, `mtime` and `opened`, and newly archived assets record their creation time and source modification time.<br>
  资产列表新增 `source_rel` / `created` / `mtime` / `opened` 字段；新归档的资产会记录创建时间与来源文件的修改时间。

### Notes · 说明

- Archiving is still a copy; the folder view only ever touches files **inside the configured output directory** (every path is normalised and prefix-checked, so `..` and absolute paths are rejected).<br>
  归档依然是复制；文件夹视图只会动**配置的输出目录之内**的文件（所有路径都做规范化与前缀校验，`..` 与绝对路径一律拒绝）。
- No new configuration keys, no new dependencies, no build step.<br>
  没有新增配置项、没有新增依赖、没有构建步骤。

## [1.1.1] - 2026-10-31

### Fixed · 修复

- Downloads never include thumbnails, even with `download_include_metadata` enabled.<br>
  即使打开了 `download_include_metadata`，下载也绝不再包含缩略图。

## [1.1.0]

### Added · 新增

- Clean downloads (assets only, flattened by default) with two settings to bring metadata and per-asset folders back.<br>
  干净下载（默认只下资产本体并平铺），两个开关可恢复元数据与每资产文件夹。
- Preview navigation with `←` / `→` inside the large-image dialog.<br>
  大图预览内用 `←` / `→` 翻页。

[1.2.6]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/4fff87f5...HEAD
[1.2.5]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/02a7d41c...4fff87f5
[1.2.4]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/452927af...02a7d41c
[1.2.3]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/2abd11b3...452927af
[1.2.2]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/d06d239...2abd11b3
[1.2.1]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/29a9c05...d06d239
[1.2.0]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/74dcc0a...29a9c05
