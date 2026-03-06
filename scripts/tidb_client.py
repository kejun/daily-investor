#!/usr/bin/env python3
"""
TiDB Cloud Zero 数据库客户端
用于投资追踪、KOL 观点存储、文章元数据管理
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

import pymysql
from pymysql.cursors import DictCursor

# 证书路径
CERT_PATH = os.path.expanduser('~/.openclaw/workspace/daily-investor/certs/isrgrootx1.pem')

# TiDB Cloud Zero 连接配置
TIDB_CONFIG = {
    'host': 'gateway01.us-west-2.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '1Au2q84rdJUCvma.root',
    'password': 'sVeoJboT0M0NwO0c',
    'database': 'demo',
    'cursorclass': DictCursor,
    'ssl': {'ca': CERT_PATH}
}

class TiDBClient:
    """TiDB Cloud Zero 客户端"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or TIDB_CONFIG
        self.conn = None
    
    def connect(self):
        """建立数据库连接"""
        if self.conn is None or not self.conn.open:
            self.conn = pymysql.connect(**self.config)
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
    
    # === 股票追踪 ===
    
    def add_stock_price(self, symbol: str, price: float, 
                        change_percent: float, volume: int):
        """添加股票价格记录"""
        with self.connect().cursor() as cursor:
            sql = """
            INSERT INTO stock_tracking (symbol, price, change_percent, volume)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (symbol, price, change_percent, volume))
            self.conn.commit()
            return cursor.lastrowid
    
    def get_latest_stocks(self, symbols: List[str] = None, limit: int = 10):
        """获取最新股票数据"""
        with self.connect().cursor() as cursor:
            if symbols:
                placeholders = ','.join(['%s'] * len(symbols))
                sql = f"""
                SELECT * FROM stock_tracking 
                WHERE symbol IN ({placeholders})
                ORDER BY recorded_at DESC 
                LIMIT %s
                """
                cursor.execute(sql, symbols + [limit])
            else:
                sql = """
                SELECT * FROM stock_tracking 
                ORDER BY recorded_at DESC 
                LIMIT %s
                """
                cursor.execute(sql, (limit,))
            return cursor.fetchall()
    
    # === KOL 观点 ===
    
    def add_kol_insight(self, username: str, platform: str, content: str,
                        likes: int = 0, retweets: int = 0,
                        sentiment: str = None, published_at: datetime = None):
        """添加 KOL 观点"""
        with self.connect().cursor() as cursor:
            sql = """
            INSERT INTO kol_insights 
            (username, platform, content, likes, retweets, sentiment, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (username, platform, content, likes, retweets, 
                                 sentiment, published_at or datetime.now()))
            self.conn.commit()
            return cursor.lastrowid
    
    def get_kol_insights(self, username: str = None, platform: str = None,
                         limit: int = 20):
        """获取 KOL 观点"""
        with self.connect().cursor() as cursor:
            conditions = []
            params = []
            
            if username:
                conditions.append("username = %s")
                params.append(username)
            if platform:
                conditions.append("platform = %s")
                params.append(platform)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql = f"""
            SELECT * FROM kol_insights 
            WHERE {where_clause}
            ORDER BY published_at DESC 
            LIMIT %s
            """
            cursor.execute(sql, params + [limit])
            return cursor.fetchall()
    
    # === 文章管理 ===
    
    def add_article(self, title: str, slug: str, category: str,
                    word_count: int, github_url: str,
                    status: str = 'draft', published_at: datetime = None):
        """添加文章元数据"""
        with self.connect().cursor() as cursor:
            sql = """
            INSERT INTO articles 
            (title, slug, category, word_count, status, github_url, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (title, slug, category, word_count, status,
                                 github_url, published_at or datetime.now()))
            self.conn.commit()
            return cursor.lastrowid
    
    def get_articles(self, category: str = None, status: str = None,
                     limit: int = 20):
        """获取文章列表"""
        with self.connect().cursor() as cursor:
            conditions = []
            params = []
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            if status:
                conditions.append("status = %s")
                params.append(status)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql = f"""
            SELECT * FROM articles 
            WHERE {where_clause}
            ORDER BY published_at DESC 
            LIMIT %s
            """
            cursor.execute(sql, params + [limit])
            return cursor.fetchall()
    
    def update_article_status(self, slug: str, status: str):
        """更新文章状态"""
        with self.connect().cursor() as cursor:
            sql = "UPDATE articles SET status = %s WHERE slug = %s"
            cursor.execute(sql, (status, slug))
            self.conn.commit()
            return cursor.rowcount
    
    # === 统计查询 ===
    
    def get_stats(self):
        """获取数据库统计"""
        with self.connect().cursor() as cursor:
            stats = {}
            
            # 股票记录数
            cursor.execute("SELECT COUNT(*) as count FROM stock_tracking")
            stats['stocks'] = cursor.fetchone()['count']
            
            # KOL 观点数
            cursor.execute("SELECT COUNT(*) as count FROM kol_insights")
            stats['kol_insights'] = cursor.fetchone()['count']
            
            # 文章数
            cursor.execute("SELECT COUNT(*) as count FROM articles")
            stats['articles'] = cursor.fetchone()['count']
            
            # 已发布文章数
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE status='published'")
            stats['published_articles'] = cursor.fetchone()['count']
            
            return stats


def main():
    """测试客户端"""
    print("=" * 60)
    print("TiDB Cloud Zero 客户端测试")
    print("=" * 60)
    
    with TiDBClient() as client:
        # 获取统计
        stats = client.get_stats()
        print(f"\n📊 数据库统计:")
        print(f"   股票记录：{stats['stocks']} 条")
        print(f"   KOL 观点：{stats['kol_insights']} 条")
        print(f"   文章总数：{stats['articles']} 篇")
        print(f"   已发布：{stats['published_articles']} 篇")
        
        # 查询最新文章
        print(f"\n📄 最新文章:")
        articles = client.get_articles(status='published', limit=3)
        for art in articles:
            print(f"   • {art['title']} ({art['word_count']} 字)")
            print(f"     🔗 {art['github_url']}")
        
        # 查询最新股票
        print(f"\n💰 最新股票数据:")
        stocks = client.get_latest_stocks(limit=5)
        for stock in stocks:
            sign = '+' if stock['change_percent'] > 0 else ''
            print(f"   {stock['symbol']}: ${stock['price']} ({sign}{stock['change_percent']}%)")


if __name__ == "__main__":
    main()
