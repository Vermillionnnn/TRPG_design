# 烛堡抄卷

《林间夜曲》的法师版：希娜·露弥（见 [`plots/hina-lumi/`](../../plots/hina-lumi/)）在烛堡书库抄写法术卷轴，玩法是逐词打字。页面是 Artifact 源（只有页面内容），字体全部内嵌，不从外部加载任何东西。

## 现有文件

| 文件 | 说明 |
| --- | --- |
| `scribe-scroll.html` | Artifact 源：湿壁画、打字玩法、规格卡，两种字体以 woff2 子集内嵌 |
| `scribe-scroll-release.html` | 发布版：补上文档外壳，可以单独用浏览器打开或发给别人，由下面的脚本生成 |
| `tools/build_release.py` | 从 Artifact 源生成发布版 |
| `tools/subset_font.py` | 从 Google Fonts 取两种字体的子集，重新嵌进页面 |
| `tools/compose_titulus.py` | 从《林间夜曲》题记的安色尔体轮廓里拆出字母，拼成新的拉丁题记，不需要下载字体 |

改了 `scribe-scroll.html` 之后重新生成发布版：

```bash
python3 html/scribe-scroll/tools/build_release.py
```

生成题记轮廓（输出写到已忽略的 `out/`）：

```bash
python3 html/scribe-scroll/tools/compose_titulus.py 'HIC·MAGA·CARMINA·NOTAT' > out/titulus.txt
```

可用字母只有 A C D E G H I L M N O R T V 和间隔点。题记意思是「此处法师抄写咒文」。

## 字体

| 字体 | 版权方 | 许可 | 用在哪里 | 子集 |
| --- | --- | --- | --- | --- |
| [Noto Serif SC](https://fonts.google.com/noto/specimen/Noto+Serif+SC) | Adobe，由 Google Fonts 发布（[google/fonts](https://github.com/google/fonts/tree/main/ofl/notoserifsc)） | SIL OFL 1.1 | 全页正文、标题、卷轴上的中文释义 | 页面里出现的所有非 ASCII 字符 + 可打印 ASCII |
| [Fondamento](https://fonts.google.com/specimen/Fondamento) | Astigmatic（[google/fonts](https://github.com/google/fonts/tree/main/ofl/fondamento)） | SIL OFL 1.1 | 羊皮纸上的英文咒文（`.sheet .text`），页面里改名为 Scroll Chancery，见下 | 可打印 ASCII + 中点 `·`（褪色字母的占位符） |
| [Uncial Antiqua](https://fonts.google.com/specimen/Uncial+Antiqua) | Astigmatic（[google/fonts](https://github.com/google/fonts/tree/main/ofl/uncialantiqua)） | SIL OFL 1.1 | 湿壁画题记（只用字母轮廓，见下） | — |

三种字体的版权声明和许可证全文在仓库根目录的 [`OFL.txt`](../../OFL.txt)；页面 `<style>` 开头的注释里也写了版权声明，所以单独发出去的发布版也带着它们。新增字体时在 `OFL.txt` 顶部加一段版权声明，在页面注释里加一行。

咒文每个字母是单独的 `<span>`，连笔草书会断开，所以选了不连笔的意大利文书手写体 Fondamento。备选也都核对过（都是 SIL OFL，信息取自 google/fonts 的 `METADATA.pb`）：Almendra（Ana Sanfelippo）、IM Fell DW Pica 斜体（Igino Marini）、Tangerine（Toshi Omagari）、Mea Culpa（Robert Leuschke）、Pinyon Script（Nicole Fally）。后三种是连笔体，拆成单字母后效果不好。

「Fondamento」是保留字体名（Reserved Font Name）。按 OFL FAQ 2.6，网页字体的子集算修改版，不能再用保留字体名，所以页面里的 CSS 家族名和子集内部的字体名都改成了 Scroll Chancery，版权声明（含保留字体名声明）原样保留。`subset_font.py` 每次重新生成都会自动改名。

改了页面里的中文后重新嵌入字体。需要访问 Google Fonts，改名还需要 fontTools 和 brotli（`pip install fonttools brotli`），所以由 VM 在自己的终端跑，或交给云端会话：

```bash
python3 html/scribe-scroll/tools/subset_font.py
```

## 画面

沿用《林间夜曲》的仿十四世纪湿壁画：1000×800 画框、回纹和菱形边、下方石灰色题记、灰泥颗粒与裂纹。

- **人物**：希娜侧身朝右坐在斜面抄经台前（中世纪「福音书作者写作」的构图），用黑色鸦羽笔写卷轴。公主切黑长直发，深靛蓝长袍配金色刺绣下摆，米白短斗篷，红宝石扣，腰带挂卷轴筒；背后收拢一对及地的黑色鸦翼。
- **光轮**：头后的金色光轮画成法阵，阴阳道五芒星和西式符文合在一起，打字时缓慢转动，连对越多越亮。
- **场景**：上方是缀金星的天青穹顶；左侧书架，右侧拱窗（窗外夜空和烛堡塔影），窗下是插满卷轴的格柜，窗台上停着一只渡鸦；抄经台旁立着烛台。
- **动作**：抄经台台面朝观者倾斜，打一个字母，笔尖落下一笔墨迹，纸上亮起一圈小光环，抄完一个词光环更大（关键词是金色）；换行时去墨水瓶蘸墨，打错一次落一滴墨渍。

## 玩法

- 选法术：火焰箭（戏法）、魔法飞弹、护盾术（1 环）、迷踪步（2 环）、火球术、法术反制（3 环）。每道法术一段自拟的英文咒文，二三十个词，关键词附中文释义。
- 选笔力：**学徒**全文可见；**书士**关键词的部分字母褪去；**大师**关键词只剩首字母，要凭释义打出正确的词。同一位置错两次就提示该字母。
- 打错不前进，计一滴墨渍：羊皮纸上那个词抖一下、溅开一团墨迹；画里笔尖甩出墨点，法阵光轮闪红，渡鸦一惊。
- 抄完按墨渍评级：无瑕 / 成卷 / 废卷。废卷当场哑火冒烟；成卷和无瑕的卷轴卷起来，飞进窗下的卷轴柜。
- 卷轴柜一开始是空的，最多放 18 卷，按学派系不同颜色的绳（塑能红、防护蓝、咒法绿），无瑕的卷轴带金边。点柜里的卷轴或下方「卷轴匣」里的「展开施放」，卷轴飞到希娜手上，法术在画里放出来，卷轴随之用掉。点柜子的空处跳到卷轴匣。卷轴匣和最佳成绩只存在当前浏览器里。
- 无瑕的卷轴施放时，手上多一层金色光芒、两圈金色法阵和一阵金屑，法术本身也放大约 1.4 倍、停留更久。每道法术都带本色的柔光和全画面染色（火橙、力场紫、护盾蓝、雾银、反制先红后金）。
- 施放时希娜手边升起一张红字符纸，烧成一圈小法阵，法术从那里放出：火焰箭的火舌和火球术飞出窗外炸开（冲击波、火星、烟），魔法飞弹三道带尾迹的力场镖，护盾术展开六边形屏障和四圈涟漪，迷踪步在银雾和闪光里隐去再现，法术反制用金环击碎窗外的敌方法印。
- 抄写中途随时可以「弃卷」；墨渍超出允许数目时会提示这一卷注定是废卷。
- 调试：点抄写台下的「调试」按钮（或在链接后加 `#debug`）打开调试面板，可以把卷轴柜加满、清空，或不抄写直接试放任一法术（可选按无瑕施放）。面板开着与否记在当前浏览器里。
- 规格卡：环阶、学派、工期与花费（《珊纳萨的万事指南》卷轴抄写规则）、卷轴的豁免 DC 与攻击加值（《城主指南》）。
- 输入用隐藏的输入框接收，手机也能弹出键盘；检测到中文输入法组字时提示切换到英文。
- 和《林间夜曲》一样：画面滚出视口后变成可拖动的小窗；声音用 Web Audio 合成（笔尖沙沙声、词尾铃声、各法术音效）。
