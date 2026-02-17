#!/usr/bin/env python3
"""
Nitter 搜索工具
支持搜索任意关键词
"""

import requests
import re
import random
from datetime import datetime
from urllib.parse import quote

class NitterSearchTool:
    """Nitter 搜索工具"""
    
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.privacydev.net", 
        "https://nitter.d420.de",
        "https://nitter.space",
        "https://nitter.cz",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def search(self, query, max_results=10):
        """
        搜索推文
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
        """
        print(f"🔍 搜索: '{query}'")
        
        # 打乱实例顺序
        instances = self.NITTER_INSTANCES.copy()
        random.shuffle(instances)
        
        for instance in instances:
            try:
                url = f"{instance}/search"
                params = {
                    'f': 'tweets',
                    'q': query,
                    'since': '',
                    'until': '',
                    'near': ''
                }
                
                print(f"  📡 尝试 {instance}...")
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=20,
                    allow_redirects=True
                )
                
                print(f"  📊 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    tweets = self._parse_search_results(response.text, max_results)
                    if tweets:
                        print(f"  ✅ 找到 {len(tweets)} 条推文")
                        return tweets
                    else:
                        print(f"  ⚠️ 页面加载成功但未找到推文")
                        # 保存页面内容用于调试
                        if 'No items found' in response.text:
                            print(f"  ℹ️ 提示: 未找到相关内容")
                        
            except requests.exceptions.Timeout:
                print(f"  ⏱️ 超时")
                continue
            except requests.exceptions.ConnectionError:
                print(f"  🔌 连接失败")
                continue
            except Exception as e:
                print(f"  ❌ 错误: {str(e)[:50]}")
                continue
        
        return []
    
    def _parse_search_results(self, html, max_results):
        """解析搜索结果"""
        tweets = []
        
        # 检查是否有结果
        if 'No items found' in html or 'no results' in html.lower():
            return tweets
        
        # 方法1: 查找 timeline-item
        pattern1 = r'<div class="timeline-item[^"]*"[^>]*>.*?<div class="tweet-content[^"]*"[^>]*>(.*?)</div>\s*</div>'
        items = re.findall(pattern1, html, re.DOTALL)
        
        if not items:
            # 方法2: 更宽松的模式
            pattern2 = r'<div class="tweet-body[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>'
            items = re.findall(pattern2, html, re.DOTALL)
        
        for item in items[:max_results]:
            tweet = self._extract_tweet_data(item)
            if tweet:
                tweets.append(tweet)
        
        return tweets
    
    def _extract_tweet_data(self, html):
        """提取单条推文数据"""
        # 提取用户名
        username_match = re.search(r'href="/([^"/]+)"[^>]*class="username"', html) or \
                        re.search(r'<a[^>]*href="/([^"/]+)"[^>]*>\s*@', html) or \
                        re.search(r'data-screen-name="([^"]+)"', html)
        username = username_match.group(1) if username_match else "unknown"
        
        # 提取推文内容 - 尝试多种模式
        content = ""
        
        # 模式1: tweet-content
        content_match = re.search(r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>\s*(?:<div class="tweet-stats|<div class="tweet-date)', html, re.DOTALL)
        if content_match:
            content = content_match.group(1)
        
        # 模式2: tweet-text
        if not content:
            text_match = re.search(r'<div class="tweet-text[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            if text_match:
                content = text_match.group(1)
        
        # 清理 HTML
        if content:
            # 移除 HTML 标签
            content = re.sub(r'<[^>]+>', ' ', content)
            # 解码实体
            content = content.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'")
            # 合并空格
            content = ' '.join(content.split())
            
            if len(content) > 10:
                return {
                    'username': username.strip(),
                    'text': content.strip()[:280]  # 限制长度
                }
        
        return None
    
    def search_multiple(self, queries, results_per_query=5):
        """
        批量搜索多个关键词
        
        Args:
            queries: 关键词列表
            results_per_query: 每个关键词的结果数
        """
        all_results = {}
        
        for query in queries:
            tweets = self.search(query, results_per_query)
            all_results[query] = tweets
            
            # 延迟避免被封
            if query != queries[-1]:
                import time
                time.sleep(random.uniform(2, 3))
        
        return all_results

def main():
    """主函数 - 测试搜索"""
    search = NitterSearchTool()
    
    # 测试搜索 OpenClaw
    print("=" * 70)
    print("Nitter 搜索测试")
    print("=" * 70)
    
    print("\n🔍 搜索: 'OpenClaw'")
    tweets = search.search("OpenClaw", max_results=5)
    
    if tweets:
        print(f"\n📋 找到 {len(tweets)} 条推文:\n")
        for i, tweet in enumerate(tweets, 1):
            print(f"{i}. @{tweet['username']}:")
            print(f"   {tweet['text'][:150]}...")
            print()
    else:
        print("\n❌ 未找到相关推文")
    
    # 批量搜索热门关键词
    print("\n" + "=" * 70)
    print("批量搜索热门关键词")
    print("=" * 70)
    
    keywords = [
        "AI",
        "Bitcoin", 
        "StockMarket",
        "NVIDIA"
    ]
    
    results = search.search_multiple(keywords, results_per_query=3)
    
    print("\n📊 搜索结果汇总:\n")
    for keyword, tweets in results.items():
        print(f"🔹 {keyword}: {len(tweets)} 条推文")
        for tweet in tweets[:2]:
            print(f"   @{tweet['username']}: {tweet['text'][:80]}...")
        print()

if __name__ == "__main__":
    main()
