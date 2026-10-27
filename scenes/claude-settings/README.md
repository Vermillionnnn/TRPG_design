# Claude Code 设置存档

VM 本地 Mac 上 Claude Code 的设置快照，以及 2026-10-26 调试沙箱和权限规则的工作日志。配置步骤见 [`../ENVIRONMENT_SETUP.md`](../ENVIRONMENT_SETUP.md)。

| 文件 | 内容 |
| --- | --- |
| [`2026-10-26-global-settings.json`](2026-10-26-global-settings.json) | 用户级 `~/.claude/settings.json`（调试结束后的最终状态，由 VM 在沙箱外打印后存档） |
| [`2026-10-26-project-settings.local.json`](2026-10-26-project-settings.local.json) | 仓库 `.claude/settings.local.json`（与原文件逐字节一致） |
| [`2026-10-26-worklog.md`](2026-10-26-worklog.md) | 当天的工作日志：Blender 沙箱崩溃、5.3 Beta、访问检查、deny 规则调试 |

## 当前状态（2026-10-26）

| 位置 | 编辑工具（Write/Edit） | bash |
| --- | --- | --- |
| 仓库内 | ✅ 直接写，不询问 | ✅ |
| 工作目录外的一般位置（如 `~/Desktop`、`~/Documents`） | ⚠️ 每次询问 VM（`defaultMode: acceptEdits`） | ❌ 沙箱拦截 |
| `~/Desktop/test` 下的兄弟项目 | ❌ 直接拒绝（项目 local 设置的 3 条 deny） | ❌ 沙箱拦截 |
| 各级 `settings.json` / `settings.local.json`、hooks、skills 等 | ❌ 直接拒绝（全局 deny） | ❌ 沙箱拦截 |

- 编辑工具不走 Seatbelt 沙箱，只受 `permissions` 约束；bash 受沙箱约束。
- 工作目录外的「询问」是软保护：点「允许」就会写入。
- 渲染命令 `BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh ...` 由项目 local 的 allow 规则自动放行，不要接管道。
- Claude 读不到全局设置；桌面版的终端面板用的是 VM 自己的权限，在那里打印的内容 Claude 能看到。
