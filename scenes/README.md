# 3D 场景

这里的场景都是用 Blender 的 Python 脚本（`bpy`）程序化生成的，每个场景一个子文件夹，里面有生成脚本和渲染结果。`.blend` 文件可由脚本重新生成，不进仓库。

| 场景 | 说明 |
| --- | --- |
| [`homebase/`](homebase/) | 法师小队的据点，剖面小房间 |
| [`blackstaff-office/`](blackstaff-office/) | 深水城黑杖塔办事处，剖面内景 |
| [`shadow-base/`](shadow-base/) | the Shadow 小队在深水城的据点，外景沙盘 |
| [`weapons/`](weapons/) | 高精度武器的展示渲染：宝石刺剑（已完成）、藤蔓法杖、魔法鲁特琴；模型在 `assets/` |
| [`assets/`](assets/) | 素材库：可复用、带参数的单个物件（一份代码 + 一张缩略图），场景脚本直接引用 |
| [`tools/`](tools/) | 辅助脚本：`frames_to_gif.py` 把渲染帧合成循环 GIF（在 Blender 里跑，不需要 ffmpeg） |

在自己的 Mac 上配置 Blender 和 Claude Code 沙箱的步骤，以及访问检查结果，见 [`ENVIRONMENT_SETUP.md`](ENVIRONMENT_SETUP.md)；遇到的问题见 [`DEBUG.md`](DEBUG.md)。

> **当前状态**：5.2.3 在沙箱里会崩在 Metal GPU 检测处（Blender 上游 bug），沙箱内渲染改用 5.3.0 Beta：命令前加 `BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender`。

> **本地环境（VM 的 Mac）的 agent 必读**：渲染命令必须写成下面这种形式，否则会弹窗等 VM 许可，或者在沙箱里崩溃（同一规定也写在根目录 `CLAUDE.md`）：
>
> ```bash
> BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh 脚本 参数...
> ```
>
> - 用行内前缀，不要 `export BLENDER=...`。
> - 命令后面不要接 `| grep`、`| tail` 之类的管道，也不要加重定向。直接运行，跑完再用 Read 工具看输出的图。
> - 只有这个形式在项目 `.claude/settings.local.json` 的 allow 规则里，会自动放行。
> - 每次 Bash 调用只写一条命令：不要用 `&&`、`;` 串联，不要用子 shell `( )`、后台 `&`、`wait`。先删旧图、再渲染、再看目录，就分成三次调用。
> - 两张图想同时渲染，就用 Bash 工具的 `run_in_background` 参数分别发起两次调用，不要在命令里写 `&`。
> - 检查图片、GIF 之类的小脚本不要塞进 `python3 -c "..."`（代码里的 `|`、`<<`、`!`、`;` 会被当成 shell 符号而弹窗）：先用 Write 工具写到 `out/xxx.py`，再运行 `python3 out/xxx.py`。
>
> 下面的示例省略了这个前缀，在 VM 的 Mac 上运行时要加上。

## 用命令行渲染

```bash
# 全景，低采样快速预览（几十秒）
scenes/blender.sh scenes/homebase/build_scene.py --render out/wide.png --samples 16 --res 50

# 正式出图
scenes/blender.sh scenes/homebase/build_scene.py --render out/wide.png --shot wide
scenes/blender.sh scenes/homebase/build_scene.py --render out/close.png --shot close
scenes/blender.sh scenes/homebase/build_scene.py --render out/top.png --shot top

# 存成 .blend，之后可以用 Blender 界面打开继续调
scenes/blender.sh scenes/homebase/build_scene.py --save out/homebase.blend

# 动画帧（每 3 帧渲一帧），再用 ffmpeg 合成
scenes/blender.sh scenes/homebase/build_scene.py --anim out/frames --step 3 --samples 32
```

各场景的参数见它自己的 README。`out/` 和 `.blender/` 已在 `.gitignore` 里。渲染默认用 CPU。改脚本时用 `--samples 8 --res 25` 快速出图。

只打开仓库脚本生成的 `.blend`：外部来源的 `.blend` 里可能嵌着 Python 脚本，确实要用时保持「Auto Run Python Scripts」关闭。
