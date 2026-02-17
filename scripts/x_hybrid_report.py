#!/usr/bin/env python3
"""
综合方案：RSS + Cookie
1. RSS：获取 KOL 最新推文（稳定可靠）
2. Cookie：获取主页时间线（补充）
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import time

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))
from fetch_nitter_v2 import NitterRSSClient

class XHybridClient:
    """混合方案客户端"""
    
    def __init__(self):
        self.rss_client = NitterRSSClient()
        self._load_cookie()
    
    def _load_cookie(self):
        """加载 cookie"""
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
    
    def get_popular_topics_from_kols(self):
        """
        从 KOL 推文中提取热门话题
        分析推文中的标签和关键词
        """
        # 投资相关 KOL
        kols = [
            'chamath',      # 科技投资
            'RayDalio',     # 宏观
            'jimcramer',    # 美股
            'biancoresearch', # 研究
        ]
        
        print("📊 分析 KOL 推文提取热门话题...")
        
        all_text = []
        for username in kols:
            try:
                tweets = self.rss_client.get_user_feed(username, max_items=5)
                for tweet in tweets:
                    all_text.append(tweet.get('text', ''))
                time.sleep(1)
            except:
                continue
        
        # 提取标签
        hashtags = []
        for text in all_text:
            found = re.findall(r'#(\w+)', text)
            hashtags.extend(found)
        
        # 统计频率
        from collections import Counter
        top_tags = Counter(hashtags).most_common(15)
        
        return top_tags
    
    def get_market_sentiment(self):
        """
        获取市场情绪
        分析交易员的推文情感
        """
        traders = ['traderstewie', 'markminervini', 'sentimentrader']
        
        print("📈 获取市场情绪...")
        
        sentiments = []
        for username in traders:
            try:
                tweets = self.rss_client.get_user_feed(username, max_items=3)
                if tweets:
                    latest = tweets[0]
                    sentiments.append({
                        'trader': username,
                        'text': latest['text'][:100] + '...' if len(latest['text']) > 100 else latest['text'],
                        'time': latest.get('published', '')
                    })
                time.sleep(1)
            except:
                continue
        
        return sentiments
    
    def generate_hybrid_report(self):
        """生成综合报告"""
        print("=" * 70)
        print(f"📊 X 热门话题综合报告 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        # 1. 热门话题
        print("\n🔥 热门话题（来自KOL推文分析）:")
        topics = self.get_popular_topics_from_kols()
        if topics:
            for i, (tag, count) in enumerate(topics[:10], 1):
                print(f"  {i}. #{tag} (出现{count}次)")
        else:
            print("  ⚠️ 暂无数据")
        
        # 2. 市场情绪
        print("\n💭 市场情绪:")
        sentiments = self.get_market_sentiment()
        if sentiments:
            for s in sentiments:
                print(f"  @{s['trader']}: {s['text']}")
        else:
            print("  ⚠️ 暂无数据")
        
        # 3. 生成报告文件
        report = self._create_report(topics, sentiments)
        return report
    
    def _create_report(self, topics, sentiments):
        """创建报告文件"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        year = date_str[:4]
        month = date_str[5:7]
        
        content = f"""# X 热门话题综合报告 | {date_str}

## 🔥 热门话题（基于KOL推文分析）

"""
        
        if topics:
            for i, (tag, count) in enumerate(topics[:10], 1):
                content += f"{i}. **#{tag}** - 出现 {count} 次\n"
        else:
            content += "*暂无数据*\n"
        
        content += "\n## 💭 市场情绪\n\n"
        
        if sentiments:
            for s in sentiments:
                content += f"### @{s['trader']}\n"
                content += f"{s['text']}\n\n"
        else:
            content += "*暂无数据*\n"
        
        content += f"\n---\n*数据来源: Nitter RSS + X Cookie | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
        
        # 保存
        import os
        os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
        path = f'../reports/{year}/{month}/hybrid-{date_str}.md'
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 报告已保存: {path}")
        return path

if __name__ == "__main__":
    client = XHybridClient()
    client.generate_hybrid_report()
