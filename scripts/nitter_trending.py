#!/usr/bin/env python3
"""
Nitter 方案 - 搜索热门话题和推文
比 X Cookie 更稳定的替代方案
"""

import requests
import re
from datetime import datetime
import random

class NitterSearch:
    """Nitter 搜索客户端"""
    
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.d420.de",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_tweets(self, query, count=10):
        """搜索推文"""
        for instance in self.NITTER_INSTANCES:
            try:
                url = f"{instance}/search"
                params = {
                    'f': 'tweets',  # 只搜索推文
                    'q': query,
                    'since': '',
                    'until': '',
                    'near': ''
                }
                
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    return self._parse_tweets(response.text, count)
                    
            except Exception as e:
                print(f"  {instance} failed: {e}")
                continue
        
        return []
    
    def _parse_tweets(self, html, count):
        """解析推文"""
        tweets = []
        
        # 从 HTML 中提取推文
        # 每条推文通常在 .timeline-item 中
        items = re.findall(r'<div class="timeline-item[^"]*"[^>]*>(.*?)</div>\s*</div>\s*<div class="timeline-item', html, re.DOTALL)
        
        if not items:
            # 备用模式
            items = re.findall(r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
        
        for item in items[:count]:
            # 提取用户名
            username_match = re.search(r'href="/([^"]+)"[^>]*class="username"', item) or \
                           re.search(r'<a[^>]*href="/([^"/]+)"[^>]*>.*?@', item)
            username = username_match.group(1) if username_match else "unknown"
            
            # 提取推文内容
            content_match = re.search(r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>', item, re.DOTALL) or \
                          re.search(r'<div class="content"[^>]*>(.*?)</div>', item, re.DOTALL)
            
            if content_match:
                content = content_match.group(1)
                # 清理 HTML
                content = re.sub(r'<[^>]+>', ' ', content)
                content = content.replace('&quot;', '"').replace('&amp;', '&')
                content = ' '.join(content.split())
                
                if len(content) > 10:
                    tweets.append({
                        'username': username,
                        'text': content[:200]
                    })
        
        return tweets
    
    def get_trending(self):
        """获取趋势话题"""
        for instance in self.NITTER_INSTANCES:
            try:
                url = f"{instance}/explore"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    # 提取热门标签
                    hashtags = re.findall(r'#/([^"\s<]+)', response.text)
                    return list(set(hashtags))[:15]
                    
            except Exception:
                continue
        
        return []

def generate_nitter_report():
    """生成 Nitter 热门话题报告"""
    print("=" * 70)
    print(f"📊 Nitter 热门话题报告 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    search = NitterSearch()
    
    # 获取趋势话题
    print("\n🔥 获取趋势话题...")
    trending = search.get_trending()
    if trending:
        print(f"  找到 {len(trending)} 个话题")
        for i, tag in enumerate(trending[:10], 1):
            print(f"  {i}. #{tag}")
    else:
        print("  ⚠️ 无法获取趋势话题")
    
    # 搜索投资相关推文
    search_queries = [
        ("AI人工智能", "AI"),
        ("A股", "A-share"),
        ("美股", "US stocks"),
        ("比特币", "Bitcoin"),
        ("英伟达", "NVIDIA"),
    ]
    
    print("\n📈 热门讨论:")
    all_results = {}
    
    for cn_query, en_query in search_queries:
        print(f"\n  🔍 {cn_query} / {en_query}:")
        
        # 尝试中文搜索
        tweets = search.search_tweets(cn_query, count=3)
        if not tweets:
            #  fallback 到英文
            tweets = search.search_tweets(en_query, count=3)
        
        if tweets:
            all_results[cn_query] = tweets
            for tweet in tweets[:2]:
                username = tweet.get('username', 'unknown')
                text = tweet.get('text', '')[:80]
                print(f"    @{username}: {text}...")
        else:
            print(f"    ⚠️ 无结果")
        
        # 延迟避免被封
        import time
        time.sleep(random.uniform(1, 2))
    
    # 保存报告
    report = f"""# X 热门话题报告 | {datetime.now().strftime('%Y-%m-%d')}

## 🔥 趋势话题

"""
    if trending:
        for i, tag in enumerate(trending[:10], 1):
            report += f"{i}. #{tag}\n"
    else:
        report += "*暂无法获取趋势话题*\n"
    
    report += "\n## 📈 热门讨论\n\n"
    
    for topic, tweets in all_results.items():
        report += f"### {topic}\n"
        for tweet in tweets[:3]:
            report += f"- **@{tweet['username']}**: {tweet['text'][:150]}...\n"
        report += "\n"
    
    report += f"\n---\n*数据来源: Nitter RSS | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    
    # 保存
    import os
    date_str = datetime.now().strftime('%Y-%m-%d')
    year = date_str[:4]
    month = date_str[5:7]
    
    os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
    report_path = f'../reports/{year}/{month}/trending-{date_str}.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存: {report_path}")

if __name__ == "__main__":
    generate_nitter_report()
