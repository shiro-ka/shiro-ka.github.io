#!/usr/bin/env python3
"""Suisou の CSS から語彙表を作る。

語彙表を手で持たないための道具。Suisou は破壊的変更がありうるので、
対応表を人間が書くと必ずずれる。真実の源泉は Suisou の CSS 側だけにする。

    python3 tools/gen_vocab.py ~/dev/Suisou

出力は vocab.json（このブランチにコミットする）。
ビルド時には Suisou を見に行かない ―― あちらの事故でサイトのビルドを止めないため。
更新したいときだけ、手でこれを走らせる。
"""
import json
import re
import sys
from pathlib import Path

ATTR = re.compile(r'data-suisou-([a-z-]+)')
# data-suisou-btn~="outline"  /  data-suisou-surface="panel bare"
VAL = re.compile(r'data-suisou-([a-z-]+)\s*[~|^$*]?=\s*"([^"]*)"')
# layout の値のうち、display / flex-direction を敷くもの＝「モード」。
# 自前 grid と同居できないのはこれだけで、screen や container のような
# ふるまいの語は同居できる。手で表を持たず CSS から判定する。
MODE = re.compile(r'\[data-suisou-layout~="([^"]+)"\]\s*\{([^}]*)\}')

# Suisou が「見づらい」と印を付けた組。印の形式は変えないと約束されている
DISCOURAGED = re.compile(
    r'/\*\s*★推奨しない[^*]*\*/\s*'
    r'\[data-suisou-theme="([a-z]+)"\]\[data-suisou-accent="([a-z]+)"\]')


def scan(suisou_root: Path) -> dict:
    files = sorted((suisou_root / "pages" / "ui").glob("*.css"))
    palette = suisou_root / "pages" / "palette.css"
    if palette.exists():
        files.append(palette)
    if not files:
        sys.exit(f"Suisou の css が見つからない: {suisou_root}")

    attrs: set[str] = set()
    values: dict[str, set[str]] = {}
    root_attrs: set[str] = set()      # palette.css 由来 ＝ html 要素に付くもの

    for f in files:
        text = f.read_text(encoding="utf-8")
        for name in ATTR.findall(text):
            if name:
                attrs.add(name)
                if f.name == "palette.css":
                    root_attrs.add(name)
        for name, raw in VAL.findall(text):
            for v in raw.split():
                # 仕様書中のプレースホルダ（"…"）は語彙ではない
                if v and v != "…":
                    values.setdefault(v, set()).add(name)

    modes: set[str] = set()
    layout = suisou_root / "pages" / "ui" / "layout.css"
    if layout.exists():
        for value, block in MODE.findall(layout.read_text(encoding="utf-8")):
            if "display:" in block or "flex-direction:" in block:
                modes.add(value)

    discouraged = []
    if palette.exists():
        text = palette.read_text(encoding="utf-8")
        for theme, accent in DISCOURAGED.findall(text):
            discouraged.append([theme, accent])

    return {
        "source": str(suisou_root),
        "files": [f.name for f in files],
        "attrs": sorted(attrs),
        "root_attrs": sorted(root_attrs),
        "discouraged": sorted(discouraged),
        "layout_modes": sorted(modes),
        "values": {k: sorted(v) for k, v in sorted(values.items())},
    }


def main() -> None:
    root = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "dev" / "Suisou"
    vocab = scan(root)
    out = Path(__file__).resolve().parent.parent / "vocab.json"
    out.write_text(json.dumps(vocab, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ambiguous = {k: v for k, v in vocab["values"].items() if len(v) > 1}
    print(f"属性 {len(vocab['attrs'])} 個 / 値 {len(vocab['values'])} 個 → {out}")
    print(f"html に付く属性: {' '.join(vocab['root_attrs'])}")
    print(f"ぶつかる値 {len(ambiguous)} 個: " + " ".join(sorted(ambiguous)))
    print("自前 grid と同居できない語: " + " ".join(vocab["layout_modes"]))
    if d := vocab["discouraged"]:
        print("推奨しない組: " + " ".join(f"{t}×{a}" for t, a in d))


if __name__ == "__main__":
    main()
