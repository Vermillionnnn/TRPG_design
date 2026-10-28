# 武器陈列

三件武器的 Blender 模型，摆在深色展台上的陈列场景。三件武器都做成了 [`scenes/assets/`](../assets/) 里的素材，其他场景可以直接 `import`。

![三件武器](weapons_all.png)

| 特写 | | |
| --- | --- | --- |
| <img src="weapons_rapier.png" width="260"> | <img src="weapons_staff.png" width="260"> | <img src="weapons_lute.png" width="260"> |
| 宝石刺剑 `gem_rapier` | 藤蔓法杖 `vine_staff` | 魔法鲁特琴 `magic_lute` |

## 三件武器

- **宝石刺剑**（[`gem_rapier`](../assets/gem_rapier.py)）：照设计者提供的角色图和握剑细节图做。剑身是近乎无色的透明水晶，截面是压扁的六边形，切面平整，带薄膜干涉和色散；晶体里散落着几百颗蓝、青、粉、橙、绿、紫的小光点，透过玻璃看像宝石内部的火彩。剑身从剑根往剑尖一路变细。剑根是一段同样带光点的水晶座：先像花瓶一样张开到尖锐的肩，收腰，再鼓成一颗菱形，然后接进剑身，底下立在一圈很薄的金环里。护手是一块厚重的金件，侧面看是上下两个梯形底对底：上半从较窄的平顶向下斜着张开到一圈锋利的圆边，前后左右完全对称；下半从边缘斜着收进一段套着四道细环的金色细颈，细颈直接接在握柄上。护指弓是一条扁金带，从护手前方长出来：它的上沿接着护手上半的斜面继续往外延伸，再顺势弯下绕过握柄，一路收细，在剑首上方绕一个小圆圈，再顺势收进剑首上的金箍，和握柄连成一体。握柄是一根加粗的长金柄，略呈纺锤形，最粗处在细颈下方不远，往下慢慢收细到剑首；剑首是两段叠起来的六面菱形金饰，下面一段是尖头，上面套一个带四根卷爪的金箍。全长约 1.25 米。
- **藤蔓法杖**（[`vine_staff`](../assets/vine_staff.py)）：微微弯曲、带树瘤的深色木杖，越往上越粗。杖顶鼓成一个木杯，蓝色六棱水晶的下半截嵌在杯里，杯沿冒出三片小碎晶。木杯外侧长出五根卷须，远远绕开水晶向外鼓起，再在水晶尖上方收拢卷回。三条藤蔓各不相同：一条粗的主藤从中段绕上来，越往上叶子越密，开着发蓝光的花苞，最后爬进杖头；一条细的木质老藤在下半截绕得很紧，只有稀疏的小叶，末端卷离杖身；一条嫩绿的短藤在上段松松绕一圈。木杯下有一圈叶子。杖身约 1.55 米，加杖头约 1.85 米。
- **魔法鲁特琴**（[`magic_lute`](../assets/magic_lute.py)）：梨形琴身，背面是深浅交替的 11 条木板；云杉面板，金色镶边。音孔是一圈发光的符文玫瑰窗（六芒星、内圈光环、外圈符文点，金色外环）。琴颈上有金色品丝，琴头向后折，两侧插着琴轸，末端是金托上的一颗蓝水晶。六根琴弦发青光，旁边飘着几个发光的音符。琴身长 0.48 米。

三件统一用参考图里的配色：白、金、深蓝和水晶蓝。

## 用法

本地配置 Blender 的方法见 [`scenes/ENVIRONMENT_SETUP.md`](../ENVIRONMENT_SETUP.md)。

```bash
scenes/blender.sh scenes/weapons/build_scene.py --render out/weapons.png --shot all
```

参数：

- `--shot all|rapier|staff|lute`：三件合影 / 刺剑护手特写 / 法杖杖头特写 / 鲁特琴
- `--samples N`：渲染采样数（默认 128）
- `--res 百分比`：渲染分辨率百分比（合影 1600×1200，特写 1000×1200）
- `--save out.blend`：保存为 `.blend` 文件

在其他场景里使用：

```python
from assets import gem_rapier, magic_lute, vine_staff

r = gem_rapier.build("Rapier", loc=(0, 0, 1.25))
r.rotation_euler = (math.radians(180), 0, 0)          # 剑尖朝下
vine_staff.build("Staff", loc=(1, 0, 0), tendrils=4, crystal_color="arcane_purple")
magic_lute.build("Lute", loc=(2, 0, 0), notes=0, glow=(1.0, 0.6, 0.2))   # 不要音符，琴弦发暖光
```

各素材的参数见 [`scenes/assets/README.md`](../assets/README.md)。

| 文件 | 说明 |
| --- | --- |
| `build_scene.py` | 陈列场景：圆形石台、深蓝渐变背景、三盏面光，武器从素材库引用 |
| `weapons_all.png` | 三件合影（1600×1200，128 采样） |
| `weapons_rapier.png` | 刺剑护手特写（1000×1200） |
| `weapons_staff.png` | 法杖杖头特写（1000×1200） |
| `weapons_lute.png` | 鲁特琴（1000×1200） |
