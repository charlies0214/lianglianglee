import os
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent.resolve()
OUTPUT_HTML = ROOT / "index.html"
OUTPUT_JSON = ROOT / "index-data.json"

def scan_directory(path: Path):
    tree = {}
    for item in sorted(path.iterdir()):
        if item.name in [".git", ".github", "node_modules"]:
            continue
        if item.is_dir():
            subtree = scan_directory(item)
            if subtree:
                tree[item.name] = subtree
        elif item.suffix == ".html" and item.name != "index.html":
            tree[item.name] = str(item.relative_to(ROOT)).replace("\\", "/")
    return tree

def write_json(tree):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)

def write_html():
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>📚 我的笔记索引</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.css">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 0; padding: 0;
      display: flex; height: 100vh; overflow: hidden;
    }}
    #sidebar {{
      width: 320px; padding: 1rem; overflow-y: auto;
      background: var(--bg); border-right: 1px solid #ccc;
    }}
    #main {{
      flex: 1; padding: 2rem; overflow-y: auto;
      background: var(--bg-alt);
    }}
    h1 {{ margin-top: 0; }}
    .folder > summary {{ font-weight: bold; cursor: pointer; }}
    .dark {{
      --bg: #111;
      --bg-alt: #181818;
      --fg: #eee;
    }}
    .light {{
      --bg: #fff;
      --bg-alt: #f9f9f9;
      --fg: #222;
    }}
    body {{
      background: var(--bg);
      color: var(--fg);
    }}
    a {{ color: #3b82f6; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .search-box {{
      margin-bottom: 1rem;
    }}
    .active {{
      font-weight: bold;
      color: #16a34a;
    }}
    summary::marker {{
      color: #999;
    }}
    .theme-toggle {{
      cursor: pointer;
      font-size: 0.9rem;
      margin-bottom: 1rem;
    }}
  </style>
</head>
<body class="light">
  <div id="sidebar">
    <div class="theme-toggle">🌗 切换主题</div>
    <div class="search-box">
      <input type="text" id="search" placeholder="🔍 输入关键词搜索..." style="width:100%; padding:0.5rem;" />
    </div>
    <div id="tree">📁 正在加载目录...</div>
  </div>
  <div id="main">
    <h1>📚 我的笔记索引</h1>
    <div id="preview">点击左侧目录查看内容</div>
  </div>
  <script>
    const treeEl = document.getElementById('tree');
    const previewEl = document.getElementById('preview');
    const searchEl = document.getElementById('search');

    function createNode(name, value) {{
      if (typeof value === 'string') {{
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#' + value;
        a.textContent = name;
        li.appendChild(a);
        return li;
      }} else {{
        const details = document.createElement('details');
        details.classList.add('folder');
        const summary = document.createElement('summary');
        summary.textContent = name;
        details.appendChild(summary);
        const ul = document.createElement('ul');
        for (const [k, v] of Object.entries(value)) {{
          ul.appendChild(createNode(k, v));
        }}
        details.appendChild(ul);
        return details;
      }}
    }}

    function buildTree(data, keyword = '') {{
      treeEl.innerHTML = '';
      for (const [k, v] of Object.entries(data)) {{
        const node = createNode(k, v);
        if (keyword === '' || node.textContent.toLowerCase().includes(keyword.toLowerCase())) {{
          treeEl.appendChild(node);
        }}
      }}
    }}

    function getIndexJsonUrl() {{
      const parts = location.pathname.split('/');
      const base = parts.slice(0, parts.indexOf('index.html')).join('/');
      return base + '/index-data.json';
    }}

    async function init() {{
      const res = await fetch(getIndexJsonUrl());
      const data = await res.json();
      buildTree(data);

      if (location.hash) {{
        const path = decodeURIComponent(location.hash.slice(1));
        loadPage(path);
      }}
    }}

    async function loadPage(path) {{
      const res = await fetch(path);
      let text = await res.text();
      if (path.endsWith('.md') || path.includes('.md.html')) {{
        if (window.marked) {{
          text = marked.parse(text);
        }}
      }}
      previewEl.innerHTML = text;
      document.querySelectorAll('#tree a').forEach(a => {{
        a.classList.toggle('active', a.getAttribute('href') === '#' + path);
      }});
    }}

    searchEl.addEventListener('input', e => {{
      init(); // 重建树
    }});

    window.addEventListener('hashchange', () => {{
      const path = decodeURIComponent(location.hash.slice(1));
      loadPage(path);
    }});

    document.querySelector('.theme-toggle').onclick = () => {{
      document.body.classList.toggle('dark');
      document.body.classList.toggle('light');
    }};

    init();

    import('https://cdn.jsdelivr.net/npm/marked/marked.min.js').then(() => {{
      if (location.hash) {{
        const path = decodeURIComponent(location.hash.slice(1));
        loadPage(path);
      }}
    }});
  </script>
</body>
</html>
"""
    OUTPUT_HTML.write_text(html, encoding="utf-8")

def main():
    print("📁 正在扫描目录...")
    tree = scan_directory(ROOT)
    print("✅ 文件结构采集完成，正在写入 index-data.json 和 index.html")
    write_json(tree)
    write_html()
    print("✅ 目录已生成！")

if __name__ == "__main__":
    main()
