#!/usr/bin/env python3
"""
简化版 X 数据获取
使用多种方法尝试获取真实数据
"""

import requests
import json
from datetime import datetime
import time
import random

class XSimpleFetcher:
    """简化版 X 数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # 从 .env.cookie 加载 Cookie
        self.auth_token = ''
        self.ct0 = ''
        
        env_file = '/home/openclawuser/.openclaw/workspace/daily-investor/.env.cookie'
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('X_AUTH_TOKEN='):
                        self.auth_token = line.split('=', 1)[1]
                    elif line.startswith('X_CT0='):
                        self.ct0 = line.split('=', 1)[1]
        except Exception as e:
            print(f"⚠️ 读取 Cookie 失败：{e}")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
        }
        
        if self.auth_token and self.ct0:
            self.headers['x-csrf-token'] = self.ct0[:32]
            self.headers['Cookie'] = f'auth_token={self.auth_token}; ct0={self.ct0}'
    
    def fetch_for_you(self, count=50):
        """获取为你推荐"""
        print("📡 获取为你推荐...")
        return self._fetch_timeline('HomeTimeline', count)
    
    def fetch_following(self, count=50):
        """获取正在关注"""
        print("📡 获取正在关注...")
        return self._fetch_timeline('HomeLatestTimeline', count)
    
    def _fetch_timeline(self, query_name, count):
        """获取时间线"""
        url = f'https://api.x.com/graphql/{query_name}'
        
        variables = {
            'count': min(count, 100),
            'includePromotedContent': False,
            'withCommunity': False,
            'voice': False
        }
        
        features = {
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False
        }
        
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(features)
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tweets = self._parse_tweets(data)
                print(f"  ✅ 获取 {len(tweets)} 条")
                return tweets
            else:
                print(f"  ⚠️ HTTP {response.status_code}")
                print(f"  响应：{response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"  ❌ 错误：{e}")
            return []
    
    def _parse_tweets(self, data):
        """解析推文数据"""
        tweets = []
        
        try:
            instructions = data.get('data', {}).get('home', {}).get('home_timeline_urt', {}).get('instructions', [])
            
            for instruction in instructions:
                entries = instruction.get('entries', [])
                for entry in entries:
                    tweet_data = self._extract_tweet(entry)
                    if tweet_data:
                        tweets.append(tweet_data)
        except Exception as e:
            print(f"  解析错误：{e}")
        
        return tweets
    
    def _extract_tweet(self, entry):
        """提取单条推文"""
        try:
            content = entry.get('content', {})
            item_content = content.get('itemContent', {})
            tweet_results = item_content.get('tweet_results', {}).get('result', {})
            
            if not tweet_results or tweet_results.get('__typename') != 'Tweet':
                return None
            
            legacy = tweet_results.get('legacy', {})
            core = tweet_results.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
            
            likes = legacy.get('favorite_count', 0)
            retweets = legacy.get('retweet_count', 0)
            replies = legacy.get('reply_count', 0)
            
            return {
                'id': tweet_results.get('rest_id'),
                'text': legacy.get('full_text', ''),
                'author': core.get('screen_name', 'unknown'),
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'heat_score': likes + retweets * 1.5 + replies * 2,
                'created_at': legacy.get('created_at')
            }
        except Exception as e:
            return None


def main():
    print("=" * 60)
    print("🐦 X 数据获取测试 (@kejunz)")
    print("=" * 60)
    
    fetcher = XSimpleFetcher()
    
    if not fetcher.auth_token:
        print("\n⚠️ 未找到 Cookie，请检查 .env.cookie 文件")
        return
    
    print("\n✅ Cookie 已加载")
    print(f"   auth_token: {fetcher.auth_token[:16]}...")
    print(f"   ct0: {fetcher.ct0[:16]}...")
    
    # 测试获取
    print("\n" + "-" * 60)
    for_you = fetcher.fetch_for_you(50)
    time.sleep(random.uniform(1.0, 2.0))
    following = fetcher.fetch_following(50)
    
    print("\n" + "=" * 60)
    print(f"📊 结果汇总")
    print("=" * 60)
    print(f"为你推荐：{len(for_you)} 条")
    print(f"正在关注：{len(following)} 条")
    
    all_tweets = for_you + following
    
    if all_tweets:
        # 按热度排序
        sorted_tweets = sorted(all_tweets, key=lambda x: x['heat_score'], reverse=True)
        
        print(f"\n🏆 Top 5 热度推文:")
        for i, t in enumerate(sorted_tweets[:5], 1):
            text = t['text'][:50].replace('\n', ' ') + '...'
            print(f"{i}. @{t['author']} - 🔥{t['heat_score']:.0f}")
            print(f"   👍{t['likes']} 🔄{t['retweets']} 💬{t['replies']}")
            print(f"   {text}\n")
    else:
        print("\n⚠️ 未获取到推文，可能原因:")
        print("   1. Cookie 已过期 → 参考 COOKIE_GUIDE.md 更新")
        print("   2. API 限流 → 等待 15 分钟再试")
        print("   3. 网络问题 → 检查连接")


if __name__ == "__main__":
    main()
