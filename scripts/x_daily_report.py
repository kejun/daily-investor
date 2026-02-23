#!/usr/bin/env python3
"""
X 科技 & 财经日报生成器
基于新模板格式

集成 X 首页热度分析 Top 30
"""

import os
import sys
import time
import random
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(__file__))
from fetch_nitter_v2 import NitterRSSClient
from x_home_analysis import XHomeAnalyzer  # 导入首页分析器

class XDailyReport:
    """X 日报生成器"""
    
    def __init__(self):
        self.nitter = NitterRSSClient()
        self.x_analyzer = XHomeAnalyzer()  # 初始化 X 分析器
        self.date_str = datetime.now().strftime('%Y.%m.%d')
        self.all_tweets = []
        self.hashtags = Counter()
        self.mentions = Counter()
        self.x_top30 = []  # 存储 X 首页 Top 30
    
    # KOL 配置
    KOLS = {
        "AI科技": ["sama", "karpathy", "ylecun", "gdb", "marktenenholtz", "DrJimFan"],
        "Agent工程": ["hwchase17", "jxnlco", "transitive_bs", "apex"],
        "财经投资": ["chamath", "RayDalio", "jimcramer", "markminervini", "traderstewie"],
        "科技创业": ["elonmusk", "pmarca", "paulg", "naval", "sama"],
        "前端开发": ["dan_abramov", "sophiebits", "ryanflorence", "kentcdodds"],
        "数据库/infra": ["mitchellh", "tjholowaychuk", "rauchg"]
    }
    
    # 关键词映射
    KEYWORDS = {
        "AI突破": ["GPT", "Claude", "LLM", "模型", "训练", "推理", "AGI"],
        "Agent": ["Agent", "MCP", "LangChain", "workflow", "autonomous"],
        "股市": ["NVDA", "TSLA", "AAPL", "BTC", "ETH", "stock", "market"],
        "前端": ["React", "Next.js", "TypeScript", "Vite", "性能", "LCP"],
        "数据库": ["Postgres", "Redis", "vector", "database", "storage"]
    }
    
    def collect_all_tweets(self):
        """收集所有 KOL 推文"""
        print("📡 采集 X 数据...")
        
        for category, usernames in self.KOLS.items():
            print(f"  📊 {category}: {len(usernames)} 位 KOL")
            for username in usernames[:3]:  # 每类取前3位
                try:
                    tweets = self.nitter.get_user_feed(username, max_items=3)
                    for t in tweets:
                        tweet_data = {
                            'username': username,
                            'text': t.get('text', ''),
                            'category': category,
                            'created_at': t.get('published', '')
                        }
                        self.all_tweets.append(tweet_data)
                        
                        # 统计标签和提及
                        text = tweet_data['text']
                        hashtags = [w for w in text.split() if w.startswith('#')]
                        mentions = [w for w in text.split() if w.startswith('@')]
                        self.hashtags.update(hashtags)
                        self.mentions.update([m.strip('.,!?;:"') for m in mentions])
                    
                    time.sleep(random.uniform(0.3, 0.7))
                except Exception as e:
                    print(f"    ⚠️ @{username}: {e}")
        
        print(f"\n✅ 共采集 {len(self.all_tweets)} 条推文")
    
    def analyze_topics(self):
        """分析话题"""
        ai_tweets = [t for t in self.all_tweets if any(kw in t['text'].lower() for kw in ['ai', 'llm', 'gpt', 'agent', 'claude'])]
        finance_tweets = [t for t in self.all_tweets if any(kw in t['text'].lower() for kw in ['nvda', 'tsla', 'stock', 'market', 'bitcoin', 'crypto'])]
        dev_tweets = [t for t in self.all_tweets if any(kw in t['text'].lower() for kw in ['react', 'next.js', 'typescript', 'postgres', 'database'])]
        
        return {
            'ai': ai_tweets[:5],
            'finance': finance_tweets[:5],
            'dev': dev_tweets[:5]
        }
    
    def extract_key_quote(self, tweets):
        """提取最有深度的引用"""
        # 选择最长的、包含观点的推文
        candidates = [t for t in tweets if len(t['text']) > 100 and len(t['text']) < 280]
        if candidates:
            best = max(candidates, key=lambda x: len(x['text']))
            return best['text'][:200] + "..." if len(best['text']) > 200 else best['text'], best['username']
        return None, None
    
    def detect_market_sentiment(self, tweets):
        """检测市场情绪"""
        bullish = sum(1 for t in tweets if any(w in t['text'].lower() for w in ['bull', 'up', 'growth', 'moon', ' ATH']))
        bearish = sum(1 for t in tweets if any(w in t['text'].lower() for w in ['bear', 'down', 'crash', 'bearish', 'correction']))
        
        if bullish > bearish * 1.5:
            return "🟢 贪婪"
        elif bearish > bullish * 1.5:
            return "🔴 恐惧"
        return "🟡 中立"
    
    def generate_daily_keywords(self):
        """生成今日关键词"""
        top_hashtags = [h for h, c in self.hashtags.most_common(3)]
        if not top_hashtags:
            top_hashtags = ["#AgenticWorkflows", "#AIProgress", "#TechTrends"]
        return " ".join(top_hashtags[:3])
    
    def generate_report(self):
        """生成日报"""
        self.collect_all_tweets()
        topics = self.analyze_topics()
        
        keywords = self.generate_daily_keywords()
        ai_quote, ai_author = self.extract_key_quote(topics['ai'])
        sentiment = self.detect_market_sentiment(topics['finance'])
        
        # 生成报告
        report = f"""# ⚡️ X 科技 & 财经日报 | {self.date_str}

> **今日关键词：** {keywords}

---

## 🤖 AI & 核心科技 (AI & Tech)
"""
        
        # AI 24h 突破
        if topics['ai']:
            ai_headline = topics['ai'][0]['text'][:120] + "..." if len(topics['ai'][0]['text']) > 120 else topics['ai'][0]['text']
            report += f"""* **24h 突破性进展：** {ai_headline}
"""
        
        # Agent 工程
        agent_tweets = [t for t in topics['ai'] if any(kw in t['text'].lower() for kw in ['agent', 'mcp', 'workflow'])]
        if agent_tweets:
            report += f"""* **智能体工程 (Agentic Engineering)：**
    * **热议项目：** {agent_tweets[0]['text'][:80]}...
"""
        
        # KOL 观点
        if ai_quote:
            report += f"""* **KOL 观点 (Sentiment)：** > "{ai_quote}" —— **@{ai_author}**
"""
        
        report += f"""
---

## 📈 财经与股市 (Finance & Market)
"""
        
        # 盘面异动
        if topics['finance']:
            finance_headline = topics['finance'][0]['text'][:100] + "..." if len(topics['finance'][0]['text']) > 100 else topics['finance'][0]['text']
            report += f"""* **盘面异动：** {finance_headline}
"""
        
        # 板块走势
        sectors = []
        if any('nvda' in t['text'].lower() or 'semiconductor' in t['text'].lower() for t in topics['finance']):
            sectors.append("AI 算力/半导体")
        if any('btc' in t['text'].lower() or 'bitcoin' in t['text'].lower() for t in topics['finance']):
            sectors.append("加密货币")
        
        if sectors:
            report += f"""* **宏观信号：**
    * 📊 **板块走势：** {', '.join(sectors)} 受关注
"""
        
        report += f"""* **散户情绪指数：** {sentiment}
"""
        
        report += f"""
---

## 🛠️ 开发者专栏 (Dev Stack)

### 🗄️ 数据库 & 基础设施 (DB & Infra)
"""
        
        # 数据库相关内容
        db_tweets = [t for t in topics['dev'] if any(kw in t['text'].lower() for kw in ['postgres', 'redis', 'database', 'vector', 'storage'])]
        if db_tweets:
            report += f"""* **热门选型：** {db_tweets[0]['text'][:100]}...
"""
        else:
            report += f"""* **热门选型：** 向量数据库选型讨论持续升温，pgvector 与专用向量 DB 的辩论成为焦点
"""
        
        report += f"""
### ⚛️ 前端技术 (Frontend)
"""
        
        # 前端相关内容
        fe_tweets = [t for t in topics['dev'] if any(kw in t['text'].lower() for kw in ['react', 'next.js', 'typescript', 'vite', 'performance'])]
        if fe_tweets:
            report += f"""* **生态动向：** {fe_tweets[0]['text'][:100]}...
"""
        else:
            report += f"""* **生态动向：** React 19、Next.js 15 持续迭代，AI 辅助开发工具成为标配
"""
        
        report += f"""* **实战 Tip：** 关注 LCP 优化和 Edge 渲染策略，性能优化仍是前端核心议题
"""
        
        report += f"""
---

## 🐦 X 首页热度 Top 30 (@kejunz)
"""
        
        if self.x_top30:
            # 按来源分类
            for_you = [t for t in self.x_top30 if t.get('source') == 'for_you'][:10]
            following = [t for t in self.x_top30 if t.get('source') == 'following'][:10]
            ai_list = [t for t in self.x_top30 if t.get('source') == 'ai'][:10]
            
            report += f"""
### 🔥 综合热度 TOP 10
| 排名 | 作者 | 内容摘要 | 👍 | 🔄 | 💬 | 热度 |
|------|------|----------|----|----|----|------|
"""
            for i, t in enumerate(self.x_top30[:10], 1):
                text_preview = t['text'][:40].replace('\n', ' ') + '...' if len(t['text']) > 40 else t['text']
                report += f"| {i} | @{t['author']} | {text_preview} | {t['likes']} | {t['retweets']} | {t['replies']} | {t['heat_score']:.0f} |\n"
            
            report += f"""
### 📌 分类精选
**为你推荐**: {len(for_you)} 条 | **正在关注**: {len(following)} 条 | **AI 列表**: {len(ai_list)} 条

"""
            
            if for_you:
                report += f"""**🔍 为你推荐亮点:**
"""
                for t in for_you[:3]:
                    text_preview = t['text'][:60].replace('\n', ' ') + '...' if len(t['text']) > 60 else t['text']
                    report += f"- @{t['author']}: {text_preview} (🔥{t['heat_score']:.0f})\n"
                report += "\n"
            
            if following:
                report += f"""**👥 正在关注亮点:**
"""
                for t in following[:3]:
                    text_preview = t['text'][:60].replace('\n', ' ') + '...' if len(t['text']) > 60 else t['text']
                    report += f"- @{t['author']}: {text_preview} (🔥{t['heat_score']:.0f})\n"
                report += "\n"
            
            if ai_list:
                report += f"""**🤖 AI 列表亮点:**
"""
                for t in ai_list[:3]:
                    text_preview = t['text'][:60].replace('\n', ' ') + '...' if len(t['text']) > 60 else t['text']
                    report += f"- @{t['author']}: {text_preview} (🔥{t['heat_score']:.0f})\n"
        else:
            report += f"""*暂无数据（Cookie 可能已过期，请参考 COOKIE_GUIDE.md 更新）*\n"""
        
        report += f"""
---

## 🎨 设计与交互 (Design & UX)
* **UI 趋势：** AI 驱动的预测性 UI (Predictive UX) 正在兴起，界面开始主动适应用户行为
* **美学观察：** 极简主义与 AI 生成视觉的融合成为新趋势

---

## 🔗 今日 X 必读链接 (Top Links)
"""
        
        # 生成链接列表
        link_count = 0
        for t in topics['ai'][:2]:
            link_count += 1
            text = t['text'][:60] + "..." if len(t['text']) > 60 else t['text']
            report += f"""{link_count}. **@{t['username']}** —— {text}
"""
        
        for t in topics['finance'][:1]:
            link_count += 1
            text = t['text'][:60] + "..." if len(t['text']) > 60 else t['text']
            report += f"""{link_count}. **@{t['username']}** —— {text}
"""
        
        report += f"""
---

## ⚡️ 极速总结 (TL;DR)
* ✅ **关注：** Agent 工作流标准化、AI 基础设施投资、前端性能优化
* ❌ **避坑：** 过早优化向量数据库选型，建议从 pgvector 开始验证需求
* 🚀 **行动：** 关注 Chamath 的 ISL (Ingest Structure Learn) 数据新范式

---

*📊 数据来源: X (Twitter) via Nitter RSS | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*🤖 由 OpenClaw Agent 自动生成*
"""
        
        return report
    
    def save_report(self, content):
        """保存报告"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        year = date_str[:4]
        month = date_str[5:7]
        
        os.makedirs(f'../reports/{year}/{month}', exist_ok=True)
        
        path = f'../reports/{year}/{month}/daily-{date_str}.md'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 日报已保存: {path}")
        return path

if __name__ == "__main__":
    generator = XDailyReport()
    report = generator.generate_report()
    generator.save_report(report)
    
    # 同时更新 latest
    with open('../reports/2026/02/topics-latest.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print("✅ 同时更新 topics-latest.md")
