#!/usr/bin/env python3
"""
通过 RSS 获取 X (Twitter) KOL 观点
使用 Nitter 镜像服务
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re

class NitterRSSClient:
    """Nitter RSS 客户端"""
    
    # Nitter 实例列表（选速度快的）
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.it",
        "https://nitter.privacydev.net",
        "https://nitter.d420.de",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_user_feed(self, username, max_items=5):
        """获取用户 RSS Feed"""
        for instance in self.NITTER_INSTANCES:
            try:
                url = f"{instance}/{username}/rss"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    return self._parse_rss(response.text, max_items)
            except Exception as e:
                print(f"  {instance} failed: {e}")
                continue
        
        return []
    
    def _parse_rss(self, xml_content, max_items):
        """解析 RSS XML"""
        try:
            root = ET.fromstring(xml_content)
            items = []
            
            # RSS 2.0 格式
            for item in root.findall('.//item')[:max_items]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                
                # 清理 HTML 标签
                text = self._clean_html(description.text) if description is not None else ""
                
                items.append({
                    'title': title.text if title is not None else "",
                    'link': link.text if link is not None else "",
                    'published': pub_date.text if pub_date is not None else "",
                    'text': text[:200] + '...' if len(text) > 200 else text
                })
            
            return items
        except Exception as e:
            print(f"  Parse error: {e}")
            return []
    
    def _clean_html(self, html):
        """清理 HTML 标签"""
        if not html:
            return ""
        # 移除 HTML 标签
        clean = re.sub('<.*?>', '', html)
        # 解码 HTML 实体
        clean = clean.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return clean

def fetch_kol_rss(category=None, max_items=3):
    """获取 KOL RSS 观点"""
    
    # KOL 清单
    KOL_LIST = {
        "美股宏观/科技": ["chamath", "RayDalio", "jimcramer"],
        "中概/港股": ["HaoHongCFA", "maoxian"],
        "技术分析": ["traderstewie", "markminervini"],
        "宏观研究": ["biancoresearch"],
        "价值投资": ["peterlynchquotes"]
    }
    
    client = NitterRSSClient()
    results = {}
    
    categories = [category] if category else KOL_LIST.keys()
    
    for cat in categories:
        results[cat] = []
        print(f"\n📊 获取 {cat} 的 RSS 观点...")
        
        for username in KOL_LIST[cat]:
            try:
                tweets = client.get_user_feed(username, max_items)
                if tweets:
                    results[cat].append({
                        'username': username,
                        'tweets': tweets
                    })
                    print(f"  ✅ @{username}: {len(tweets)} 条")
                else:
                    print(f"  ⚠️ @{username}: 无数据")
            except Exception as e:
                print(f"  ❌ @{username}: {e}")
    
    return results

def format_for_insights(results):
    """格式化为投资洞察报告"""
    insights = []
    
    for category, users in results.items():
        for user in users:
            if user['tweets']:
                tweet = user['tweets'][0]  # 最新一条
                text = tweet['text'].replace('\n', ' ')
                if len(text) > 100:
                    text = text[:100] + '...'
                
                insights.append({
                    'investor': f"@{user['username']}",
                    'view': text,
                    'market': category.split('/')[0]
                })
    
    return insights

if __name__ == "__main__":
    print("=" * 60)
    print("RSS 方式获取 X KOL 观点")
    print("=" * 60)
    
    # 测试获取一个用户
    client = NitterRSSClient()
    print("\n🧪 测试获取 @chamath 的 RSS...")
    tweets = client.get_user_feed("chamath", max_items=2)
    
    if tweets:
        print(f"✅ 成功获取 {len(tweets)} 条推文")
        for i, tweet in enumerate(tweets, 1):
            print(f"\n  {i}. {tweet['text'][:100]}...")
            print(f"     时间: {tweet['published'][:20]}")
    else:
        print("❌ 获取失败，Nitter 服务可能不可用")
    
    # 完整测试
    print("\n" + "=" * 60)
    print("获取所有 KOL 观点...")
    print("=" * 60)
    
    results = fetch_kol_rss(max_items=2)
    insights = format_for_insights(results)
    
    print("\n📋 格式化输出（用于投资洞察报告）:")
    print("-" * 60)
    for item in insights[:5]:
        print(f"\n{item['investor']} ({item['market']}):")
        print(f"  \"{item['view']}\"")
