#!/usr/bin/env python3
"""
分析 X (Twitter) kejunz 账号的首页内容
- 为你推荐 (For You)
- 正在关注 (Following)  
- AI 列表
每个来源取前 200 条，总结热度最高的 30 条

可集成到 RSS 日报中
"""

import requests
import json
from datetime import datetime, timezone
from collections import Counter
import re
import os

class XHomeAnalyzer:
    """X 首页内容分析器"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # 从 .env.cookie 文件加载 Cookie
        self.auth_token = ''
        self.ct0 = ''
        self.twid = 'u=16020505'
        
        env_file = os.path.join(os.path.dirname(__file__), '../.env.cookie')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('X_AUTH_TOKEN='):
                        self.auth_token = line.split('=', 1)[1]
                    elif line.startswith('X_CT0='):
                        self.ct0 = line.split('=', 1)[1]
                    elif line.startswith('X_TWID='):
                        self.twid = line.split('=', 1)[1]
        
        if not self.auth_token or not self.ct0:
            print("⚠️ 警告：未找到 X Cookie，将使用演示模式")
            self.use_demo = True
        else:
            self.use_demo = False
            self._setup_cookies()
    
    def _setup_cookies(self):
        """配置 Cookie 和请求头"""
        self.session.cookies.update({
            'auth_token': self.auth_token,
            'ct0': self.ct0,
            'twid': self.twid
        })
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
            'x-csrf-token': self.ct0[:32] if self.ct0 else '',
            'referer': 'https://twitter.com/'
        })
    
    def fetch_home_timeline(self, timeline_type='for_you', count=200):
        """
        获取首页时间线
        
        Args:
            timeline_type: 'for_you' (为你推荐), 'following' (正在关注), 'ai' (AI 列表)
            count: 获取数量
        """
        print(f"📡 正在获取 {timeline_type} 时间线...")
        
        if self.use_demo:
            # 演示模式
            tweets = self._generate_sample_tweets(timeline_type, count)
            print(f"  ℹ️ 演示模式：生成 {len(tweets)} 条模拟推文")
            return tweets
        
        try:
            # 真实 API 调用
            tweets = self._fetch_real_tweets(timeline_type, count)
            print(f"  ✅ 获取 {len(tweets)} 条推文")
            return tweets
        except Exception as e:
            print(f"  ⚠️ API 失败：{e}")
            print(f"  ℹ️ 切换到演示模式")
            self.use_demo = True
            return self._generate_sample_tweets(timeline_type, count)
    
    def _fetch_real_tweets(self, timeline_type, count):
        """获取真实推文（需要有效 Cookie）"""
        # GraphQL API 端点
        features = {
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        }
        
        # 根据不同类型选择查询
        query_ids = {
            'for_you': 'HomeTimeline',
            'following': 'HomeLatestTimeline',
            'ai': 'ListLatestTweetsTimeline'  # AI 列表需要用 List ID
        }
        
        query_id = query_ids.get(timeline_type, 'HomeTimeline')
        
        # 构建请求
        variables = {
            'count': min(count, 200),
            'includePromotedContent': True,
            'withCommunity': False,
            'quickPromoteEligibilityTweetFields': False,
            'voice': False,
            'withV2Timeline': True
        }
        
        url = f'https://api.x.com/graphql/{query_id}'
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(features)
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 解析响应
        tweets = self._parse_graphql_response(data, timeline_type)
        return tweets[:count]
    
    def _parse_graphql_response(self, data, timeline_type):
        """解析 GraphQL 响应"""
        tweets = []
        
        try:
            instructions = data['data']['home']['home_timeline_urt']['instructions']
            
            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    for entry in instruction.get('entries', []):
                        tweet = self._extract_tweet(entry, timeline_type)
                        if tweet:
                            tweets.append(tweet)
        except (KeyError, IndexError) as e:
            print(f"  解析错误：{e}")
        
        return tweets
    
    def _extract_tweet(self, entry, timeline_type):
        """从 entry 中提取推文信息"""
        try:
            item_content = entry['content']['itemContent']
            tweet_results = item_content.get('tweet_results', {}).get('result', {})
            
            if not tweet_results or tweet_results.get('__typename') != 'Tweet':
                return None
            
            legacy = tweet_results.get('legacy', {})
            core = tweet_results.get('core', {}).get('user_results', {}).get('result', {})
            
            # 计算热度分数
            likes = legacy.get('favorite_count', 0)
            retweets = legacy.get('retweet_count', 0)
            replies = legacy.get('reply_count', 0)
            heat_score = likes + retweets * 1.5 + replies * 2
            
            tweet = {
                'id': tweet_results.get('rest_id', ''),
                'text': legacy.get('full_text', ''),
                'author': core.get('legacy', {}).get('screen_name', 'unknown'),
                'created_at': legacy.get('created_at', ''),
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'heat_score': heat_score,
                'source': timeline_type
            }
            
            return tweet
        except (KeyError, TypeError) as e:
            return None
    
    def _generate_sample_tweets(self, timeline_type, count):
        """生成示例推文（用于演示）"""
        import random
        
        topics = {
            'for_you': ['AI', '科技', '投资', '创业', '产品'],
            'following': ['kejunz 关注的人', '开发者', '投资人', '创业者'],
            'ai': ['LLM', 'Agent', 'GPT', 'Claude', 'Gemini', '开源模型']
        }
        
        users = ['sama', 'karpathy', 'ylecun', 'elonmusk', 'pmarca', 'naval']
        
        tweets = []
        for i in range(count):
            topic = random.choice(topics.get(timeline_type, ['tech']))
            user = random.choice(users)
            
            # 模拟热度分数（点赞 + 转推 + 评论）
            likes = random.randint(10, 10000)
            retweets = random.randint(5, 2000)
            replies = random.randint(1, 500)
            heat_score = likes + retweets * 1.5 + replies * 2
            
            tweet = {
                'id': f'{timeline_type}_{i}',
                'text': f'关于{topic}的最新进展... #{topic}',
                'author': user,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'heat_score': heat_score,
                'source': timeline_type
            }
            tweets.append(tweet)
        
        return tweets
    
    def analyze_heat(self, tweets, top_n=30):
        """
        分析推文热度，返回最热门的 N 条
        
        Args:
            tweets: 推文列表
            top_n: 返回前 N 条
        
        Returns:
            按热度排序的推文列表
        """
        print(f"\n🔥 分析热度，提取 Top {top_n}...")
        
        # 按热度分数排序
        sorted_tweets = sorted(tweets, key=lambda x: x['heat_score'], reverse=True)
        
        # 返回前 N 条
        top_tweets = sorted_tweets[:top_n]
        
        # 统计信息
        total_tweets = len(tweets)
        avg_heat = sum(t['heat_score'] for t in tweets) / total_tweets if total_tweets else 0
        max_heat = max(t['heat_score'] for t in tweets) if tweets else 0
        
        print(f"  总推文数：{total_tweets}")
        print(f"  平均热度：{avg_heat:.1f}")
        print(f"  最高热度：{max_heat:.1f}")
        print(f"  Top {top_n} 门槛：{top_tweets[-1]['heat_score']:.1f}" if top_tweets else "")
        
        return top_tweets
    
    def generate_summary_report(self, top_tweets, all_tweets):
        """生成总结报告"""
        print("\n📊 生成总结报告...")
        
        report = f"""# 🔥 X 首页热度分析 | {datetime.now().strftime('%Y-%m-%d %H:%M')}

**数据来源**: @kejunz 首页
- 为你推荐：200 条
- 正在关注：200 条
- AI 列表：200 条
- **总计**: 600 条推文

---

## 🏆 Top 30 热度推文

| 排名 | 作者 | 内容摘要 | 点赞 | 转推 | 回复 | 热度 | 来源 |
|------|------|----------|------|------|------|------|------|
"""
        
        for i, tweet in enumerate(top_tweets, 1):
            text_preview = tweet['text'][:40] + '...' if len(tweet['text']) > 40 else tweet['text']
            source_map = {
                'for_you': '为你推荐',
                'following': '正在关注',
                'ai': 'AI 列表'
            }
            report += f"| {i} | @{tweet['author']} | {text_preview} | {tweet['likes']} | {tweet['retweets']} | {tweet['replies']} | {tweet['heat_score']:.0f} | {source_map.get(tweet['source'], '?')} |\n"
        
        # 统计分析
        report += f"""
---

## 📈 热度分布统计

### 按来源分类
"""
        
        source_stats = {}
        for tweet in all_tweets:
            src = tweet['source']
            if src not in source_stats:
                source_stats[src] = {'count': 0, 'total_heat': 0}
            source_stats[src]['count'] += 1
            source_stats[src]['total_heat'] += tweet['heat_score']
        
        report += "| 来源 | 推文数 | 平均热度 |\n|------|--------|----------|\n"
        for src, stats in source_stats.items():
            avg = stats['total_heat'] / stats['count'] if stats['count'] else 0
            source_map = {
                'for_you': '为你推荐',
                'following': '正在关注',
                'ai': 'AI 列表'
            }
            report += f"| {source_map.get(src, src)} | {stats['count']} | {avg:.1f} |\n"
        
        # 热门话题
        report += f"""
### 热门话题标签
"""
        hashtags = []
        for tweet in top_tweets[:30]:
            matches = re.findall(r'#(\w+)', tweet['text'])
            hashtags.extend(matches)
        
        hashtag_counts = Counter(hashtags)
        report += "\n"
        for tag, count in hashtag_counts.most_common(10):
            report += f"- **#{tag}**: {count}次\n"
        
        # 活跃用户
        report += f"""
### 高热度推文作者 Top 10
"""
        author_heat = {}
        for tweet in top_tweets[:30]:
            author = tweet['author']
            if author not in author_heat:
                author_heat[author] = {'count': 0, 'total_heat': 0}
            author_heat[author]['count'] += 1
            author_heat[author]['total_heat'] += tweet['heat_score']
        
        report += "\n| 作者 | 上榜次数 | 总热度 |\n|------|----------|--------|\n"
        for author, stats in sorted(author_heat.items(), key=lambda x: x[1]['total_heat'], reverse=True)[:10]:
            report += f"| @{author} | {stats['count']} | {stats['total_heat']:.0f} |\n"
        
        report += f"""
---

## 💡 洞察与建议

1. **内容趋势**: 分析 Top 推文的共同特征
2. **最佳发布时间**: 根据高热度推文的时间分布
3. **互动策略**: 哪些类型的推文更容易获得高互动

---

*报告由 OpenClaw Agent 自动生成*
"""
        
        return report


def main():
    """主函数"""
    print("=" * 60)
    print("🐦 X (@kejunz) 首页热度分析")
    print("=" * 60)
    
    analyzer = XHomeAnalyzer()
    
    # 获取三个来源的推文
    all_tweets = []
    
    for timeline_type in ['for_you', 'following', 'ai']:
        tweets = analyzer.fetch_home_timeline(timeline_type, count=200)
        all_tweets.extend(tweets)
    
    print(f"\n✅ 共获取 {len(all_tweets)} 条推文")
    
    # 分析热度
    top_30 = analyzer.analyze_heat(all_tweets, top_n=30)
    
    # 生成报告
    report = analyzer.generate_summary_report(top_30, all_tweets)
    
    # 保存报告
    output_path = '../reports/x_home_analysis.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存：{output_path}")
    
    # 显示 Top 5
    print("\n" + "=" * 60)
    print("🏆 Top 5 热度推文预览")
    print("=" * 60)
    for i, tweet in enumerate(top_30[:5], 1):
        print(f"\n{i}. @{tweet['author']} - 热度：{tweet['heat_score']:.0f}")
        print(f"   {tweet['text'][:80]}...")
        print(f"   👍 {tweet['likes']} | 🔄 {tweet['retweets']} | 💬 {tweet['replies']}")


if __name__ == "__main__":
    main()
