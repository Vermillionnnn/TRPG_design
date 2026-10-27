"""Build the standalone release page from the artifact source.

The artifact source (scribe-scroll.html) is page content only: the artifact
viewer wraps it in a document with a doctype, a viewport and a small reset.
A copy sent on its own needs that wrapper itself, so this script adds it.

    python3 html/scribe-scroll/tools/build_release.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'scribe-scroll.html'
OUT = ROOT / 'scribe-scroll-release.html'

src = SRC.read_text(encoding='utf-8')
title = re.search(r'<title>(.*?)</title>', src).group(1)
style = re.search(r'<style>.*?</style>', src, re.S).group(0)
body = src[src.index(style) + len(style):].strip()

# the same reset the artifact viewer puts around the page
RESET = """<style>
:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
img{max-width:100%}
[hidden]{display:none!important}
</style>"""

page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="仿中世纪湿壁画：书士会法师希娜·露弥在烛堡书库抄写法术卷轴。逐词打字抄完一卷，卷轴收进卷轴柜，取出施放时法术在画里放出来。">
<title>{title}</title>
{RESET}
{style}
</head>
<body>
{body}
</body>
</html>
"""
OUT.write_text(page, encoding='utf-8')
print(f'wrote {OUT.name}: {len(page.encode("utf-8"))} bytes')
