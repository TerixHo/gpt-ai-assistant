"""下載觸控按鈕圖示：Iconify 的 Tabler Icons（MIT 授權），輸出白色 SVG 到 godot/assets/ui/icons/。

Iconify 的線上 API 在本開發環境被網路政策擋住，所以改從 npm 套件庫下載 Iconify 官方發佈的
@iconify-json/tabler 圖示集（內容與 API 相同），解出需要的圖示。

用法：python3 tools/ui/fetch_icons.py
輸出：godot/assets/ui/icons/<用途>.svg 與 ICON-CREDITS.txt（授權聲明，MIT 要求保留）。
"""
import io
import json
import tarfile
import urllib.request
from pathlib import Path

PACKAGE_URL = "https://registry.npmjs.org/@iconify-json/tabler/-/tabler-1.2.42.tgz"
OUT = Path(__file__).resolve().parents[2] / "godot" / "assets" / "ui" / "icons"
# 用途 -> Tabler 圖示名稱
ICONS = {
    "jump": "arrow-big-up-lines-filled",
    "turn": "arrow-back-up",
    "look": "binoculars-filled",
    "view": "camera-rotate",
    "pause": "player-pause-filled",
    "rescue": "home-filled",
    "charge": "flame-filled",
    "tap": "hand-click",
    "swipe": "hand-finger",
    "move": "hand-move",
}
# 匯入 Godot 時的點陣大小（像素）；按鈕最大約 90 像素，畫成 128 才清楚
PIXELS = 128


def main():
    with urllib.request.urlopen(PACKAGE_URL, timeout=60) as r:
        data = r.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        icons = json.load(tar.extractfile("package/icons.json"))
        info = json.load(tar.extractfile("package/info.json"))
    size = icons.get("width", 24)
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name in ICONS.items():
        icon = icons["icons"].get(name)
        if icon is None:
            raise SystemExit(f"找不到圖示 {name}（Tabler {info.get('version')}）")
        body = icon["body"].replace("currentColor", "#ffffff")
        w = icon.get("width", size)
        h = icon.get("height", size)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{PIXELS}" height="{PIXELS}" '
               f'viewBox="0 0 {w} {h}">{body}</svg>\n')
        (OUT / f"{key}.svg").write_text(svg, encoding="utf-8")
        print(f"[icons] {key}.svg ← tabler:{name}")
    lic = info.get("license", {})
    author = info.get("author", {})
    credits = (
        "觸控按鈕圖示來源\n\n"
        f"Tabler Icons {info.get('version')}（經 Iconify 圖示集 @iconify-json/tabler 1.2.42 取得）\n"
        f"作者：{author.get('name')}　{author.get('url')}\n"
        f"授權：{lic.get('title')}　{lic.get('url')}\n\n"
        "使用的圖示：\n" + "\n".join(f"  {k}: tabler:{v}" for k, v in ICONS.items()) + "\n\n"
        "以下授權全文取自 https://raw.githubusercontent.com/tabler/tabler-icons/main/LICENSE\n\n"
        "MIT License\n\n"
        "Copyright (c) 2020-2026 Paweł Kuna\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and "
        "associated documentation files (the \"Software\"), to deal in the Software without restriction, including "
        "without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
        "copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the "
        "following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all copies or substantial "
        "portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT "
        "LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO "
        "EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER "
        "IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR "
        "THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n"
    )
    (OUT / "ICON-CREDITS.txt").write_text(credits, encoding="utf-8")


if __name__ == "__main__":
    main()
