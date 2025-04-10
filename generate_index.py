import os
import json
from pathlib import Path
from urllib.parse import quote

# 配置
IGNORE_DIRS = {'.git', 'scripts', 'static', '.github', 'cdn-cgi', '.vscode', '__pycache__'}
ROOT_PATH = '.'
OUTPUT_JSON = 'index-data.json'
OUTPUT_HTML = 'index.html'

# 工具函数：收集有效文件（只收集.md.html）
def collect_files(base_path):
    file_tree = {}

    for root, dirs, files in os.walk(base_path):
        # 排除无关目录
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        rel_root = os.path.relpath(root, base_path)
        tree = file_tree
        if rel_root != '.':
            for part in rel_root.split(os.sep):
                tree = tree.setdefault(part, {})

        for file in sorted(files):
            if file.endswith('.md.html'):
                tree[file] = os.path.join(rel_root, file).replace("\\", "/")

    return file_tree

# 生成 index-data.json
def write_json(data):
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 生成 index.html：主结构模板 + 动态加载逻辑
def write_html():
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>📚 我的笔记索引</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/spectre.css/dist/spectre.min.css">
  <style>
    body {{ display: flex; margin: 0; font-family: system-ui; }}
    #sidebar {{ width: 300px; height: 100vh; overflow-y: auto; border-right: 1px solid #ddd; padding: 1rem; }}
    #content {{ flex: 1; padding: 2rem; overflow-y: auto; height: 100vh; }}
    .folder {{ font-weight: bold; cursor: pointer; padding: 0.3rem 0; color: #333; }}
    .file {{ cursor: pointer; display: block; padding: 0.2rem 0; text-decoration: none; color: #333; margin-left: 1rem; }}
    .file:hover, .folder:hover {{ text-decoration: underline; }}
    .active {{ color: #0070f3 !important; font-weight: bold; }}
    .hidden {{ display: none; }}
    .directory-content {{ margin-top: 1rem; }}
    .directory-content .file {{ margin-left: 0; display: block; }}
    .directory-item {{ display: block; padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0; }}
    .search-result {{ margin-top: 0.5rem; }}
    .search-highlight {{ background-color: #ffeb3b; }}
    .breadcrumb {{ margin-bottom: 1.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 3px; }}
    h1, h2, h3, h4 {{ margin-top: 0; }}
    ul.simple-list {{ list-style: none; padding: 0; margin: 0; }}
    ul.simple-list li {{ padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0; }}
    ul.simple-list li:last-child {{ border-bottom: none; }}
    ul.simple-list a {{ display: block; text-decoration: none; color: #333; }}
    ul.simple-list a:hover {{ text-decoration: underline; }}
    #tree .folder:before {{ content: "📁 "; }}
    #tree .file:before {{ content: "📄 "; }}
    .directory-item.folder:before {{ content: "📁 "; }}
    .directory-item.file:before {{ content: "📄 "; }}
    #search-results .search-result-title {{ margin: 1rem 0; font-weight: bold; }}
    /* 响应式设计 */
    @media (max-width: 768px) {{
      body {{ flex-direction: column; }}
      #sidebar {{ width: 100%; height: auto; max-height: 40vh; }}
      #content {{ height: auto; }}
    }}
  </style>
</head>
<body>
  <div id="sidebar">
    <h4>📚 我的笔记索引</h4>
    <input type="text" id="search" placeholder="🔍 输入关键词搜索..." class="input" />
    <div id="search-results" class="hidden"></div>
    <div id="tree"></div>
  </div>
  <div id="content"><p>← 从左侧选择一个文件开始阅读</p></div>

  <script>
    // 全局变量存储文件数据
    let fileData = {{}};
    let allFiles = [];
    let currentPath = '';
    
    async function loadTree() {{
      const res = await fetch(new URL('index-data.json', window.location).href);
      const data = await res.json();
      fileData = data;
      const tree = document.getElementById('tree');
      
      // 收集所有文件路径用于搜索
      collectAllFiles(data, '');
      
      function renderTree(obj, parentEl) {{
        // 创建目录列表
        const list = document.createElement('ul');
        list.className = 'simple-list';
        
        // 对象的键进行排序，确保目录在文件前面
        const keys = Object.keys(obj).sort((a, b) => {{
          const aIsDir = typeof obj[a] === 'object';
          const bIsDir = typeof obj[b] === 'object';
          if (aIsDir && !bIsDir) return -1;
          if (!aIsDir && bIsDir) return 1;
          return a.localeCompare(b);
        }});
        
        for (const key of keys) {{
          const value = obj[key];
          const item = document.createElement('li');
          
          if (typeof value === 'string') {{
            // 文件项
            const a = document.createElement('a');
            a.textContent = key.replace('.md.html', '');
            a.className = 'file';
            a.href = '#' + value;
            a.setAttribute('data-path', value);
            a.onclick = e => {{
              e.preventDefault();
              loadContent(value);
              document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
              a.classList.add('active');
              currentPath = value;
            }};
            item.appendChild(a);
          }} else if (typeof value === 'object' && key !== 'assets') {{
            // 目录项
            const folderLink = document.createElement('a');
            folderLink.textContent = key;
            folderLink.className = 'folder';
            folderLink.href = '#folder:' + key;
            
            // 目录点击行为 - 不再展开子目录，直接在右侧显示内容
            folderLink.onclick = function(e) {{
              e.preventDefault();
              document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
              folderLink.classList.add('active');
              
              // 在右侧内容区域显示目录内容列表
              showDirectoryContent(key, value, key);
            }};
            
            item.appendChild(folderLink);
          }}
          
          list.appendChild(item);
        }}
        
        parentEl.appendChild(list);
      }}

      // 清空树并重新渲染
      tree.innerHTML = '';
      renderTree(data, tree);

      // 如果 hash 存在就直接加载
      if (window.location.hash) {{
        const hash = decodeURIComponent(window.location.hash.slice(1));
        if (hash.startsWith('folder:')) {{
          // 处理目录哈希
          const folderPath = hash.substring(7);
          const parts = folderPath.split('/');
          let current = data;
          
          // 逐级查找目录
          for (const part of parts) {{
            if (current[part] && typeof current[part] === 'object') {{
              current = current[part];
            }} else {{
              break;
            }}
          }}
          
          // 显示该目录内容
          showDirectoryContent(parts[parts.length-1], current, folderPath);
          
          // 高亮左侧对应的目录
          const folderEl = document.querySelector(`.folder[href="#folder:${{parts[0]}}"]`);
          if (folderEl) {{
            document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
            folderEl.classList.add('active');
          }}
        }} else {{
          // 处理文件哈希
          loadContent(hash);
          
          // 尝试高亮左侧对应的文件或目录
          const filePath = hash.split('/');
          if (filePath.length > 1) {{
            const topLevelDir = filePath[0];
            const folderEl = document.querySelector(`.folder[href="#folder:${{topLevelDir}}"]`);
            if (folderEl) {{
              document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
              folderEl.classList.add('active');
            }}
          }}
        }}
      }}
      
      // 初始化搜索功能
      initSearch();
    }}
    
    // 收集所有文件路径和名称用于搜索
    function collectAllFiles(obj, prefix) {{
      for (const key in obj) {{
        const value = obj[key];
        if (typeof value === 'string') {{
          allFiles.push({{
            name: key.replace('.md.html', ''),
            path: value,
            displayPath: prefix ? prefix + ' > ' + key.replace('.md.html', '') : key.replace('.md.html', '')
          }});
        }} else if (typeof value === 'object' && key !== 'assets') {{
          const newPrefix = prefix ? prefix + ' > ' + key : key;
          collectAllFiles(value, newPrefix);
        }}
      }}
    }}
    
    // 初始化搜索功能
    function initSearch() {{
      const searchInput = document.getElementById('search');
      const searchResults = document.getElementById('search-results');
      const tree = document.getElementById('tree');
      
      searchInput.addEventListener('input', function() {{
        const query = this.value.trim().toLowerCase();
        
        if (query.length < 2) {{
          searchResults.classList.add('hidden');
          tree.classList.remove('hidden');
          return;
        }}
        
        // 显示搜索结果，隐藏原目录树
        searchResults.classList.remove('hidden');
        tree.classList.add('hidden');
        
        // 清空之前的搜索结果
        searchResults.innerHTML = '';
        
        // 搜索匹配的文件
        const matches = allFiles.filter(file => 
          file.name.toLowerCase().includes(query) || 
          file.displayPath.toLowerCase().includes(query)
        );
        
        // 限制显示结果数量
        const limitedMatches = matches.slice(0, 30);
        
        if (limitedMatches.length > 0) {{
          // 添加搜索结果标题
          const title = document.createElement('div');
          title.textContent = `搜索结果 (共 ${{matches.length}} 项)`;
          title.className = 'search-result-title';
          searchResults.appendChild(title);
          
          // 添加搜索结果列表
          const resultList = document.createElement('ul');
          resultList.className = 'simple-list';
          
          // 添加搜索结果项
          limitedMatches.forEach(file => {{
            const item = document.createElement('li');
            const link = document.createElement('a');
            link.className = 'file search-result';
            link.href = '#' + file.path;
            
            // 高亮匹配的文本
            const highlightedText = file.displayPath.replace(
              new RegExp(query, 'gi'),
              match => `<span class="search-highlight">${{match}}</span>`
            );
            
            link.innerHTML = highlightedText;
            
            link.onclick = e => {{
              e.preventDefault();
              loadContent(file.path);
              document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
              link.classList.add('active');
              currentPath = file.path;
              
              // 重置搜索
              searchInput.value = '';
              searchResults.classList.add('hidden');
              tree.classList.remove('hidden');
            }};
            
            item.appendChild(link);
            resultList.appendChild(item);
          }});
          
          searchResults.appendChild(resultList);
        }} else {{
          searchResults.innerHTML = '<div class="search-result">没有找到匹配结果</div>';
        }}
      }});
      
      // 允许按ESC键退出搜索
      document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape' && !searchResults.classList.contains('hidden')) {{
          searchInput.value = '';
          searchResults.classList.add('hidden');
          tree.classList.remove('hidden');
        }}
      }});
    }}
    
    // 创建面包屑导航
    function createBreadcrumb(path) {{
      if (!path) return '';
      
      const parts = path.split('/');
      let html = '<div class="breadcrumb">';
      html += '<a href="#" onclick="return false;">首页</a>';
      
      let currentPath = '';
      for (let i = 0; i < parts.length; i++) {{
        currentPath += (i > 0 ? '/' : '') + parts[i];
        html += ' &gt; ';
        if (i === parts.length - 1) {{
          html += `<span>${{parts[i]}}</span>`;
        }} else {{
          html += `<a href="#folder:${{currentPath}}" onclick="return false;">${{parts[i]}}</a>`;
        }}
      }}
      
      html += '</div>';
      return html;
    }}
    
    // 显示目录内容（文件列表）
    function showDirectoryContent(dirName, dirData, fullPath = '') {{
      const container = document.getElementById('content');
      let html = createBreadcrumb(fullPath);
      html += `<h2>📁 ${{dirName}}</h2>`;
      
      // 创建文件列表
      html += '<ul class="simple-list directory-content">';
      
      // 对象的键进行排序，确保目录在文件前面
      const keys = Object.keys(dirData).sort((a, b) => {{
        const aIsDir = typeof dirData[a] === 'object';
        const bIsDir = typeof dirData[b] === 'object';
        if (aIsDir && !bIsDir) return -1;
        if (!aIsDir && bIsDir) return 1;
        return a.localeCompare(b);
      }});
      
      // 记录文件和目录数量
      let itemCount = 0;
      
      // 添加上级目录链接（如果不是根目录）
      if (fullPath && fullPath.includes('/')) {{
        const parentPath = fullPath.substring(0, fullPath.lastIndexOf('/'));
        html += `<li><a class="directory-item folder" href="#folder:${{parentPath}}" onclick="return false;">上一级</a></li>`;
      }}
      
      // 添加文件和目录列表
      for (const key of keys) {{
        if (key === 'assets') continue; // 跳过资源目录
        
        const value = dirData[key];
        itemCount++;
        
        if (typeof value === 'object') {{
          // 目录项
          const newPath = fullPath ? fullPath + '/' + key : key;
          html += `<li><a class="directory-item folder" href="#folder:${{newPath}}" onclick="return false;">${{key}}</a></li>`;
        }} else if (typeof value === 'string') {{
          // 文件项
          html += `<li><a class="directory-item file" href="#${{value}}" onclick="return false;">${{key.replace('.md.html', '')}}</a></li>`;
        }}
      }}
      
      // 如果没有文件和目录，显示提示
      if (itemCount === 0) {{
        html += '<li>该目录下没有内容</li>';
      }}
      
      html += '</ul>';
      
      // 更新URL哈希，但不触发hashchange事件
      const newUrl = '#folder:' + fullPath;
      history.replaceState(null, '', newUrl);
      
      container.innerHTML = html;
      
      // 为目录内容中的链接添加点击事件
      container.querySelectorAll('.directory-item').forEach(link => {{
        const href = link.getAttribute('href');
        
        if (href && href.startsWith('#folder:')) {{
          // 目录点击事件
          link.onclick = function(e) {{
            e.preventDefault();
            const folderPath = href.substring(8);
            const parts = folderPath.split('/');
            let current = fileData;
            
            // 逐级查找目录
            for (const part of parts) {{
              if (current[part] && typeof current[part] === 'object') {{
                current = current[part];
              }} else {{
                break;
              }}
            }}
            
            // 显示该目录内容
            showDirectoryContent(parts[parts.length-1] || '根目录', current, folderPath);
          }};
        }} else if (href && href.startsWith('#')) {{
          // 文件点击事件
          link.onclick = function(e) {{
            e.preventDefault();
            const filePath = href.substring(1);
            loadContent(filePath);
          }};
        }}
      }});
    }}

    // 调整图片路径的函数
    function adjustImagePaths(html, basePath) {{
      // 创建一个临时的DOM元素来解析HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;
      
      // 查找所有图片标签
      const images = tempDiv.querySelectorAll('img');
      images.forEach(img => {{
        const src = img.getAttribute('src');
        if (src && !src.startsWith('http') && !src.startsWith('/')) {{
          // 是相对路径，需要调整
          const baseDir = basePath.substring(0, basePath.lastIndexOf('/'));
          img.src = baseDir + '/' + src;
        }}
      }});
      
      return tempDiv.innerHTML;
    }}

    async function loadContent(path) {{
      try {{
        const res = await fetch(path);
        if (!res.ok) throw new Error(`HTTP error! status: ${{res.status}}`);
        
        const text = await res.text();
        const container = document.getElementById('content');
        
        // 提取路径部分用于面包屑导航
        const pathParts = path.split('/');
        const fileName = pathParts.pop(); // 移除文件名
        const directoryPath = pathParts.join('/');
        
        // 创建面包屑导航
        let html = createBreadcrumb(directoryPath);
        
        // 添加内容并调整图片路径
        if (path.endsWith('.md.html')) {{
          const adjustedHtml = adjustImagePaths(text, path);
          container.innerHTML = html + adjustedHtml;
        }} else {{
          container.innerHTML = html + '<pre>' + text + '</pre>';
        }}
        
        // 更新URL哈希
        window.location.hash = path;
        currentPath = path;
        
        // 回到顶部
        container.scrollTop = 0;
      }} catch (error) {{
        console.error('Error loading content:', error);
        document.getElementById('content').innerHTML = `<div class="error">加载内容出错: ${{error.message}}</div>`;
      }}
    }}

    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', loadTree);
    
    // 监听哈希变化事件
    window.addEventListener('hashchange', function() {{
      const hash = decodeURIComponent(window.location.hash.slice(1));
      if (hash.startsWith('folder:')) {{
        // 处理目录哈希
        const folderPath = hash.substring(7);
        const parts = folderPath.split('/');
        let current = fileData;
        
        // 逐级查找目录
        for (const part of parts) {{
          if (current[part] && typeof current[part] === 'object') {{
            current = current[part];
          }} else {{
            break;
          }}
        }}
        
        // 显示该目录内容
        showDirectoryContent(parts[parts.length-1] || '根目录', current, folderPath);
        
        // 高亮左侧对应的目录（只针对顶级目录）
        if (parts.length === 1) {{
          const folderEl = document.querySelector(`.folder[href="#folder:${{parts[0]}}"]`);
          if (folderEl) {{
            document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
            folderEl.classList.add('active');
          }}
        }}
      }} else if (hash && hash !== currentPath) {{
        // 处理文件哈希
        loadContent(hash);
        
        // 尝试高亮左侧对应的目录
        const filePath = hash.split('/');
        if (filePath.length > 1) {{
          const topLevelDir = filePath[0];
          const folderEl = document.querySelector(`.folder[href="#folder:${{topLevelDir}}"]`);
          if (folderEl) {{
            document.querySelectorAll('.file, .folder').forEach(el => el.classList.remove('active'));
            folderEl.classList.add('active');
          }}
        }}
      }}
    }});
  </script>
</body>
</html>
'''
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

# 主函数
def main():
    print("📁 正在扫描目录...")
    structure = collect_files(ROOT_PATH)
    print("✅ 文件结构采集完成，正在写入 index-data.json 和 index.html")
    write_json(structure)
    write_html()
    print("✅ 页面生成完毕，请部署到 Cloudflare Pages 进行访问")

if __name__ == '__main__':
    main()
