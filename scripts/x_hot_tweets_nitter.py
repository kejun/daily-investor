#!/usr/bin/env python3
"""
X 推文追踪器 - Nitter RSS 版本
抓取指定 KOL 的最新推文

注意：Nitter RSS 不包含互动数据（点赞/转发数），无法按热度筛选
"""

import os
import sys
import re
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict

# 添加父目录到路径以导入 Nitter 客户端
sys.path.insert(0, os.path.dirname(__file__))
from fetch_nitter_v2 import NitterRSSClient


class XHotTweetsTracker:
    """X 热门推文追踪器"""
    
    # 核心 KOL 列表（按领域分类）
    KOL_LIST = {
        "AI/LLM": [
            "sama", "karpathy", "ylecun", "DemisHassabis",
            "hardmaru", "Jim_Fan", "swyx", "natfriedman",
            "levelsio", "packyM"
        ],
        "Agent/MCP": [
            "hwchase17", "jxnlco", "DrJimFan", "yoheinakajima",
            "CalebPeffer", "ericciarla", "shreyashankar2"
        ],
        "投资/财经": [
            "chamath", "RayDalio", "jimcramer", "HaoHongCFA",
            "biancoresearch", "downtownjbrown", "michael_saylor"
        ],
        "科技/创业": [
            "elonmusk", "pmarca", "paulg", "sama",
            "levie", "dhh", " Naval"
        ],
        "开发者工具": [
            "fchollet", "jeremyphoward", "karan", "guigranda",
            "sophiebits", "addyosmani"
        ]
    }
    
    # 注意：Nitter RSS 不包含互动数据，无法按热度筛选
    # 以下阈值保留但实际不使用
    MIN_LIKES = None
    MIN_RETWEETS = None
    
    def __init__(self):
        self.nitter = NitterRSSClient()
        self.all_tweets = []
    

    
    def collect_tweets(self, categories: list = None, tweets_per_user: int = 10):
        """
        收集推文
        
        Args:
            categories: 要抓取的类别列表，None 表示全部
            tweets_per_user: 每个用户抓取多少条推文
        """
        categories = categories or list(self.KOL_LIST.keys())
        
        for category in categories:
            if category not in self.KOL_LIST:
                print(f"⚠️ 未知类别：{category}")
                continue
            
            kols = self.KOL_LIST[category]
            print(f"\n📊 [{category}] 抓取 {len(kols)} 位 KOL...")
            
            for username in kols:
                try:
                    tweets = self.nitter.get_user_feed(username, max_items=tweets_per_user)
                    
                    for tweet in tweets:
                        # 清理文本（移除可能的 HTML 残留）
                        clean_text = tweet.get('text', '').replace('\n', ' ').strip()
                        
                        tweet_data = {
                            'username': username,
                            'category': category,
                            'text': clean_text[:280],  # 限制长度
                            'link': tweet.get('link', ''),
                            'published': tweet.get('published', '')
                        }
                        
                        self.all_tweets.append(tweet_data)
                    
                    print(f"  ✅ @{username}: {len(tweets)} 条")
                    
                    # 避免请求过快
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    print(f"  ❌ @{username}: {e}")
        
        print(f"\n📈 总计抓取：{len(self.all_tweets)} 条推文")
    
    def get_latest_tweets(self, limit_per_category: int = 5):
        """
        获取最新推文（按类别分组）
        
        Args:
            limit_per_category: 每类别最多显示多少条
        """
        from collections import defaultdict
        
        by_category = defaultdict(list)
        for tweet in self.all_tweets:
            by_category[tweet['category']].append(tweet)
        
        # 每类别限制数量
        limited = []
        for cat, tweets in by_category.items():
            limited.extend(tweets[:limit_per_category])
        
        print(f"📊 最新推文：{len(limited)} 条")
        
        return limited
    
    def generate_report(self, tweets: list, output_path: str = None):
        """生成报告"""
        if not tweets:
            print("⚠️ 没有推文数据")
            return
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        time_str = datetime.now().strftime('%H:%M')
        
        if not output_path:
            os.makedirs('../reports/x-tracker', exist_ok=True)
            output_path = f'../reports/x-tracker/x-tracker-{date_str}.md'
        
        # 按类别分组
        by_category = defaultdict(list)
        for tweet in tweets:
            by_category[tweet['category']].append(tweet)
        
        content = f"""# 📱 X 推文追踪 | {date_str} {time_str}

> 基于 Nitter RSS 抓取指定 KOL 的最新推文

---

## 📊 概览

| 类别 | 推文数 |
|------|--------|
"""
        
        for cat, cat_tweets in by_category.items():
            content += f"| {cat} | {len(cat_tweets)} 条 |\n"
        
        content += f"\n**总计**: {len(tweets)} 条推文\n\n"
        content += "---\n\n"
        
        # 详细列表
        for category, cat_tweets in by_category.items():
            content += f"## {category}\n\n"
            
            for i, t in enumerate(cat_tweets, 1):
                text = t['text'].strip()
                
                # 转换链接
                link = t['link']
                if link and 'nitter' in link:
                    link = link.replace('nitter.net', 'x.com').replace('nitter.privacydev.net', 'x.com')
                
                content += f"### {i}. @{t['username']}\n\n"
                content += f"{text}\n\n"
                if link:
                    content += f"🔗 [查看原文]({link})\n\n"
        
        content += f"""---

## 📌 说明

- **数据来源**: X (Twitter) via Nitter RSS
- **更新时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
- **覆盖 KOL**: {sum(len(v) for v in self.KOL_LIST.values())} 位
- **注意**: Nitter RSS 不包含互动数据（点赞/转发数）

---
*本报告由 OpenClaw 自动生成*
"""
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 报告已保存：{output_path}")
        
        # 同时保存 JSON 格式
        json_path = output_path.replace('.md', '.json')
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tweets, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 数据已保存：{json_path}")
    
    def run(self, categories: list = None, tweets_per_user: int = 10, limit_per_category: int = 5):
        """运行完整流程"""
        print("=" * 70)
        print(f"📱 X 推文追踪器 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        # 收集
        self.collect_tweets(categories, tweets_per_user)
        
        # 获取最新推文
        latest_tweets = self.get_latest_tweets(limit_per_category)
        
        # 生成报告
        self.generate_report(latest_tweets)
        
        return latest_tweets


if __name__ == "__main__":
    tracker = XHotTweetsTracker()
    
    # 可以指定类别，如：["AI/LLM", "Agent/MCP"]
    # 每个用户抓取 5 条，每类别最多显示 5 条
    tracker.run(categories=None, tweets_per_user=5, limit_per_category=5)
