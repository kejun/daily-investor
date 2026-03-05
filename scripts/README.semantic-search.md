# 🔍 语义搜索应用

基于 TiDB Cloud Zero + 阿里云百炼 Embedding 的语义搜索应用。

## 功能特性

- ✅ **语义搜索** - 基于向量相似度，理解查询意图
- ✅ **文档管理** - 添加、删除、浏览文档
- ✅ **相似推荐** - 查找与指定文档相似的内容
- ✅ **批量导入** - 支持批量添加文档
- ✅ **元数据支持** - 支持标签等自定义元数据

## 技术架构

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  用户查询   │ ──► │ 阿里云 Embedding │ ──► │  1024 维向量  │
└─────────────┘     └──────────────────┘     └──────────────┘
                                                        │
                                                        ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  搜索结果   │ ◄── │  余弦相似度排序   │ ◄── │ TiDB Zero DB │
└─────────────┘     └──────────────────┘     └──────────────┘
```

## 快速开始

### 1. 运行应用

```bash
cd ~/.openclaw/workspace/daily-investor/scripts

# CLI 交互模式
python3 semantic_search.py
```

### 2. 编程方式使用

```python
from semantic_search import SemanticSearch

with SemanticSearch() as search:
    # 添加文档
    doc_id = search.add_document(
        title='文档标题',
        content='文档内容...',
        metadata={'tags': ['标签 ', '分类']}
    )
    
    # 语义搜索
    results = search.search('AI 人工智能', top_k=5)
    for r in results:
        print(f'{r["similarity"]:.3f} - {r["title"]}')
    
    # 查找相似文档
    similar = search.find_similar(doc_id=1, top_k=3)
    for s in similar:
        print(f'{s["similarity"]:.3f} - {s["title"]}')
```

## 配置说明

### 数据库配置

TiDB Cloud Zero 实例信息保存在 `TOOLS.md`，包括：
- Host, Port, Username, Password
- 实例 30 天有效，过期需重新创建

### Embedding 配置

使用阿里云百炼 `text-embedding-v4` 模型：
- **维度**: 1024
- **API Key**: 已配置在脚本中
- **Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`

如需使用其他嵌入服务，可设置环境变量：

```bash
# 使用环境变量覆盖默认配置
export DASHSCOPE_API_KEY="your-api-key"
python3 semantic_search.py
```

## API 参考

### SemanticSearch 类

#### 添加文档
```python
add_document(title: str, content: str, metadata: Dict = None) -> int
add_documents_batch(documents: List[Dict]) -> List[int]
```

#### 搜索
```python
search(query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict]
find_similar(doc_id: int, top_k: int = 5) -> List[Dict]
```

#### 管理
```python
get_document(doc_id: int) -> Dict
list_documents(limit: int = 20) -> List[Dict]
delete_document(doc_id: int) -> bool
get_stats() -> Dict
```

## 示例数据

应用预置了 8 个示例文档，覆盖以下主题：
- AI/人工智能
- 机器学习/深度学习
- Python 编程
- 神经网络
- 投资理财
- Agent 记忆系统
- MCP 协议
- 向量数据库

## 搜索效果测试

```
🔍 搜索 "机器学习和深度学习"
1. [0.696] 机器学习算法详解
2. [0.539] 神经网络架构设计
3. [0.376] Python 编程技巧

🔍 搜索 "Agent 智能代理记忆"
1. [0.743] Agent 记忆系统架构
2. [0.468] MCP 协议详解
3. [0.372] 人工智能发展趋势
```

## 注意事项

1. **TiDB Zero 实例有效期**: 30 天，过期需重新创建
2. **Claim 实例**: 如需长期保存，访问 Claim URL 转换为 TiDB Starter
3. **API 调用**: 阿里云 Embedding 按调用次数计费（免费额度充足）
4. **相似度阈值**: 可通过 `threshold` 参数过滤低质量结果（推荐 0.3-0.5）

## 扩展方向

- [ ] 支持文档分块（长文档分割）
- [ ] 添加混合搜索（关键词 + 语义）
- [ ] 支持多语言嵌入
- [ ] Web UI 界面
- [ ] API 服务化

---

*基于 TiDB Cloud Zero + 阿里云百炼 Embedding*
