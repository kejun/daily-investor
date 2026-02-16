#!/usr/bin/env python3
"""
X (Twitter) API 客户端
用于获取投资者 KOL 的最新观点
"""

import os
import json
import requests
from datetime import datetime, timedelta

def load_env_file(filepath='.env'):
    """手动加载 .env 文件"""
    env = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key] = value
    return env

# 加载环境变量
env = load_env_file()
os.environ.update(env)

class XAPIClient:
    def __init__(self):
        self.bearer_token = os.getenv('X_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("X_BEARER_TOKEN not found in .env file")
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.twitter.com/2"
    
    def get_user_by_username(self, username):
        """获取用户信息"""
        url = f"{self.base_url}/users/by/username/{username}"
        params = {
            "user.fields": "public_metrics,description,created_at"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json().get('data')
        else:
            print(f"Error getting user {username}: {response.status_code}")
            print(response.text)
            return None
    
    def get_user_tweets(self, user_id, max_results=10):
        """获取用户最近推文"""
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,context_annotations",
            "exclude": "replies,retweets"  # 只获取原创推文
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Error getting tweets: {response.status_code}")
            print(response.text)
            return []
    
    def search_tweets(self, query, max_results=10):
        """搜索推文"""
        url = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Error searching tweets: {response.status_code}")
            print(response.text)
            return []

# KOL 清单
KOL_LIST = {
    "美股宏观/科技": ["chamath", "RayDalio", "jimcramer"],
    "中概/港股": ["HaoHongCFA", "maoxian", "realDawningW"],
    "技术分析": ["traderstewie", "markminervini"],
    "宏观研究": ["biancoresearch", "downtownjbrown"],
    "价值投资": ["peterlynchquotes", "howardmarksbook"]
}

def fetch_kol_insights(category=None, max_tweets=5):
    """
    获取 KOL 最新观点
    
    Args:
        category: 分类名称（如"美股宏观/科技"），None 表示全部
        max_tweets: 每个 KOL 获取的推文数量
    """
    client = XAPIClient()
    insights = {}
    
    categories = [category] if category else KOL_LIST.keys()
    
    for cat in categories:
        insights[cat] = []
        print(f"\n📊 获取 {cat} 的观点...")
        
        for username in KOL_LIST[cat]:
            try:
                # 获取用户信息
                user = client.get_user_by_username(username)
                if not user:
                    continue
                
                user_id = user['id']
                name = user.get('name', username)
                
                # 获取最近推文
                tweets = client.get_user_tweets(user_id, max_results=max_tweets)
                
                if tweets:
                    insights[cat].append({
                        'username': username,
                        'name': name,
                        'tweets': tweets
                    })
                    print(f"  ✅ @{username}: {len(tweets)} 条推文")
                else:
                    print(f"  ⚠️ @{username}: 无推文")
                    
            except Exception as e:
                print(f"  ❌ @{username}: {str(e)}")
    
    return insights

def format_for_report(insights):
    """格式化为投资洞察报告格式"""
    formatted = []
    
    for category, users in insights.items():
        for user in users:
            for tweet in user['tweets'][:1]:  # 只取最新一条
                text = tweet['text'].replace('\n', ' ')
                if len(text) > 100:
                    text = text[:100] + '...'
                
                formatted.append({
                    'investor': f"@{user['username']}",
                    'view': text,
                    'category': category.split('/')[0]
                })
    
    return formatted

if __name__ == "__main__":
    # 测试：获取所有 KOL 的最新观点
    print("=" * 60)
    print("X API 测试 - 获取投资者观点")
    print("=" * 60)
    
    # 先测试单个用户
    client = XAPIClient()
    print("\n🧪 测试获取 @chamath 的信息...")
    user = client.get_user_by_username("chamath")
    if user:
        print(f"✅ 成功: {user['name']} (@{user['username']})")
        print(f"   描述: {user.get('description', 'N/A')[:50]}...")
        
        # 获取推文
        tweets = client.get_user_tweets(user['id'], max_results=3)
        print(f"\n📱 最新 {len(tweets)} 条推文:")
        for i, tweet in enumerate(tweets, 1):
            text = tweet['text'].replace('\n', ' ')[:80]
            print(f"   {i}. {text}...")
    else:
        print("❌ 获取失败")
    
    # 测试搜索
    print("\n🔍 测试搜索 'AI stock'...")
    search_results = client.search_tweets("AI stock", max_results=3)
    print(f"找到 {len(search_results)} 条相关推文")
