"""把 Godot 網頁版匯出結果包成可以發布的資料夾。

用途：發布平台單一檔案有大小上限（約 15MB），而 Godot 引擎主程式（.wasm）與遊戲資料包（.pck）
可能超過。這個腳本把兩者用 gzip 壓縮、切成小段，產生載入頁（shell_template.html），
載入頁在瀏覽器裡把分段接回並解壓，引擎本身不需要修改。

用法：
    python3 tools/web/package_web.py <Godot 匯出資料夾> <輸出資料夾> [--part-mb 12]

輸出：
    index.html        給發布平台用的頁面片段（平台會自動補上 html、head、body）
    local_test.html   完整的 HTML 文件，給本機瀏覽器測試用
    index.js、*.worklet.js、*.gzN.wasm 分段檔
"""

import argparse
import gzip
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIG_FILES = ("index.wasm", "index.pck")
COPY_FILES = ("index.js", "index.audio.worklet.js", "index.audio.position.worklet.js")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--part-mb", type=float, default=12.0)
    args = ap.parse_args()
    src = Path(args.export_dir)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    part_size = int(args.part_mb * 1024 * 1024)

    exported_html = (src / "index.html").read_text(encoding="utf-8")
    m = re.search(r"const GODOT_CONFIG = (\{.*?\});", exported_html, re.S)
    if not m:
        raise SystemExit("在匯出的 index.html 裡找不到 GODOT_CONFIG")
    config = json.loads(m.group(1))

    chunks = {}
    total = 0
    for name in BIG_FILES:
        raw = (src / name).read_bytes()
        packed = gzip.compress(raw, compresslevel=9, mtime=0)
        parts = []
        for i in range(0, len(packed), part_size):
            # 發布平台只供應特定副檔名；分段一律用 .wasm 結尾（載入頁是讀原始位元組再自己解壓，不看檔案類型）
            part_name = f"{name}.gz{i // part_size}.wasm"
            (out / part_name).write_bytes(packed[i:i + part_size])
            parts.append(part_name)
        chunks[name] = {"parts": parts, "size": len(raw)}
        total += len(packed)
        print(f"{name}: 原始 {len(raw) / 1048576:.1f}MB，壓縮後 {len(packed) / 1048576:.1f}MB，分 {len(parts)} 段")

    for name in COPY_FILES:
        if (src / name).exists():
            shutil.copy2(src / name, out / name)
            total += (src / name).stat().st_size
        else:
            print(f"注意：匯出資料夾沒有 {name}")

    shell = (HERE / "shell_template.html").read_text(encoding="utf-8")
    page = (shell
            .replace("__CHUNKS__", json.dumps(chunks, ensure_ascii=False))
            .replace("__GODOT_CONFIG__", json.dumps(config, ensure_ascii=False))
            .replace("__TOTAL_MB__", f"{total / 1048576:.0f}"))
    (out / "index.html").write_text(page, encoding="utf-8")
    local = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
             '<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n'
             + page + "\n</body>\n</html>\n")
    (out / "local_test.html").write_text(local, encoding="utf-8")
    print(f"完成：{out}，下載總量約 {total / 1048576:.1f}MB")


if __name__ == "__main__":
    main()
