#!/usr/bin/env python3
"""
通过 Cookie 访问 X (Twitter)
无需 API Key，使用浏览器 Cookie 获取数据

使用方法：
1. 登录 X.com
2. F12 → Application → Cookies → https://twitter.com
3. 复制 auth_token 和 ct0
4. 更新 .env.cookie 文件
5. 运行脚本

注意：Cookie 有过期时间，失效后需重新获取
"""

import os
import json
import re
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    raise

class XCookieClient:
    """使用 Cookie 访问 X"""
    
    def __init__(self):
        self.auth_token = os.getenv('X_AUTH_TOKEN')
        self.ct0 = os.getenv('X_CT0')
        
        if not self.auth_token or not self.ct0:
            raise ValueError("X_AUTH_TOKEN 或 X_CT0 未设置，请检查 .env.cookie 文件")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://twitter.com/',
            'Origin': 'https://twitter.com',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-client-language': 'en',
            'x-csrf-token': self.ct0,
            'Cookie': f'auth_token={self.auth_token}; ct0={self.ct0}'
        })
        
        self.base_url = "https://twitter.com/i/api/graphql"
    
    def get_user_tweets(self, username, count=10):
        """
        获取用户推文
        
        Args:
            username: 用户名（不含 @）
            count: 获取数量
        """
        try:
            # 首先获取用户 ID
            user_id = self._get_user_id(username)
            if not user_id:
                print(f"  ❌ 无法获取用户 {username} 的 ID")
                return []
            
            # 获取推文
            tweets = self._fetch_tweets(user_id, count)
            return tweets
            
        except Exception as e:
            print(f"  ❌ 获取 {username} 推文失败: {e}")
            return []
    
    def _get_user_id(self, username):
        """获取用户 ID"""
        url = "https://api.twitter.com/graphql/G3KGOASz96MR-ucTmZNWyA/UserByScreenName"
        
        params = {
            'variables': json.dumps({
                'screen_name': username,
                'withSafetyModeUserFields': True
            }),
            'features': json.dumps({
                'hidden_profile_likes_enabled': True,
                'hidden_profile_subscriptions_enabled': True,
                'responsive_web_graphql_exclude_directive_enabled': True,
                'verified_phone_label_enabled': False,
                'subscriptions_verification_info_is_identity_verified_enabled': True,
                'subscriptions_verification_info_verified_since_enabled': True,
                'highlights_tweets_tab_ui_enabled': True,
                'responsive_web_twitter_article_notes_tab_enabled': False,
                'creator_subscriptions_tweet_preview_api_enabled': True,
                'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                'responsive_web_graphql_timeline_navigation_enabled': True
            })
        }
        
        response = self.session.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('data', {}).get('user', {})
            if user:
                return user.get('result', {}).get('rest_id')
        elif response.status_code == 403:
            print(f"  ⚠️ Cookie 可能已过期，请重新获取")
        
        return None
    
    def _fetch_tweets(self, user_id, count):
        """获取推文列表"""
        url = "https://twitter.com/i/api/graphql/QK8pLE4Ewt8zZgTtPD5CFw/UserTweets"
        
        variables = {
            "userId": user_id,
            "count": count,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True
        }
        
        features = {
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "c9s_tweet_anatomy_moderator_denied_tweets_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        }
        
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(features)
        }
        
        response = self.session.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"  ❌ 请求失败: {response.status_code}")
            return []
        
        data = response.json()
        
        # 解析推文
        tweets = []
        try:
            timeline = data.get('data', {}).get('user', {}).get('result', {}).get('timeline_v2', {}).get('timeline', {}).get('instructions', [])
            
            for instruction in timeline:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    
                    for entry in entries:
                        content = entry.get('content', {})
                        if content.get('entryType') == 'TimelineTimelineItem':
                            tweet_data = content.get('itemContent', {}).get('tweet_results', {}).get('result', {})
                            
                            if tweet_data:
                                legacy = tweet_data.get('legacy', {})
                                
                                # 跳过转发和回复
                                if legacy.get('retweeted') or legacy.get('in_reply_to_status_id_str'):
                                    continue
                                
                                tweet_text = legacy.get('full_text', '')
                                created_at = legacy.get('created_at', '')
                                
                                tweets.append({
                                    'text': self._clean_text(tweet_text),
                                    'created_at': created_at,
                                    'retweet_count': legacy.get('retweet_count', 0),
                                    'favorite_count': legacy.get('favorite_count', 0)
                                })
                                
                                if len(tweets) >= count:
                                    break
        except Exception as e:
            print(f"  ⚠️ 解析推文失败: {e}")
        
        return tweets
    
    def _clean_text(self, text):
        """清理推文文本"""
        # 移除 t.co 短链接
        text = re.sub(r'https?://t\.co/\w+', '', text)
        # 移除多余空格
        text = ' '.join(text.split())
        return text.strip()

def load_cookie_env(filepath=None):
    """加载 Cookie 环境变量"""
    if filepath is None:
        # 尝试多个路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, '.env.cookie'),
            os.path.join(script_dir, '..', '.env.cookie'),
            '.env.cookie'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
    
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# KOL 清单
KOL_LIST = {
    "美股宏观/科技": ["chamath", "RayDalio", "jimcramer"],
    "中概/港股": ["HaoHongCFA", "maoxian", "realDawningW"],
    "技术分析": ["traderstewie", "markminervini"],
    "宏观研究": ["biancoresearch", "downtownjbrown"],
    "价值投资": ["peterlynchquotes", "howardmarksbook"]
}

def fetch_kol_by_cookie(category=None, max_tweets=5):
    """通过 Cookie 获取 KOL 观点"""
    
    # 加载 Cookie
    load_cookie_env()
    
    try:
        client = XCookieClient()
    except ValueError as e:
        print(f"❌ {e}")
        return {}
    
    results = {}
    categories = [category] if category else KOL_LIST.keys()
    
    for cat in categories:
        results[cat] = []
        print(f"\n📊 获取 {cat} 的观点...")
        
        for username in KOL_LIST[cat]:
            try:
                tweets = client.get_user_tweets(username, max_tweets)
                
                if tweets:
                    results[cat].append({
                        'username': username,
                        'tweets': tweets
                    })
                    print(f"  ✅ @{username}: {len(tweets)} 条推文")
                else:
                    print(f"  ⚠️ @{username}: 无数据")
                    
                # 添加延迟避免被封
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ @{username}: {str(e)}")
    
    return results

def format_for_insights(results):
    """格式化为投资洞察"""
    insights = []
    
    for category, users in results.items():
        for user in users:
            if user['tweets']:
                tweet = user['tweets'][0]
                text = tweet['text']
                if len(text) > 120:
                    text = text[:120] + '...'
                
                insights.append({
                    'investor': f"@{user['username']}",
                    'view': text,
                    'market': category.split('/')[0],
                    'likes': tweet.get('favorite_count', 0),
                    'retweets': tweet.get('retweet_count', 0)
                })
    
    return insights

if __name__ == "__main__":
    print("=" * 60)
    print("X Cookie 方式获取 KOL 观点")
    print("=" * 60)
    
    # 测试获取
    results = fetch_kol_by_cookie(category="美股宏观/科技", max_tweets=3)
    
    if results:
        print("\n📋 结果预览:")
        print("-" * 60)
        
        insights = format_for_insights(results)
        for item in insights:
            print(f"\n{item['investor']} ({item['market']}) ❤️{item['likes']} 🔄{item['retweets']}:")
            print(f"  \"{item['view']}\"")
    else:
        print("\n❌ 未获取到数据，请检查 Cookie 是否有效")
        print("\n获取 Cookie 方法：")
        print("1. 浏览器登录 x.com")
        print("2. F12 → Application → Cookies → https://twitter.com")
        print("3. 复制 auth_token 和 ct0 的值")
        print("4. 更新 .env.cookie 文件")
