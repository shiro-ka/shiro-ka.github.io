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


def scan(suisou_root: Path) -> dict:
    files = sorted((suisou_root / "pages" / "ui").glob("*.css"))
    palette = suisou_root / "pages" / "palette.css"
    if palette.exists():
        files.append(palette)
    if not files:
        sys.exit(f"Suisou の css が見つからない: {suisou_root}")

    attrs: set[str] = set()
    values: dict[str, set[str]] = {}

    for f in files:
        text = f.read_text(encoding="utf-8")
        for name in ATTR.findall(text):
            if name:
                attrs.add(name)
        for name, raw in VAL.findall(text):
            for v in raw.split():
                # 仕様書中のプレースホルダ（"…"）は語彙ではない
                if v and v != "…":
                    values.setdefault(v, set()).add(name)

    return {
        "source": str(suisou_root),
        "files": [f.name for f in files],
        "attrs": sorted(attrs),
        "values": {k: sorted(v) for k, v in sorted(values.items())},
    }


def main() -> None:
    root = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "dev" / "Suisou"
    vocab = scan(root)
    out = Path(__file__).resolve().parent.parent / "vocab.json"
    out.write_text(json.dumps(vocab, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ambiguous = {k: v for k, v in vocab["values"].items() if len(v) > 1}
    print(f"属性 {len(vocab['attrs'])} 個 / 値 {len(vocab['values'])} 個 → {out}")
    print(f"ぶつかる値 {len(ambiguous)} 個: " + " ".join(sorted(ambiguous)))


if __name__ == "__main__":
    main()
