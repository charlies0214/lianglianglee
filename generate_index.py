import os
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent
OUTPUT = ROOT / "index.html"
ICON = "📄"

def collect_entries():
    html_files = []
    for root, dirs, files in os.walk(ROOT):
        root_path = Path(root)
        for file in files:
            if file.endswith(".html") and file != "index.html":
                file_path = root_path / file
                rel_path = file_path.relative_to(ROOT).as_posix()
                html_files.append(rel_path)
    return sorted(html_files)

def build_index(entries):
    lines = [
        "<!DOCTYPE html>",
        "<html lang='zh'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>📚 我的笔记索引</title>",
        "  <style>",
        "    body { font-family: sans-serif; padding: 2rem; background: #f9f9f9; }",
        "    ul { list-style: none; padding-left: 1rem; }",
        "    li { margin: 0.4rem 0; }",
        "    a { text-decoration: none; color: #0366d6; }",
        "    a:hover { text-decoration: underline; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>📚 我的笔记索引</h1>",
        "  <ul>"
    ]

    for path in entries:
        display = escape(path)
        lines.append(f"    <li>{ICON} <a href='{path}'>{display}</a></li>")

    lines += [
        "  </ul>",
        "</body>",
        "</html>"
    ]

    return "\n".join(lines)

def main():
    entries = collect_entries()
    html = build_index(entries)
    OUTPUT.write_text(html, encoding='utf-8')
    print(f"✅ index.html 已生成，共 {len(entries)} 项")

if __name__ == "__main__":
    main()
