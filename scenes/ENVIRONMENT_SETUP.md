# 环境配置

在自己的 Mac 上用命令行跑 `scenes/` 里的脚本的配置方法，前提是 Claude Code 开着沙箱：只能读 `~/Desktop/test`，网络只放行 GitHub，不能跳出沙箱。遇到的问题和配置背景见 [`DEBUG.md`](DEBUG.md)。

## 1. 先加禁令：`~/.claude/settings.json`

在 `permissions.deny` 里加一条（Claude 改不了 `settings.json`，要你自己改）：

```json
"Bash(* --enable-autoexec*)"
```

改完重开 Claude 会话，然后让 Claude 跑 `blender --help --enable-autoexec`：被拦住就说明规则生效了。

## 2. 克隆仓库

```bash
mkdir -p ~/Desktop/test && cd ~/Desktop/test && git clone https://github.com/Vermillionnnn/TRPG_design.git
```

## 3. 在桌面版 Code 里选择工作目录

在 Code 标签页里选 `~/Desktop/test/TRPG_design`。一定要选仓库根目录，否则 Claude 写不了仓库，也读不到 `CLAUDE.md`。Claude 能 `git fetch` / `git pull`，`git push` 要你在沙箱外执行。

## 4. 安装 Blender 并确认版本

从 [blender.org](https://www.blender.org/download/) 下载（Apple 芯片选 ARM64），或者 `brew install --cask blender`。装好后**自己双击打开一次再关掉**，因为 Gatekeeper 的首次运行确认框在沙箱里弹不出来。

脚本在下面两个版本上跑过：

- 本地 Mac：`Blender 5.2.3 LTS`（Apple 芯片，hash e13b728c6880）
- 本地 Mac Beta：`Blender 5.3.0 Beta`（`/Applications/Blender_beta.app`，hash 4768a6eac54c），沙箱内渲染用它

## 5. 用 `blender.sh` 测试

[`blender.sh`](blender.sh) 依次从 `$BLENDER`、`PATH` 里的 `blender`、`/Applications/Blender.app` 找 Blender，把用户目录放到仓库内的 `.blender/`，然后执行：

```bash
Blender -b --factory-startup --disable-autoexec -P 脚本 -- 参数
```

让 Claude 跑下面的命令，能在 `out/t.png` 出图就算通过：

```bash
scenes/blender.sh scenes/homebase/build_scene.py --render out/t.png --samples 8 --res 25
```

> **当前状态**：5.2.3 在沙箱里会崩在 Metal GPU 检测处，这是 Blender 上游的 bug。5.3.0 Beta 已经能在沙箱里出图：
>
> ```bash
> BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh scenes/homebase/build_scene.py --render out/t.png --samples 8 --res 25
> ```
>
> 详情见 [`DEBUG.md`](DEBUG.md) 问题 1。

## 访问检查结果（2026-10-26）

在配好的环境里，让 Claude 分别用 bash 命令和 Read 工具去读各级设置文件；写入只用一个空的项目本地设置做了探针（见下面「写入探针」）。

### 设置文件

| 文件 | 级别 | bash（Seatbelt 沙箱） | Read 工具 |
| --- | --- | --- | --- |
| `~/.claude/settings.json` | 用户（全局） | ❌ `Operation not permitted` | ❌ 被 `blockReadsOutsideWorkingDirectories` 拦住 |
| `~/.claude/settings.local.json` | 用户（全局） | 文件不存在 | ❌ 被 `blockReadsOutsideWorkingDirectories` 拦住 |
| `.claude/settings.json` | 项目 | 文件不存在 | 文件不存在 |
| `.claude/settings.local.json` | 项目（本地） | 文件不存在 | 文件不存在 |
| `/Library/Application Support/ClaudeCode/managed-settings.json` | 管理员 | 文件不存在 | ❌ 被 `blockReadsOutsideWorkingDirectories` 拦住 |
| `/Library/Application Support/ClaudeCode/managed-settings.d/` | 管理员 | 目录不存在 | 未测（同上，工作目录外一律拦住） |

- Claude 读不到任何一级的设置文件。仓库里的 `.claude/` 目前只有 Claude Code 自己用的 `.cc-writes/`。
- 两条路的边界不一样：bash 受 Seatbelt 沙箱限制，挡的是 `~` 和 `/Users` 等目录，`/Library` 能看到（所以能报「不存在」）；Read 工具受 `blockReadsOutsideWorkingDirectories` 限制，工作目录外的路径一律拦住。
- 全局 `settings.json` 读不到，但下面的禁令生效了，说明它确实被 Claude Code 加载了。

### 写入探针

应 VM 要求，让 Claude 往仓库里写一个内容为 `{ }` 的 `.claude/settings.local.json`（空设置，即使写成功也不改变任何行为）：

| 方式 | 结果 |
| --- | --- |
| bash：`printf '{ }\n' > .claude/settings.local.json` | ❌ 执行前被权限层拒绝（`Permission to use Bash ... has been denied`），没走到沙箱 |
| Write 工具 | ❌ `File is in a directory that is denied by your permission settings.` |

两次之后 `.claude/` 里都没有新文件。虽然 `.claude/` 在仓库里、Claude 能写仓库，但 Claude 用两种方式都写不了项目级设置，改设置只能由 VM 自己来。

### `--enable-autoexec` 禁令

| 命令 | 结果 |
| --- | --- |
| `blender --help --enable-autoexec` | ❌ 执行前被拒（`Permission to use Bash ... has been denied`） |
| `/Applications/Blender_beta.app/Contents/MacOS/Blender --help --enable-autoexec` | ❌ 执行前被拒 |

规则按命令文本匹配，所以写完整路径也会被拦住。没有测试短形式 `-y`：它不在禁令范围内，CLAUDE.md 也不允许用。

### 工作目录外的写入与 `acceptEdits`

后续测试发现：编辑工具（Write/Edit）不走 Seatbelt 沙箱，只受 `permissions` 约束。在 auto 模式下，它们能在工作目录外新建和修改文件，而 bash 不能。用 deny 规则「除了仓库都拒绝」的尝试都失败了：带通配符的路径规则会连仓库一起挡住，逐项列出的规则又管不到以后新建的文件（详见 [`claude-settings/2026-10-26-worklog.md`](claude-settings/2026-10-26-worklog.md)）。

最终做法：全局设置恢复到实验前的状态，只加 `"defaultMode": "acceptEdits"`。实测结果：

| 位置 | 编辑工具 | bash |
| --- | --- | --- |
| 仓库内 | ✅ 直接写，不询问 | ✅ |
| 工作目录外的一般位置（如 `~/Desktop`、`~/Documents`） | ⚠️ 每次询问 VM | ❌ 沙箱拦截 |
| `~/Desktop/test` 下的兄弟项目 | ❌ 直接拒绝（项目 local 设置的 deny） | ❌ 沙箱拦截 |
| 各级 `settings.json` / `settings.local.json` | ❌ 直接拒绝 | ❌ 沙箱拦截 |

- 「询问」是软保护：点「允许」就会写入，遇到陌生路径要留意。
- 桌面版里每个会话可能有自己的权限模式，新开会话时要确认是「Accept edits」，而不是 auto。
- 渲染命令自动放行：项目 `.claude/settings.local.json` 里加了 `"allow": ["Bash(BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh *)"]`，实测不再弹窗。命令要写成这个形式，后面不要接 `| grep` 等管道，否则可能匹配不上。
- 设置快照存档在 [`claude-settings/`](claude-settings/)。
