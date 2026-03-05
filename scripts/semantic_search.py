#!/usr/bin/env python3
"""
语义搜索应用 - 基于 TiDB Zero + 阿里云 Embedding
支持添加文档、语义搜索、相似度计算
"""

import os
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

import pymysql
from pymysql.cursors import DictCursor
import requests

# ============ 配置 ============

# TiDB 连接配置
CERT_PATH = os.path.expanduser('~/.openclaw/workspace/daily-investor/certs/isrgrootx1.pem')
TIDB_CONFIG = {
    'host': 'gateway01.us-west-2.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '1Au2q84rdJUCvma.root',
    'password': 'sVeoJboT0M0NwO0c',
    'database': 'semantic_search',
    'cursorclass': DictCursor,
    'ssl': {'ca': CERT_PATH}
}

# 阿里云百炼 Embedding 配置
# 优先使用环境变量，否则使用 Mock 模式
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
EMBEDDING_MODEL = 'text-embedding-v3'
EMBEDDING_DIM = 1024  # text-embedding-v3 的维度

# OpenRouter 配置（备用）
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_EMBEDDING_MODEL = 'openai/text-embedding-3-small'

# ============ Embedding 客户端 ============

class EmbeddingClient:
    """嵌入向量客户端 - 支持多种 API"""
    
    def __init__(self, provider: str = 'auto'):
        """
        初始化嵌入客户端
        
        Args:
            provider: 'auto' | 'dashscope' | 'openrouter' | 'mock'
        """
        self.provider = self._detect_provider(provider)
        self.dashscope_key = DASHSCOPE_API_KEY
        self.openrouter_key = OPENROUTER_API_KEY
    
    def _detect_provider(self, provider: str) -> str:
        """自动检测可用的嵌入服务"""
        if provider != 'auto':
            return provider
        
        if DASHSCOPE_API_KEY:
            return 'dashscope'
        elif OPENROUTER_API_KEY:
            return 'openrouter'
        else:
            return 'mock'
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本的嵌入向量"""
        if self.provider == 'dashscope':
            return self._get_dashscope_embedding(text)
        elif self.provider == 'openrouter':
            return self._get_openrouter_embedding(text)
        else:
            return self._mock_embedding(text)
    
    def _get_dashscope_embedding(self, text: str) -> List[float]:
        """阿里云百炼 Embedding"""
        try:
            response = requests.post(
                'https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self.dashscope_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': EMBEDDING_MODEL,
                    'input': text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['data'][0]['embedding']
            else:
                print(f"⚠️ DashScope API 错误: {response.status_code}")
                return self._mock_embedding(text)
        except Exception as e:
            print(f"⚠️ DashScope 请求失败: {e}")
            return self._mock_embedding(text)
    
    def _get_openrouter_embedding(self, text: str) -> List[float]:
        """OpenRouter Embedding"""
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self.openrouter_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': OPENROUTER_EMBEDDING_MODEL,
                    'input': text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['data'][0]['embedding']
            else:
                print(f"⚠️ OpenRouter API 错误: {response.status_code}")
                return self._mock_embedding(text)
        except Exception as e:
            print(f"⚠️ OpenRouter 请求失败: {e}")
            return self._mock_embedding(text)
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Mock 嵌入向量（用于测试）"""
        # 使用简单的哈希作为种子，生成伪随机向量
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(EMBEDDING_DIM).astype(np.float32)
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取嵌入向量"""
        return [self.get_embedding(text) for text in texts]


# ============ 语义搜索客户端 ============

class SemanticSearch:
    """语义搜索客户端"""
    
    def __init__(self, embedding_client: EmbeddingClient = None):
        self.embedding = embedding_client or EmbeddingClient()
        self.conn = None
    
    def connect(self):
        """建立数据库连接"""
        if self.conn is None or not self.conn.open:
            self.conn = pymysql.connect(**TIDB_CONFIG)
        return self.conn
    
    def close(self):
        """关闭连接"""
        if self.conn and self.conn.open:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # === 文档管理 ===
    
    def add_document(self, title: str, content: str, metadata: Dict = None) -> int:
        """
        添加文档
        
        Args:
            title: 文档标题
            content: 文档内容
            metadata: 可选元数据
        
        Returns:
            文档 ID
        """
        # 生成嵌入向量（标题 + 内容）
        text_to_embed = f"{title}\n{content}"
        embedding = self.embedding.get_embedding(text_to_embed)
        
        with self.connect().cursor() as cursor:
            sql = """
            INSERT INTO documents (title, content, embedding, metadata)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (
                title,
                content,
                json.dumps(embedding),
                json.dumps(metadata or {})
            ))
            self.conn.commit()
            
            doc_id = cursor.lastrowid
            print(f"✅ 文档已添加: ID={doc_id}, 标题={title[:50]}...")
            return doc_id
    
    def add_documents_batch(self, documents: List[Dict[str, Any]]) -> List[int]:
        """批量添加文档"""
        ids = []
        for doc in documents:
            doc_id = self.add_document(
                title=doc.get('title', ''),
                content=doc.get('content', ''),
                metadata=doc.get('metadata')
            )
            ids.append(doc_id)
        return ids
    
    def get_document(self, doc_id: int) -> Dict:
        """获取单个文档"""
        with self.connect().cursor() as cursor:
            cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
            return cursor.fetchone()
    
    def list_documents(self, limit: int = 20) -> List[Dict]:
        """列出所有文档"""
        with self.connect().cursor() as cursor:
            cursor.execute("""
                SELECT id, title, LEFT(content, 100) as content_preview, 
                       created_at, metadata
                FROM documents 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    
    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""
        with self.connect().cursor() as cursor:
            cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            self.conn.commit()
            return cursor.rowcount > 0
    
    # === 语义搜索 ===
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            threshold: 相似度阈值（0-1）
        
        Returns:
            搜索结果列表，按相似度排序
        """
        # 生成查询嵌入
        query_embedding = self.embedding.get_embedding(query)
        query_vec = np.array(query_embedding)
        
        # 获取所有文档
        with self.connect().cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, embedding, metadata, created_at
                FROM documents
            """)
            documents = cursor.fetchall()
        
        if not documents:
            return []
        
        # 计算相似度
        results = []
        for doc in documents:
            doc_embedding = json.loads(doc['embedding'])
            doc_vec = np.array(doc_embedding)
            
            # 计算余弦相似度
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
            )
            
            if similarity >= threshold:
                results.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'metadata': json.loads(doc['metadata']) if doc['metadata'] else {},
                    'similarity': float(similarity),
                    'created_at': doc['created_at'].isoformat() if doc['created_at'] else None
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def find_similar(self, doc_id: int, top_k: int = 5) -> List[Dict]:
        """查找与指定文档相似的其他文档"""
        doc = self.get_document(doc_id)
        if not doc or not doc.get('embedding'):
            return []
        
        query_embedding = json.loads(doc['embedding'])
        query_vec = np.array(query_embedding)
        
        with self.connect().cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, embedding, metadata, created_at
                FROM documents
                WHERE id != %s
            """, (doc_id,))
            documents = cursor.fetchall()
        
        results = []
        for d in documents:
            d_embedding = json.loads(d['embedding'])
            d_vec = np.array(d_embedding)
            
            similarity = np.dot(query_vec, d_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(d_vec)
            )
            
            results.append({
                'id': d['id'],
                'title': d['title'],
                'similarity': float(similarity)
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    # === 统计 ===
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.connect().cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            total = cursor.fetchone()['count']
            
            return {
                'total_documents': total,
                'database': 'semantic_search',
                'embedding_model': EMBEDDING_MODEL,
                'embedding_dim': EMBEDDING_DIM
            }


# ============ CLI 界面 ============

def cli_add(search: SemanticSearch):
    """添加文档"""
    print("\n📝 添加新文档")
    print("-" * 40)
    
    title = input("标题: ").strip()
    if not title:
        print("❌ 标题不能为空")
        return
    
    print("内容 (输入空行结束):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    
    content = "\n".join(lines)
    if not content:
        print("❌ 内容不能为空")
        return
    
    # 添加可选元数据
    metadata = {}
    tags = input("标签 (逗号分隔，可选): ").strip()
    if tags:
        metadata['tags'] = [t.strip() for t in tags.split(',')]
    
    doc_id = search.add_document(title, content, metadata)
    print(f"\n✅ 文档已保存，ID: {doc_id}")


def cli_search(search: SemanticSearch):
    """语义搜索"""
    print("\n🔍 语义搜索")
    print("-" * 40)
    
    query = input("输入搜索内容: ").strip()
    if not query:
        print("❌ 搜索内容不能为空")
        return
    
    try:
        top_k = int(input("返回结果数量 (默认 5): ").strip() or "5")
    except ValueError:
        top_k = 5
    
    print(f"\n🔎 搜索中...")
    results = search.search(query, top_k=top_k)
    
    if not results:
        print("❌ 没有找到相关文档")
        return
    
    print(f"\n找到 {len(results)} 个相关文档:\n")
    for i, r in enumerate(results, 1):
        print(f"【{i}】相似度: {r['similarity']:.3f}")
        print(f"    标题: {r['title']}")
        print(f"    内容: {r['content'][:100]}...")
        print(f"    ID: {r['id']}")
        print()


def cli_list(search: SemanticSearch):
    """列出所有文档"""
    print("\n📚 文档列表")
    print("-" * 40)
    
    docs = search.list_documents()
    
    if not docs:
        print("暂无文档")
        return
    
    for doc in docs:
        print(f"ID: {doc['id']} | {doc['title']}")
        print(f"   {doc['content_preview']}...")
        print(f"   创建时间: {doc['created_at']}")
        print()


def cli_stats(search: SemanticSearch):
    """显示统计"""
    print("\n📊 数据库统计")
    print("-" * 40)
    
    stats = search.get_stats()
    print(f"文档总数: {stats['total_documents']}")
    print(f"数据库: {stats['database']}")
    print(f"嵌入模型: {stats['embedding_model']}")
    print(f"向量维度: {stats['embedding_dim']}")


def cli_similar(search: SemanticSearch):
    """查找相似文档"""
    print("\n🔗 查找相似文档")
    print("-" * 40)
    
    try:
        doc_id = int(input("输入文档 ID: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字 ID")
        return
    
    results = search.find_similar(doc_id)
    
    if not results:
        print("没有找到相似文档")
        return
    
    print(f"\n找到 {len(results)} 个相似文档:\n")
    for i, r in enumerate(results, 1):
        print(f"【{i}】相似度: {r['similarity']:.3f}")
        print(f"    ID: {r['id']} | {r['title']}")
        print()


def cli_demo(search: SemanticSearch):
    """添加示例数据"""
    print("\n🎯 添加示例数据...")
    
    sample_docs = [
        {
            'title': '人工智能发展趋势',
            'content': '人工智能正在快速发展，大语言模型、多模态AI、智能代理等技术不断突破。2026年将是AI应用落地的重要一年。',
            'metadata': {'tags': ['AI', '科技趋势']}
        },
        {
            'title': '机器学习算法介绍',
            'content': '机器学习是人工智能的核心技术，包括监督学习、无监督学习、强化学习等。深度学习是机器学习的重要分支，在图像识别、自然语言处理等领域取得了突破。',
            'metadata': {'tags': ['机器学习', '深度学习']}
        },
        {
            'title': '投资理财基础知识',
            'content': '投资理财是财务管理的重要组成部分。常见的投资方式包括股票、债券、基金、房地产等。分散投资是降低风险的重要策略。',
            'metadata': {'tags': ['投资', '理财']}
        },
        {
            'title': 'Python 编程技巧',
            'content': 'Python 是一门流行的编程语言，广泛用于数据分析、机器学习、Web开发等领域。掌握列表推导式、装饰器、生成器等特性可以提高代码效率。',
            'metadata': {'tags': ['Python', '编程']}
        },
        {
            'title': '神经网络架构设计',
            'content': '神经网络是深度学习的基础，常见的架构包括CNN、RNN、Transformer等。Transformer架构在自然语言处理领域取得了巨大成功。',
            'metadata': {'tags': ['神经网络', '深度学习']}
        }
    ]
    
    ids = search.add_documents_batch(sample_docs)
    print(f"✅ 已添加 {len(ids)} 个示例文档")


def main():
    """主程序"""
    print("=" * 60)
    print("🔍 语义搜索应用 - TiDB Zero + 阿里云 Embedding")
    print("=" * 60)
    
    with SemanticSearch() as search:
        while True:
            print("\n命令菜单:")
            print("  1. 添加文档")
            print("  2. 语义搜索")
            print("  3. 列出文档")
            print("  4. 查找相似")
            print("  5. 显示统计")
            print("  6. 添加示例数据")
            print("  0. 退出")
            
            choice = input("\n请选择: ").strip()
            
            if choice == '1':
                cli_add(search)
            elif choice == '2':
                cli_search(search)
            elif choice == '3':
                cli_list(search)
            elif choice == '4':
                cli_similar(search)
            elif choice == '5':
                cli_stats(search)
            elif choice == '6':
                cli_demo(search)
            elif choice == '0':
                print("\n👋 再见!")
                break
            else:
                print("❌ 无效选择")


if __name__ == "__main__":
    main()
