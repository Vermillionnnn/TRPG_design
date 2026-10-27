# 调试记录：Blender 在沙箱里跑不起来

在 Claude Code 沙箱里跑 Blender 遇到的问题和排查方法。配置步骤见 [`ENVIRONMENT_SETUP.md`](ENVIRONMENT_SETUP.md)。

## 问题 1：启动时在 Metal GPU 检测处崩溃（Blender 上游 bug，5.3.0 Beta 已可用）

**日期**：2026-10-26
**环境**：VM 的 Mac（Mac16,8，Apple M4 Pro，macOS 26.6.2），Blender 5.2.3 LTS（hash e13b728c6880），Claude Code 桌面版沙箱

### 现象

在沙箱里跑 ENVIRONMENT_SETUP.md 第 5 步的测试命令：

```bash
scenes/blender.sh scenes/homebase/build_scene.py --render out/t.png --samples 8 --res 25
```

约 0.5 秒后退出，没有生成 `out/t.png`。输出里只有：

```
Blender 5.2.3 LTS (hash e13b728c6880 built 2026-10-22 01:31:22)
Writing: /tmp/claude-501/blender.crash.txt
```

崩溃日志的调用栈（节选）：

```
6  blender::gpu::supports_barycentric_whitelist(MTLDevice)
7  blender::gpu::MTLBackend::metal_is_supported()
8  blender::GPU_backend_type_selection_detect()
9  blender::wm_homefile_read_ex(...)
10 blender::WM_init(...)
```

崩在 `_platform_strstr`，Python 调用栈为空。

### 已经确认的

- `blender --version` 在沙箱里正常，说明 Blender 能找到、能执行，Gatekeeper 也已经放行。
- 崩溃发生在 `WM_init` 阶段，场景脚本还没开始执行，跟 `build_scene.py` 无关。
- 即使是 `-b` 无界面模式，Blender 启动时仍会检测 GPU 后端（Metal）。
- `blender.sh` 已经建好 `.blender/user/`，所以不是用户目录的问题。
- 报错里没有 `Operation not permitted`，也没有任何文件路径。
- 启动时的 `ArchWarn: ARCH_CACHE_LINE_SIZE != ...` 是 Blender 自带的 USD 库在 Apple 芯片上的常见警告，跟这次崩溃无关。
- macOS 崩溃报告（14:40:35 那次运行）：
  - `EXC_BAD_ACCESS (SIGSEGV)`，`KERN_INVALID_ADDRESS at 0x0`，`strstr` 读了空指针。
  - 已经加载了 GPU 驱动 `AGXMetalG16X.bundle`，说明 Metal 设备本身创建成功了，问题出在后面读设备信息这一步。
  - `Responsible Process: claude`、`Coalition: com.anthropic.claudefordesktop`，确认是从 Claude 的沙箱 shell 启动的。
- `log show` 按 `deny` + `mach-lookup` + `Blender` 查最近 30 分钟，结果为空。
- 加 `--gpu-backend` 参数绕不过去：反汇编 5.2.3 的 `bpy` 模块（Linux 构建，同一份源码）可见，`wm_homefile_read_ex` 无论有没有指定后端都会调用 `GPU_backend_type_selection_detect()`，指定后端只影响检测哪一个。`--factory-startup` 也不跳过这一步。

### 原因：Blender 上游已知 bug

Blender 的 bug 跟踪里有两条对应的报告（链接来自评审，本地沙箱只能访问 GitHub，未能打开核实）：

- [#163296 SIGSEGV in supports_barycentric_whitelist during Metal backend detection in a restricted macOS process](https://projects.blender.org/blender/blender/issues/163296)：函数名和本次崩溃日志一致。
- [#163272 Crash on startup when MTLCreateSystemDefaultDevice() returns nil (sandboxed / non-GUI execution contexts)](https://projects.blender.org/blender/blender/issues/163272)：同一类问题，已有修复提交 [19726af88c「Metal: Allow running Blender without GPU」](https://projects.blender.org/blender/blender/commit/19726af88c0380820c1b49e89b265b9d67e793d8)。

修复进了哪个版本、是否覆盖「设备存在但名字为 nil」这种情况，还没确认。但 5.2.3（2026-10-22 构建）照样崩，说明 5.2.3 里没有这个修复。

在受限的进程里（这里是 Claude Code 的沙箱），Metal 返回的设备信息不完整，Blender 没检查空值就传给了 `strstr`。被挡的操作大概率是 IOKit 相关的，而 Claude Code 的沙箱设置里没有 IOKit 的放行项，所以靠改沙箱配置修不好。

关于 `log show` 查不到记录：不一定是拦截不写日志。Seatbelt 的 `deny` 记录挂在 `kernel` 进程名下，按 `eventMessage CONTAINS "Blender"` 能匹配到，按 `process == "Blender"` 匹配不到。下面第 2 步用的是前一种写法。

### 进展：5.3.0 Beta 在沙箱内能跑

2026-10-26 用 `/Applications/Blender_beta.app`（Blender 5.3.0 Beta，hash 4768a6eac54c，`blender-v5.3-release` 分支，2026-10-23 构建）在沙箱里跑同一条测试命令：

```bash
BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender scenes/blender.sh scenes/homebase/build_scene.py --render out/t.png --samples 8 --res 25
```

- 没有崩溃，约 8 秒出图（`out/t.png`，画面正常），日志里也没有 GPU 或 Metal 相关的报错。
- 说明 5.3 里已经包含了能处理这种情况的修复，至少对这台机器有效。
- 脚本输出了 6 条 `DeprecationWarning`：`Material.use_nodes` / `World.use_nodes` 预计在 Blender 6.0 移除。现在不影响出图。

### 下一步

1. **在沙箱外跑一次**（VM 在自己的终端里）。这一步既能确认原因，又能先拿到一张图：

   ```bash
   cd ~/Desktop/test/TRPG_design && scenes/blender.sh scenes/homebase/build_scene.py --render out/t.png --samples 8 --res 25
   ```

   沙箱外也崩的话，就不是沙箱的问题，要另查 Blender 和 Metal。

2. （可选）想弄清楚具体被拦的是什么，可以让 Claude 在沙箱里再跑一次，然后马上在沙箱外查：

   ```bash
   /usr/bin/log show --last 5m --style compact --predicate 'eventMessage CONTAINS "deny" AND eventMessage CONTAINS "Blender"'
   ```

   查到什么都不改变结论，不指望靠它修好。

### 现在怎么办

| 做法 | 说明 |
| --- | --- |
| **用 5.3.0 Beta（当前做法）** | Claude 在沙箱里用 Beta 渲染：命令前加 `BLENDER=/Applications/Blender_beta.app/Contents/MacOS/Blender`，或者 VM 在桌面版环境变量里设好。代价是 Beta 版本身可能有别的问题；正式出图可以再用 5.2.3 在沙箱外核对一次 |
| 分工渲染 | Claude 在沙箱里改脚本和参数，VM 在自己的终端里用 5.2.3 跑 `scenes/blender.sh ...` 出图到 `out/`，Claude 再读 `out/` 里的图看结果。和「push 由 VM 做」是同一种分工，不改任何设置 |
| 等正式版 | 5.3 正式发布后换成正式版；或者等 5.2.x LTS 后续小版本是否也带上修复（#163272 / #163296） |
| 自己写 Seatbelt 规则 | 把 `blender.sh` 的副本放到 Claude 写不到的地方，用 `excludedCommands` 让它跳出 Claude 的沙箱，副本内部再用 `sandbox-exec` 套一份自己写的规则：允许 IOKit 和 Metal，禁网络，只许写仓库。能做，但要写和调试 `.sb` 配置，`sandbox-exec` 又已被苹果标为 deprecated，等上游修好就白做了。除非很快要高频渲染，否则不值得 |

看起来能绕过、其实不行的办法：

- `pip install bpy`：Mac 上装的是同一份代码，`WM_init` 里一样会检测 Metal。
- `--gpu-backend`：见上面「已经确认的」，不跳过检测，而且 macOS 上除了 Metal 也没有别的后端可选。
- 直接把 Blender 加进 `excludedCommands`：等于让它完全不受沙箱约束，不要这样做。

## 通用排查方法

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 报某个路径 `Operation not permitted` | 沙箱挡了读取 | 只把那一个路径加到 `~/.claude/settings.json` 的 `sandbox.filesystem.allowRead`。开着 `blockReadsOutsideWorkingDirectories` 时，项目级 `allowRead` 不计入沙箱 |
| 崩溃或失败，但报错里没有文件路径 | 可能是 Mach lookup 或 IOKit 访问被挡（字体、GPU、窗口服务器等系统服务） | 在沙箱外查 `log show` 里的 `deny` 记录。如果是 `mach-lookup`，可以试着把对应的服务加到 `sandbox.network.allowMachLookup`，但有[报告](https://claudeissues.com/issue/82793-sandbox-allowmachlookup-is-not-passed-through-from-settings-json-so-the-only-fix)（第三方汇总站，未核实）说这一项传不到沙箱，别指望它；如果是 `iokit-*`，没有对应的放行项 |
| 找不到 Blender | 不在 `/Applications` 或 `PATH` 里 | 在桌面版环境变量里设 `BLENDER=/path/to/Blender`，或者软链接到 `/usr/local/bin/blender` |
| 第一次运行没反应 | Gatekeeper 首次运行确认框在沙箱里弹不出来 | 自己双击打开一次 Blender |

## 沙箱配置背景

- **`blender.sh` 为什么要改用户目录**：Blender 在 macOS 上会去读 `~/Library/Application Support/Blender/…`。在沙箱里这个路径返回 `Operation not permitted`，而不是「文件不存在」，可能导致 Blender 报错而不是跳过。所以 `blender.sh` 用 `BLENDER_USER_RESOURCES` 把用户目录改到仓库内的 `.blender/`。
- **`/Applications` 不用加 `allowRead`**：`blockReadsOutsideWorkingDirectories` 封锁的是 `~`、`/Users`、`/Volumes` 等目录，`/Applications` 不在其中，默认就能读。
- **`--enable-autoexec` 禁令**：只匹配命令文本，挡不住短形式 `-y`，也挡不住藏在脚本里的写法。但 `--factory-startup` 下 Blender 默认就不会自动运行 `.blend` 里嵌的脚本，所以这条禁令是多加的一道锁，不是唯一的保护。
- **`denyRead: ["~/"]`**：开着 `blockReadsOutsideWorkingDirectories` 时是多余的；但工作目录路径里含有 `*`、`?`、`[` 时 block 会失效，所以留着兜底。
- **联网**：Claude 启动的 Blender 受沙箱网络白名单限制。你自己双击打开 Blender 时它不在沙箱里，联网由 Blender 偏好设置里的「Allow Online Access」控制，默认关闭。
- **外部 `.blend`**：外部来源的 `.blend` 进入仓库只有一个技术通道，就是 `git fetch <URL>`。目前没有硬性封堵，靠 `CLAUDE.md` 约束；如果真出现过一次，再考虑加 PreToolUse hook。
- **云端和本地的区别**：云端用的是 Linux 上 pip 安装的 `bpy` 模块，和 Mac 上的 Blender.app 是不同的构建。API 相同，但云端没有 GUI 和 Metal，所以不会碰到问题 1。
