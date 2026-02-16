#!/usr/bin/env python3
"""
X 综合话题追踪系统 - 精简版
覆盖核心话题和 KOL
"""

import os
import sys
import time
import random
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from fetch_nitter_v2 import NitterRSSClient

class XTopicTracker:
    """X 话题追踪器"""
    
    def __init__(self):
        self.nitter = NitterRSSClient()
    
    # 精简配置 - 核心 KOL
    TOPICS = {
        "AI技术": {
            "kols": ["sama", "karpathy", "ylecun"],
            "keywords": ["AI", "LLM", "GPT", "Claude", "OpenAI"]
        },
        "Agent技术": {
            "kols": ["hwchase17", "jxnlco", "DrJimFan"],
            "keywords": ["MCP", "Agent", "LangChain"]
        },
        "投资": {
            "kols": ["chamath", "RayDalio", "jimcramer"],
            "keywords": ["NVDA", "TSLA", "stock", "market", "Bitcoin"]
        },
        "科技": {
            "kols": ["elonmusk", "pmarca", "paulg"],
            "keywords": ["SpaceX", "Tesla", "startup", "tech"]
        }
    }
    
    def collect_kol_tweets(self, category, kols):
        """收集 KOL 推文"""
        print(f"\n📊 [{category}] 收集 {len(kols)} 位 KOL...")
        
        tweets = []
        for username in kols:
            try:
                user_tweets = self.nitter.get_user_feed(username, max_items=2)
                for t in user_tweets:
                    tweets.append({
                        'username': username,
                        'text': t.get('text', ''),
                        'category': category
                    })
                time.sleep(random.uniform(0.5, 1))
            except:
                pass
        
        print(f"  ✅ 收集到 {len(tweets)} 条推文")
        return tweets
    
    def filter_by_keywords(self, tweets, keywords):
        """关键词过滤"""
        matched = []
        for tweet in tweets:
            text_lower = tweet['text'].lower()
            for kw in keywords:
                if kw.lower() in text_lower:
                    tweet['keyword'] = kw
                    matched.append(tweet)
                    break
        return matched
    
    def generate_report(self):
        """生成报告"""
        print("=" * 70)
        print(f"📈 X 话题追踪 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        all_results = {}
        
        for category, config in self.TOPICS.items():
            # 收集推文
            tweets = self.collect_kol_tweets(category, config['kols'])
            
            # 关键词过滤
            matched = self.filter_by_keywords(tweets, config['keywords'])
            
            if matched:
                all_results[category] = matched
                print(f"  🔥 {category}: {len(matched)} 条匹配")
        
        # 保存报告
        self._save_report(all_results)
        return all_results
    
    def _save_report(self, results):
        """保存报告"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        year = date_str[:4]
        month = date_str[5:7]
        
        os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
        
        content = f"""# X 话题追踪 | {date_str}

"""
        
        for category, tweets in results.items():
            content += f"\n## 🔹 {category}\n\n"
            for t in tweets[:5]:
                text = t['text'].replace('\n', ' ')[:150]
                if len(t['text']) > 150:
                    text += '...'
                content += f"**@{t['username']}** ({t.get('keyword', 'general')}):\n{text}\n\n"
        
        if not results:
            content += "*暂无匹配内容*\n"
        
        content += f"\n---\n*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        
        path = f'../reports/{year}/{month}/topics-latest.md'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 报告已保存: {path}")

if __name__ == "__main__":
    tracker = XTopicTracker()
    tracker.generate_report()
