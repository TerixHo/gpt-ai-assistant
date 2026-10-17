#!/usr/bin/env python3
"""重新產生全部音效與歡呼語音（不含配樂）。保留這個入口是為了相容舊的說明文件。

用法：
    python3 tools/audio/generate_audio.py [輸出資料夾]
實際內容在 generate_sfx.py（音效）與 voice.py（共振峰語音）；配樂見 generate_music.py。
"""
import sys
from pathlib import Path

import generate_sfx

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    generate_sfx.main_all(Path(args[0]) if args else Path(__file__).resolve().parents[2] / "godot" / "assets" / "audio")
