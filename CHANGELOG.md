# Changelog

All notable changes to **ComfyUI-AssetManager** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> 本文件记录 **ComfyUI-AssetManager** 的所有重要改动，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与[语义化版本](https://semver.org/lang/zh-CN/)。

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

[1.2.2]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/d06d239...HEAD
[1.2.1]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/29a9c05...d06d239
[1.2.0]: https://github.com/wardenlee/ComfyUI-AssetManager/compare/74dcc0a...29a9c05
