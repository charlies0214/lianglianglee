import os
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent
OUTPUT_HTML = ROOT / "index.html"
OUTPUT_JSON = ROOT / "index-data.json"

def collect_entries():
    print("📁 正在扫描目录...")
    tree = {}

    for root, dirs, files in os.walk(ROOT):
        root_path = Path(root)
        rel_root = root_path.relative_to(ROOT).as_posix()
        for file in files:
            if file.endswith(".html") and file != "index.html":
                rel_path = (root_path / file).relative_to(ROOT).as_posix()
                parts = rel_path.split("/")
                current = tree
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = rel_path

    print("✅ 文件结构采集完成，正在写入 index-data.json 和 index.html")
    return tree

def write_json(data):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_html():
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>📚 我的笔记索引</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: sans-serif; margin: 0; display: flex; }}
    nav {{ width: 300px; height: 100vh; overflow-y: auto; background: #f2f2f2; padding: 1rem; }}
    #preview {{ flex: 1; padding: 2rem; overflow-y: auto; }}
    ul {{ list-style: none; padding-left: 1rem; }}
    li {{ margin: 0.3rem 0; }}
    a {{ text-decoration: none; color: #0366d6; }}
    a:hover {{ text-decoration: underline; }}
    summary {{ cursor: pointer; font-weight: bold; }}
    .active {{ font-weight: bold; color: #d6336c; }}
    input {{ width: 100%; margin: 1rem 0; padding: 0.5rem; }}
  </style>
</head>
<body>
  <nav>
    <h2>📚 我的笔记索引</h2>
    <input type="text" placeholder="🔍 输入关键词搜索..." oninput="filterTree(this.value)">
    <div id="tree"></div>
  </nav>
  <div id="preview">📄 点击左侧文件以加载页面内容...</div>

  <script>
    async function loadData() {{
      const basePath = location.pathname.endsWith('/') ? location.pathname : location.pathname.replace(/[^/]+$/, '');
      const res = await fetch(basePath + 'index-data.json');
      const tree = await res.json();
      buildTree(tree, document.getElementById('tree'));
    }}

    function buildTree(obj, container) {{
      const ul = document.createElement('ul');
      for (const key in obj) {{
        const li = document.createElement('li');
        if (typeof obj[key] === 'string') {{
          const a = document.createElement('a');
          a.textContent = key;
          a.href = '#' + obj[key];
          a.onclick = e => {{
            e.preventDefault();
            loadPreview(obj[key]);
            highlightActiveLink(obj[key]);
          }};
          li.appendChild(a);
        }} else {{
          const details = document.createElement('details');
          const summary = document.createElement('summary');
          summary.textContent = key;
          details.appendChild(summary);
          buildTree(obj[key], details);
          li.appendChild(details);
        }}
        ul.appendChild(li);
      }}
      container.appendChild(ul);
    }}

    function loadPreview(path) {{
      fetch(path)
        .then(res => res.text())
        .then(html => {{
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const body = doc.querySelector('body');
          document.getElementById('preview').innerHTML = body ? body.innerHTML : html;
          window.scrollTo(0, 0);
        }});
    }}

    function highlightActiveLink(path) {{
      document.querySelectorAll('nav a').forEach(a => {{
        a.classList.toggle('active', a.getAttribute('href') === '#' + path);
      }});
    }}

    function filterTree(query) {{
      query = query.toLowerCase();
      document.querySelectorAll('nav li').forEach(li => {{
        const text = li.textContent.toLowerCase();
        li.style.display = text.includes(query) ? '' : 'none';
      }});
    }}

    // 初始化
    window.addEventListener('DOMContentLoaded', () => {{
      loadData();
      if (location.hash.length > 1) {{
        const path = decodeURIComponent(location.hash.slice(1));
        loadPreview(path);
        highlightActiveLink(path);
      }}
      window.addEventListener('hashchange', () => {{
        const path = decodeURIComponent(location.hash.slice(1));
        loadPreview(path);
        highlightActiveLink(path);
      }});
    }});
  </script>
</body>
</html>
"""
    OUTPUT_HTML.write_text(html, encoding="utf-8")

def main():
    data = collect_entries()
    write_json(data)
    write_html()
    print("✅ 所有文件已生成")

if __name__ == "__main__":
    main()
