# CLAUDE.md

跑团（D&D 5e，2014 规则）设计与讨论的仓库：3D 场景、网页小作品、矢量美术、立绘和文字资料。没有统一的构建系统，每个作品自带脚本。

## 语言与称呼

- 面向设计者的回复、README、文档一律用中文；代码、代码注释、commit message 用英文。
- 仓库是公开的。提到仓库主人时用昵称 VM 或「设计者」，不要写真名（文件、commit message、PR 描述都适用）。
- 根目录 `README.md` 保持简短，只列目录和作品；细节写进各子文件夹的 README。

## 目录

| 目录 | 内容 |
| --- | --- |
| `scenes/` | Blender 场景，`bpy` 脚本生成 |
| `html/` | 网页作品 |
| `svg/` | 矢量美术（地图、道具卡、图标） |
| `plots/` | 立绘与绘制过程、数据可视化 |
| `notes/` | 设定、规则速查、团务记录 |

每个作品一个子文件夹（如 `scenes/homebase/`），里面放源文件、成品和一份中文 README。新增作品时同时在根 README 的「现有作品」里加一行。

## 各类作品怎么跑

### Blender 场景（`scenes/`）

```bash
scenes/blender.sh scenes/homebase/build_scene.py --render out/wide.png --samples 16 --res 50
```

- `blender.sh` 负责找到 Blender（`$BLENDER`、`PATH`、`/Applications`），把 Blender 用户目录放到仓库内的 `.blender/`，并以 `-b --factory-startup --disable-autoexec` 运行。
- 脚本在 Blender 5.2.3 和 5.3.0 Beta 上实际跑过。VM 的 Mac 上 5.2.3 在沙箱里会崩（Metal 上游 bug），沙箱内渲染用 5.3.0 Beta：`BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh ...`。具体版本：5.2.3 LTS（hash e13b728c6880）、5.3.0 Beta（hash 4768a6eac54c）。
- 云端等没有 Blender 的环境可以 `pip install bpy` 后直接 `python3 scenes/homebase/build_scene.py ...`（`bpy` 只支持特定 Python 版本，5.2 对应 3.13）。
- `homebase` 的参数：`--shot wide|close|top`、`--samples N`、`--res 百分比`、`--anim 目录 [--step N]`、`--save x.blend`。
- 调试时用低采样、低分辨率（`--samples 8 --res 25`，约 20 秒）；正式出图用默认值。
- 可复用的单个物件放 `scenes/assets/`（一个 `.py` 带 `build()` + 一张同名缩略图，`scenes/assets/thumbnail.py` 生成），场景里 `import` 使用，不要复制代码；约定见 [`scenes/assets/README.md`](scenes/assets/README.md)。
- 渲染输出放 `out/`（已忽略）。要提交的成品图放进场景文件夹，并在它的 README 里更新文件表。`.blend` 不进仓库。

### 网页（`html/`）

- `html/bard-lute/bard-lute.html` 是 Artifact 源（只有页面内容），改它之后运行 `python3 html/bard-lute/tools/build_release.py` 重新生成可单独打开的 `bard-lute-release.html`。
- 改了页面里的中文字后运行 `python3 html/bard-lute/tools/subset_font.py`，重新嵌入字体子集（需要访问 Google Fonts）。
- `html/scribe-scroll/` 同样的流程：改 `scribe-scroll.html` 后跑 `tools/build_release.py` 生成 `scribe-scroll-release.html`；改了页面文字后跑 `tools/subset_font.py`，重嵌页面依赖的字体子集。它需要联网和 fontTools、brotli，本地沙箱跑不了，请 VM 在自己的终端跑或交给云端会话。
- 宣传短片：`html/bard-lute/video/tools/make_video.sh`，依赖和流程见 [`html/bard-lute/video/README.md`](html/bard-lute/video/README.md)。中间文件在 `video/.work/`，不进仓库。

### 立绘（`plots/`）

成品图加 README，重点写绘制过程（工具、提示词、迭代），故事背景只写一两句。

## 本地环境（VM 的 Mac）

Claude Code 在沙箱里运行：只能读 `~/Desktop/test`、只能写仓库，网络只放行 GitHub，不能跳出沙箱。配置指南和调试记录由设计者私下保存，不在公开仓库里。

- 只通过 `scenes/blender.sh` 调 Blender，渲染输出写到仓库内的 `out/`。不要使用 `--enable-autoexec` 或 `-y`。
- **本地环境必须**：渲染用 5.3 Beta，命令写成行内前缀 `BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh ...`，不要用 `export BLENDER=...`。原因：5.2.3 在沙箱里会崩（Metal GPU 检测处的 Blender 上游 bug）；`export` 会触发许可询问，行内前缀不会。
- **本地环境必须**：每次 Bash 调用只写一条简单命令，否则会弹窗等 VM 许可：
  - 不要用 `&&`、`;` 串联，不要用子 shell `( )`、后台 `&`、`wait`、管道 `|`、重定向 `>`。要做几件事就分几次调用；要并行就用 Bash 工具的 `run_in_background` 参数。
  - 不要把含 `|`、`<<`、`!`、`;`、`>` 等字符的代码塞进 `python3 -c "..."`：先用 Write 工具写到 `out/xxx.py`（`out/` 已忽略），再运行 `python3 out/xxx.py`。
  - 看输出用 Read 工具读文件或图片，不要靠 `| grep`、`| tail` 过滤。
- 只加载仓库脚本生成的 `.blend`，不加载外部来源的 `.blend`；不 `git fetch` 非本人的仓库。
- 不要尝试 `git push`；可以 `git fetch` / `git pull`，push 由 VM 在沙箱外执行。
- 不要 `pip install`、`curl`、下载字体或模型；需要联网的步骤（如 `subset_font.py`、`make_video.sh`）请 VM 在自己的终端里跑。
- 不要修改 `.claude/` 下的配置，也不要尝试绕过沙箱。命令被拦截时，把报错里的路径或域名告诉 VM，由 VM 决定是否放行；放行由 VM 手动加在用户级 `~/.claude/settings.json` 的 `sandbox.filesystem.allowRead`（只加报错的那一个路径；开着 `blockReadsOutsideWorkingDirectories` 时项目级 `allowRead` 不计入沙箱）。

## 注意

- 不要提交 `.blend`、渲染中间帧、`.work/` 之类可以重新生成的大文件。
- 改了脚本参数或输出文件时，同步更新对应 README。
- 推送或开 PR 之前检查身份（仓库是公开的，不能带出设计者的真名或私人邮箱）：
  1. `git config user.name` / `user.email` 只能是 `VM` + `132499586+Vermillionnnn@users.noreply.github.com`，或 Claude + `noreply@anthropic.com`；不是的话先用 `git config user.name/user.email` 改掉再提交。
  2. `git log origin/main..HEAD --format='%an %ae / %cn %ce'` 只出现上面两种身份（本地按上面「单条简单命令」的要求，不要接 `| sort -u`）；commit message、改动内容、PR 标题和描述里也只用 VM 或「设计者」。云端开 PR 时描述开头会自动带一行 `Requested by **名字** · project thread`，加粗的名字一律写 VM（保留上面的注释标记行和链接）。
  3. 真名关键词不写进仓库。用它们 grep 本次的 `git log -p origin/main..HEAD`；云端从项目记忆里取，本地由 VM 自己检查。有命中就先改（未推送的 commit 用 `git commit --amend` / `git rebase` 修正），已推送到 `main` 的先告诉 VM，不要擅自改写历史。
