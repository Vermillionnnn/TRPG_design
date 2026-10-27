# 宣传短片《我把我们团的吟游诗人做成了一个可以玩的音游》

用上一级目录的 [`bard-lute.html`](../bard-lute.html) 自动生成的 43 秒横屏短片（1920×1080，30fps）。分镜见 [storyboard.md](storyboard.md)。

## 生成

```sh
html/bard-lute/video/tools/make_video.sh                         # 默认用 html/bard-lute/bard-lute.html
html/bard-lute/video/tools/make_video.sh path/to/bard-lute.html  # 或指定别的页面
```

成片在 `html/bard-lute/video/.work/bard_ad_1080p.mp4`（成片和中间文件都不进仓库；`WORK=` 可换目录，`JOBS=` 设并行数，默认 4）。全程约 10 分钟。

依赖：Node + Playwright（带 Chromium）、Python 3 + numpy + scipy、ffmpeg、curl（下载 Google Fonts 的 ZCOOL 小薇、Noto Serif SC、Uncial Antiqua）。

## 流程

| 步骤 | 脚本 | 做什么 |
|------|------|--------|
| 声音 | `audio_capture.js` | 实时播放页面（三首曲目、和弦与琴键、音游、开场扫弦），把页面的音频输出录成 webm |
| 混音 | `mix.py`, `audio_tracks.py` | 按时间轴交叉淡化各段音乐，铺一层合成的篝火噼啪与夜虫声，转场处加呼声；之后统一到 −14 LUFS |
| 规划 | `vplan.py` | 算出每一帧成片需要哪次录制、哪个虚拟时刻、哪块区域、放大几倍 |
| 画面 | `vrun.js`, `vcap.js`, `vclock.js` | 在虚拟时钟下驱动页面（接管 rAF、计时器、`performance.now`、音频时钟和 CSS 动画），逐帧截取所需区域，特写按最终倍数高分辨率渲染 |
| 演奏 | `bot.js` | 音游自动演奏（固定随机种子，大多完美，少量不错） |
| 合成 | `build_manifest.py`, `comp.html`, `render.js` | 合成器按时间轴摆放素材、字幕、转场和连击特效，逐帧渲染，再用 ffmpeg 与混音合成 |

画面与声音分开录：声音必须实时录，画面用虚拟时钟才能逐帧清晰。两者都以「点播放 / 按键 / 开始音游」的时刻为锚点，曲子的节拍由页面按固定时间表排，所以能对齐。
