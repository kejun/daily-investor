#!/usr/bin/env python3
"""
语义搜索 Web 应用
基于 Flask + TiDB Zero + 阿里云 Embedding
"""

import os
import sys
import json
from datetime import datetime

from flask import Flask, render_template_string, request, jsonify

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))
from semantic_search import SemanticSearch, EMBEDDING_MODEL

app = Flask(__name__)

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 语义搜索</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .stats {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #666;
        }
        .results {
            margin-top: 20px;
        }
        .result-item {
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 0 10px 10px 0;
            transition: transform 0.2s;
        }
        .result-item:hover {
            transform: translateX(5px);
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .result-title {
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }
        .result-similarity {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
        }
        .result-content {
            color: #666;
            line-height: 1.6;
            font-size: 0.95em;
        }
        .result-meta {
            margin-top: 10px;
            font-size: 0.85em;
            color: #999;
        }
        .tag {
            display: inline-block;
            background: #e0e0e0;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 5px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .add-doc {
            margin-top: 30px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
        }
        .add-doc h3 {
            margin-bottom: 15px;
            color: #333;
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
            margin-bottom: 10px;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 语义搜索</h1>
        <p class="subtitle">基于 TiDB Zero + 阿里云 Embedding ({{ embedding_model }})</p>
        
        <div class="stats">
            📊 数据库：<strong>{{ stats.total_documents }}</strong> 个文档
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="输入搜索内容..." 
                   onkeypress="if(event.key==='Enter') doSearch()">
            <button onclick="doSearch()" id="searchBtn">搜索</button>
        </div>
        
        <div id="results" class="results"></div>
        
        <div class="add-doc">
            <h3>📝 添加文档</h3>
            <div class="form-group">
                <label>标题</label>
                <input type="text" id="docTitle" style="width:100%; padding:10px; border:2px solid #e0e0e0; border-radius:8px;">
            </div>
            <div class="form-group">
                <label>内容</label>
                <textarea id="docContent" placeholder="输入文档内容..."></textarea>
            </div>
            <div class="form-group">
                <label>标签（逗号分隔，可选）</label>
                <input type="text" id="docTags" style="width:100%; padding:10px; border:2px solid #e0e0e0; border-radius:8px;" placeholder="AI, 技术">
            </div>
            <button onclick="addDocument()">添加文档</button>
        </div>
        
        <div class="add-doc">
            <h3>📚 文档管理</h3>
            <button onclick="viewAllDocuments()" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">📋 查看所有文档</button>
        </div>
    </div>
    
    <!-- 文档列表弹窗 -->
    <div id="docListModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000;" onclick="closeDocList(event)">
        <div style="max-width:800px; margin:50px auto; background:white; border-radius:16px; padding:40px; max-height:80vh; overflow-y:auto;" onclick="event.stopPropagation()">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h2 style="margin:0;">📚 所有文档</h2>
                <button onclick="document.getElementById('docListModal').style.display='none'" style="background:#f0f0f0; color:#333; padding:10px 20px;">✕ 关闭</button>
            </div>
            <div id="docListContent" class="loading">加载中...</div>
        </div>
    </div>
    
    <script>
        async function doSearch() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;
            
            const resultsDiv = document.getElementById('results');
            const searchBtn = document.getElementById('searchBtn');
            
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>搜索中...</div>';
            searchBtn.disabled = true;
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query, top_k: 5})
                });
                const data = await response.json();
                
                if (data.results.length === 0) {
                    resultsDiv.innerHTML = '<div class="loading">没有找到相关文档</div>';
                } else {
                    let html = '';
                    data.results.forEach((r, i) => {
                        const tags = r.metadata && r.metadata.tags 
                            ? r.metadata.tags.map(t => `<span class="tag">${t}</span>`).join('')
                            : '';
                        html += `
                            <div class="result-item">
                                <div class="result-header">
                                    <span class="result-title">${i+1}. ${escapeHtml(r.title)}</span>
                                    <span class="result-similarity">${(r.similarity * 100).toFixed(1)}% 匹配</span>
                                </div>
                                <div class="result-content">${escapeHtml(r.content.substring(0, 200))}${r.content.length > 200 ? '...' : ''}</div>
                                ${tags ? '<div class="result-meta">' + tags + '</div>' : ''}
                            </div>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                }
            } catch (e) {
                resultsDiv.innerHTML = '<div class="loading">搜索失败：' + e.message + '</div>';
            }
            
            searchBtn.disabled = false;
        }
        
        async function addDocument() {
            const title = document.getElementById('docTitle').value.trim();
            const content = document.getElementById('docContent').value.trim();
            const tags = document.getElementById('docTags').value.trim();
            
            if (!title || !content) {
                alert('标题和内容不能为空');
                return;
            }
            
            try {
                const response = await fetch('/document', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: title,
                        content: content,
                        metadata: {tags: tags ? tags.split(',').map(t=>t.trim()) : []}
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    alert('文档已添加！ID: ' + data.doc_id);
                    document.getElementById('docTitle').value = '';
                    document.getElementById('docContent').value = '';
                    document.getElementById('docTags').value = '';
                    location.reload();
                } else {
                    alert('添加失败：' + data.error);
                }
            } catch (e) {
                alert('添加失败：' + e.message);
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function viewAllDocuments() {
            const modal = document.getElementById('docListModal');
            const content = document.getElementById('docListContent');
            
            modal.style.display = 'block';
            content.innerHTML = '<div class="spinner"></div>加载中...';
            
            try {
                const response = await fetch('/documents?limit=50');
                const data = await response.json();
                
                if (data.documents.length === 0) {
                    content.innerHTML = '<div class="loading">暂无文档</div>';
                    return;
                }
                
                let html = '<div class="results">';
                data.documents.forEach((doc, i) => {
                    const tags = doc.metadata && doc.metadata.tags 
                        ? doc.metadata.tags.map(t => `<span class="tag">${t}</span>`).join('')
                        : '';
                    html += `
                        <div class="result-item">
                            <div class="result-header">
                                <span class="result-title">${i+1}. ${escapeHtml(doc.title)}</span>
                                <span style="font-size:0.85em; color:#999;">ID: ${doc.id}</span>
                            </div>
                            <div class="result-content">${escapeHtml(doc.content_preview || doc.content || '').substring(0, 150)}${(doc.content_preview || doc.content || '').length > 150 ? '...' : ''}</div>
                            <div class="result-meta">
                                创建时间：${doc.created_at || '未知'}
                                ${tags ? '<br>' + tags : ''}
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                content.innerHTML = html;
            } catch (e) {
                content.innerHTML = '<div class="loading">加载失败：' + e.message + '</div>';
            }
        }
        
        function closeDocList(e) {
            if (e.target.id === 'docListModal') {
                document.getElementById('docListModal').style.display = 'none';
            }
        }
        
        // 点击 ESC 关闭弹窗
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.getElementById('docListModal').style.display = 'none';
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """首页"""
    with SemanticSearch() as search:
        stats = search.get_stats()
    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        embedding_model=EMBEDDING_MODEL
    )

@app.route('/search', methods=['POST'])
def search():
    """语义搜索 API"""
    data = request.json
    query = data.get('query', '')
    top_k = data.get('top_k', 5)
    
    if not query:
        return jsonify({'error': '查询内容为空'}), 400
    
    with SemanticSearch() as search:
        results = search.search(query, top_k=top_k)
    
    return jsonify({'results': results})

@app.route('/document', methods=['POST'])
def add_document():
    """添加文档 API"""
    data = request.json
    title = data.get('title', '')
    content = data.get('content', '')
    metadata = data.get('metadata', {})
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    try:
        with SemanticSearch() as search:
            doc_id = search.add_document(title, content, metadata)
        return jsonify({'success': True, 'doc_id': doc_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/documents', methods=['GET'])
def list_documents():
    """列出所有文档 API"""
    limit = request.args.get('limit', 20, type=int)
    
    with SemanticSearch() as search:
        docs = search.list_documents(limit)
    
    return jsonify({'documents': docs})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 启动语义搜索 Web 服务...")
    print(f"   本地访问：http://localhost:{port}")
    print(f"   按 Ctrl+C 停止服务")
    app.run(host='0.0.0.0', port=port, debug=False)
