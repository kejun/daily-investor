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
            "keywords": ["AI", "LLM", "GPT", "Claude", "OpenAI"],
            "name_zh": "人工智能"
        },
        "Agent技术": {
            "kols": ["hwchase17", "jxnlco", "DrJimFan"],
            "keywords": ["MCP", "Agent", "LangChain"],
            "name_zh": "AI智能体"
        },
        "投资": {
            "kols": ["chamath", "RayDalio", "jimcramer"],
            "keywords": ["NVDA", "TSLA", "stock", "market", "Bitcoin"],
            "name_zh": "投资理财"
        },
        "科技": {
            "kols": ["elonmusk", "pmarca", "paulg"],
            "keywords": ["SpaceX", "Tesla", "startup", "tech"],
            "name_zh": "科技动态"
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
        print(f"📈 X (Twitter) 热门话题追踪 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        all_results = {}
        
        for category, config in self.TOPICS.items():
            # 收集推文
            tweets = self.collect_kol_tweets(category, config['kols'])
            
            # 关键词过滤
            matched = self.filter_by_keywords(tweets, config['keywords'])
            
            if matched:
                all_results[category] = matched
                name_zh = config.get('name_zh', category)
                print(f"  🔥 {name_zh}: {len(matched)} 条相关推文")
        
        # 保存报告
        self._save_report(all_results)
        return all_results
    
    def _save_report(self, results):
        """保存中文报告"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        time_str = datetime.now().strftime('%H:%M')
        year = date_str[:4]
        month = date_str[5:7]
        
        os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
        
        content = f"""# 📱 X (Twitter) 热门话题追踪 | {date_str} {time_str}

> 自动采集 X 平台热门话题，覆盖 AI、Agent、投资、科技四大领域

---

## 📊 今日概览

"""
        
        if results:
            content += "| 类别 | 相关推文数 |\n"
            content += "|------|-----------|\n"
            for category, tweets in results.items():
                config = self.TOPICS.get(category, {})
                name_zh = config.get('name_zh', category)
                content += f"| {name_zh} | {len(tweets)} 条 |\n"
        else:
            content += "*今日暂无匹配内容*\n"
        
        content += "\n---\n\n"
        
        for category, tweets in results.items():
            config = self.TOPICS.get(category, {})
            name_zh = config.get('name_zh', category)
            
            content += f"## 🔥 {name_zh}\n\n"
            content += f"*关键词: {', '.join(config.get('keywords', [])[:5])}*\n\n"
            
            for i, t in enumerate(tweets[:8], 1):
                text = t['text'].replace('\n', ' ')
                # 保留原文，但截断显示
                if len(text) > 200:
                    display_text = text[:200] + '...'
                else:
                    display_text = text
                
                keyword = t.get('keyword', 'general')
                content += f"**{i}. @{t['username']}** [匹配: {keyword}]\n"
                content += f"> {display_text}\n\n"
        
        if not results:
            content += "## 📭 无数据\n\n"
            content += "今日暂无匹配的推文内容。\n"
        
        content += f"""
---

## 📌 说明

- **数据来源**: X (Twitter) via Nitter RSS
- **更新时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
- **采集方式**: 自动抓取核心 KOL 推文并匹配关键词
- **覆盖领域**: 人工智能、AI智能体、投资理财、科技动态

---
*本报告由 OpenClaw 自动生成*
"""
        
        path = f'../reports/{year}/{month}/topics-latest.md'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 中文报告已保存: {path}")

if __name__ == "__main__":
    tracker = XTopicTracker()
    tracker.generate_report()
