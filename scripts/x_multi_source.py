#!/usr/bin/env python3
"""
X 热门话题多源采集方案
结合 Google 搜索 + Nitter RSS + Cookie 访问
"""

import os
import sys
import requests
import re
import random
from datetime import datetime
from urllib.parse import quote

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
from fetch_nitter_v2 import NitterRSSClient

class XMultiSource:
    """X 多源采集器"""
    
    def __init__(self):
        self.nitter = NitterRSSClient()
        self._load_cookie()
    
    def _load_cookie(self):
        """加载 Cookie"""
        env_paths = [
            os.path.join(os.path.dirname(__file__), '.env.cookie'),
            os.path.join(os.path.dirname(__file__), '..', '.env.cookie'),
        ]
        for path in env_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            k, v = line.strip().split('=', 1)
                            os.environ[k] = v
        
        self.ct0 = os.getenv('X_CT0')
        self.twid = os.getenv('X_TWID')
    
    def search_google_twitter(self, query, count=5):
        """
        使用 Google 搜索 Twitter 内容
        搜索语法: site:twitter.com keyword
        """
        print(f"🔍 Google 搜索: '{query}' on Twitter...")
        
        try:
            # 使用 searx 或其他无搜索引擎
            # 这里使用 Brave Search API（如果有）或替代方案
            
            # 尝试使用 Brave Search
            brave_api_key = os.getenv('BRAVE_API_KEY', '')
            if brave_api_key:
                url = "https://api.search.brave.com/res/v1/web/search"
                headers = {
                    "Accept": "application/json",
                    "X-Subscription-Token": brave_api_key
                }
                params = {
                    "q": f"site:twitter.com {query}",
                    "count": count,
                    "freshness": "pd"  # 过去24小时
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get('web', {}).get('results', []):
                        if 'twitter.com' in item.get('url', ''):
                            results.append({
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'description': item.get('description', '')[:150]
                            })
                    return results[:count]
            
            # 如果没有 Brave API，使用备用方案
            return []
            
        except Exception as e:
            print(f"  ⚠️ 搜索失败: {e}")
            return []
    
    def get_kol_tweets(self, username, count=5):
        """获取 KOL 推文"""
        try:
            return self.nitter.get_user_feed(username, count)
        except:
            return []
    
    def extract_trending_from_kols(self, kols=None):
        """
        从 KOL 推文中提取热门话题
        """
        if kols is None:
            kols = [
                'chamath', 'RayDalio', 'jimcramer',
                'elonmusk', 'traderstewie', 'markminervini'
            ]
        
        print("📊 分析 KOL 推文...")
        
        all_hashtags = []
        all_mentions = []
        tweet_samples = []
        
        for username in kols:
            try:
                tweets = self.get_kol_tweets(username, 5)
                for tweet in tweets:
                    text = tweet.get('text', '')
                    
                    # 提取标签
                    hashtags = re.findall(r'#(\w+)', text)
                    all_hashtags.extend(hashtags)
                    
                    # 提取提及
                    mentions = re.findall(r'@(\w+)', text)
                    all_mentions.extend(mentions)
                    
                    # 保存样本
                    if len(tweet_samples) < 10:
                        tweet_samples.append({
                            'username': username,
                            'text': text[:150] + '...' if len(text) > 150 else text
                        })
                
                import time
                time.sleep(1)
                
            except Exception as e:
                continue
        
        # 统计频率
        from collections import Counter
        top_hashtags = Counter(all_hashtags).most_common(15)
        top_mentions = Counter(all_mentions).most_common(10)
        
        return {
            'hashtags': top_hashtags,
            'mentions': top_mentions,
            'samples': tweet_samples
        }
    
    def get_timeline_preview(self):
        """
        使用 Cookie 获取主页时间线预览
        """
        if not self.ct0 or not self.twid:
            return None
        
        print("📱 获取主页时间线...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Cookie': f'ct0={self.ct0}; twid={self.twid}',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get('https://x.com/home', headers=headers, timeout=15)
            
            if response.status_code == 200 and 'login' not in response.url:
                # 从页面中提取推文内容
                texts = re.findall(r'"text"[:\s]*"([^"]{20,280})"', response.text)
                return texts[:5]
            
            return None
            
        except Exception as e:
            return None
    
    def generate_comprehensive_report(self):
        """生成综合报告"""
        print("=" * 70)
        print(f"📊 X 热门话题综合报告 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        # 1. 从 KOL 提取热门话题
        kol_data = self.extract_trending_from_kols()
        
        print("\n🔥 热门标签:")
        if kol_data['hashtags']:
            for i, (tag, count) in enumerate(kol_data['hashtags'][:10], 1):
                print(f"  {i}. #{tag} ({count}次)")
        
        print("\n👥 热门提及:")
        if kol_data['mentions']:
            for i, (mention, count) in enumerate(kol_data['mentions'][:5], 1):
                print(f"  {i}. @{mention} ({count}次)")
        
        print("\n💬 热门推文:")
        for i, tweet in enumerate(kol_data['samples'][:5], 1):
            print(f"\n  {i}. @{tweet['username']}:")
            print(f"     {tweet['text']}")
        
        # 2. 获取时间线预览
        timeline = self.get_timeline_preview()
        if timeline:
            print("\n📱 主页时间线预览:")
            for i, text in enumerate(timeline[:3], 1):
                print(f"  {i}. {text[:100]}...")
        
        # 生成报告文件
        self._save_report(kol_data, timeline)
        
        return kol_data
    
    def _save_report(self, kol_data, timeline):
        """保存报告"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        year = date_str[:4]
        month = date_str[5:7]
        
        content = f"""# X 热门话题综合报告 | {date_str}

## 🔥 热门标签

"""
        
        if kol_data['hashtags']:
            for i, (tag, count) in enumerate(kol_data['hashtags'][:10], 1):
                content += f"{i}. **#{tag}** - {count} 次提及\n"
        else:
            content += "*暂无数据*\n"
        
        content += "\n## 👥 热门提及\n\n"
        
        if kol_data['mentions']:
            for i, (mention, count) in enumerate(kol_data['mentions'][:5], 1):
                content += f"{i}. **@{mention}** - {count} 次\n"
        else:
            content += "*暂无数据*\n"
        
        content += "\n## 💬 热门推文\n\n"
        
        for tweet in kol_data['samples'][:8]:
            content += f"### @{tweet['username']}\n"
            content += f"{tweet['text']}\n\n"
        
        if timeline:
            content += "\n## 📱 主页时间线预览\n\n"
            for text in timeline[:3]:
                content += f"- {text[:100]}...\n"
        
        content += f"\n---\n*数据来源: Nitter RSS + X Cookie | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        
        # 保存
        import os
        os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
        path = f'../reports/{year}/{month}/multi-source-{date_str}.md'
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 报告已保存: {path}")

if __name__ == "__main__":
    collector = XMultiSource()
    collector.generate_comprehensive_report()
