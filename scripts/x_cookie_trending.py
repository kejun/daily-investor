#!/usr/bin/env python3
"""
X Cookie 方案 - 搜索热门话题和推文
使用 twid + ct0 访问公开数据
"""

import os
import requests
import json
from datetime import datetime

def load_env(filepath='.env.cookie'):
    """加载环境变量"""
    env = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key] = value
                    os.environ[key] = value
    return env

class XCookieSearch:
    """使用 Cookie 搜索 X 内容"""
    
    def __init__(self):
        # 尝试加载环境变量
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, '.env.cookie'),
            os.path.join(script_dir, '..', '.env.cookie'),
            '.env.cookie'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                load_env(path)
                break
        
        self.ct0 = os.getenv('X_CT0')
        self.twid = os.getenv('X_TWID')
        
        if not self.ct0 or not self.twid:
            raise ValueError("X_CT0 或 X_TWID 未设置")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://x.com/',
            'Cookie': f'ct0={self.ct0}; twid={self.twid}'
        }
    
    def get_trending_topics(self):
        """
        获取热门话题（通过主页 HTML 解析）
        
        注意：由于 API 限制，这里使用网页解析方式
        """
        print("🔥 获取热门话题...")
        
        try:
            # 访问探索页面
            url = 'https://x.com/explore/tabs/trending'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ 访问失败: {response.status_code}")
                return []
            
            # 从页面中提取趋势话题
            # X 的趋势话题通常在 JSON 数据中
            topics = []
            
            # 尝试从页面脚本中提取
            import re
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL)
            
            for script in scripts:
                if 'trend' in script.lower() or 'Trend' in script:
                    # 尝试提取趋势数据
                    trends_match = re.findall(r'"trend"[:\s]*\{[^}]*"name"[:\s]*"([^"]+)"', script)
                    if trends_match:
                        topics.extend(trends_match[:10])
            
            # 备用：从页面文本中提取常见趋势格式
            if not topics:
                # 查找 #话题 格式
                hashtag_pattern = r'#([\w\u4e00-\u9fff]+)'
                hashtags = re.findall(hashtag_pattern, response.text)
                topics = list(set(hashtags))[:10]
            
            return topics
            
        except Exception as e:
            print(f"❌ 获取热门话题失败: {e}")
            return []
    
    def search_tweets(self, query, count=10):
        """
        搜索推文（使用搜索页面）
        
        Args:
            query: 搜索关键词
            count: 返回数量
        """
        print(f"🔍 搜索: '{query}'...")
        
        try:
            # 使用 X 搜索页面
            url = f'https://x.com/search'
            params = {
                'q': query,
                'src': 'typed_query',
                'f': 'live'  # 最新推文
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ 搜索失败: {response.status_code}")
                return []
            
            # 从 HTML 中提取推文内容
            tweets = []
            import re
            
            # 尝试多种推文文本模式
            text_patterns = [
                r'"text"[:\s]*"([^"]{20,280})"',  # JSON 格式
                r'<div[^>]*data-testid="tweetText"[^>]*>(.*?)</div>',  # HTML 格式
                r'<span[^>]*>([^<]{30,280})</span>',  # 通用文本
            ]
            
            for pattern in text_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    # 清理 HTML 标签
                    clean_text = re.sub(r'<[^>]+>', '', match)
                    clean_text = clean_text.replace('&quot;', '"').replace('&amp;', '&')
                    
                    if len(clean_text) > 20 and clean_text not in [t['text'] for t in tweets]:
                        tweets.append({
                            'text': clean_text[:200],
                            'query': query
                        })
                    
                    if len(tweets) >= count:
                        break
                
                if len(tweets) >= count:
                    break
            
            return tweets[:count]
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def get_user_tweets_html(self, username, count=5):
        """
        获取用户推文（HTML 解析方式）
        
        Args:
            username: 用户名（不含 @）
            count: 返回数量
        """
        print(f"📱 获取 @{username} 的推文...")
        
        try:
            url = f'https://x.com/{username}'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ 获取失败: {response.status_code}")
                return []
            
            tweets = []
            import re
            
            # 从页面中提取推文文本
            # X 的推文通常在特定的 data-testid 属性中
            text_matches = re.findall(r'"text"[:\s]*"([^"]{10,280})"', response.text)
            
            for text in text_matches[:count]:
                clean_text = text.replace('\\n', ' ').replace('\\"', '"')
                if len(clean_text) > 10:
                    tweets.append({
                        'text': clean_text[:200],
                        'username': username
                    })
            
            return tweets
            
        except Exception as e:
            print(f"❌ 获取失败: {e}")
            return []

def generate_trending_report():
    """生成热门话题报告"""
    print("=" * 70)
    print(f"📊 X 热门话题报告 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    try:
        x = XCookieSearch()
        
        # 获取热门话题
        print("\n🔥 热门话题:")
        topics = x.get_trending_topics()
        if topics:
            for i, topic in enumerate(topics[:10], 1):
                print(f"  {i}. #{topic}")
        else:
            print("  ⚠️ 无法获取热门话题")
        
        # 搜索特定关键词
        search_queries = [
            "AI investment",
            "stock market",
            "Bitcoin",
            "NVDA"
        ]
        
        print("\n📈 热门讨论:")
        all_tweets = []
        for query in search_queries:
            tweets = x.search_tweets(query, count=3)
            if tweets:
                print(f"\n  🔍 {query}:")
                for tweet in tweets[:2]:
                    print(f"    - {tweet['text'][:100]}...")
                all_tweets.extend(tweets)
        
        # 保存报告
        report = f"""# X 热门话题报告 | {datetime.now().strftime('%Y-%m-%d')}

## 🔥 热门话题

"""
        if topics:
            for i, topic in enumerate(topics[:10], 1):
                report += f"{i}. #{topic}\n"
        
        report += f"\n## 📈 热门讨论\n\n"
        
        for query in search_queries:
            report += f"### {query}\n"
            tweets = x.search_tweets(query, count=2)
            for tweet in tweets:
                report += f"- {tweet['text'][:150]}...\n"
            report += "\n"
        
        report += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        
        # 保存到文件
        date_str = datetime.now().strftime('%Y-%m-%d')
        year = date_str[:4]
        month = date_str[5:7]
        
        os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
        report_path = f'../reports/{year}/{month}/trending-{date_str}.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 报告已保存: {report_path}")
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")

if __name__ == "__main__":
    generate_trending_report()
