#!/usr/bin/env python3
"""
Reddit 热门话题挖掘工具（使用 RSS 源 + Web Search）

无需 API 凭证，使用 Reddit RSS 源抓取

用法：
    python3 reddit_trending_rss.py
"""

import feedparser
import json
from datetime import datetime
from typing import List, Dict, Any
import os
import requests

class RedditTrendingRSS:
    """Reddit 热门话题挖掘器（基于 RSS）"""
    
    # 目标 Subreddits
    SUBREDDITS = {
        'ai': [
            'artificial',
            'MachineLearning',
            'LocalLLaMA',
            'singularity',
            'ChatGPT',
            'ClaudeAI',
            'OpenAI'
        ],
        'database': [
            'database',
            'PostgreSQL',
            'MongoDB',
            'redis',
            'sql',
            'ClickHouse'
        ],
        'tech': [
            'technology',
            'programming',
            'webdev',
            'devops',
            'coding'
        ]
    }
    
    def __init__(self, limit: int = 10):
        """
        初始化
        
        Args:
            limit: 每个 Subreddit 抓取帖子数量
        """
        self.limit = limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch_subreddit_rss(self, subreddit: str) -> List[Dict[str, Any]]:
        """
        通过 RSS 源抓取 Subreddit 热门帖子
        
        Args:
            subreddit: Subreddit 名称
            
        Returns:
            帖子列表
        """
        posts = []
        
        # Reddit RSS 源格式：https://www.reddit.com/r/{subreddit}/.rss
        rss_url = f'https://www.reddit.com/r/{subreddit}/.rss'
        
        try:
            resp = self.session.get(rss_url, timeout=30)
            resp.raise_for_status()
            
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries[:self.limit]:
                # 提取分数和评论数（Reddit RSS 中包含这些信息）
                title = entry.title if hasattr(entry, 'title') else ''
                link = entry.link if hasattr(entry, 'link') else ''
                
                # 尝试从摘要中提取分数
                score = 0
                num_comments = 0
                
                if hasattr(entry, 'summary'):
                    summary = entry.summary
                    # 尝试解析 "submitted by ... to ... | X comments | Y points"
                    if 'points' in summary:
                        try:
                            import re
                            points_match = re.search(r'(\d+)\s*points', summary)
                            if points_match:
                                score = int(points_match.group(1))
                            
                            comments_match = re.search(r'(\d+)\s*comments', summary)
                            if comments_match:
                                num_comments = int(comments_match.group(1))
                        except:
                            pass
                
                posts.append({
                    'subreddit': subreddit,
                    'title': title,
                    'url': link,
                    'score': score,
                    'num_comments': num_comments,
                    'published': entry.published if hasattr(entry, 'published') else '',
                    'author': entry.author if hasattr(entry, 'author') else 'unknown'
                })
            
            return posts
            
        except Exception as e:
            print(f"  ❌ 抓取 r/{subreddit} RSS 失败：{e}")
            return []
    
    def fetch_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """抓取所有目标 Subreddits"""
        results = {}
        
        for category, subreddits in self.SUBREDDITS.items():
            print(f"\n📂 抓取 {category} 类别...")
            results[category] = []
            
            for subreddit in subreddits:
                print(f"  └─ r/{subreddit}")
                posts = self.fetch_subreddit_rss(subreddit)
                results[category].extend(posts)
                
                # 按分数排序并保留 top
                results[category] = sorted(
                    results[category],
                    key=lambda x: x.get('score', 0),
                    reverse=True
                )[:self.limit]
        
        return results
    
    def generate_report(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成 Markdown 报告"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""# 🔥 Reddit 热门话题 | {now}

**数据来源**: Reddit RSS 源  
**抓取范围**: AI、数据库、技术类 Subreddits

---

## 📊 数据概览

| 类别 | Subreddits 数量 | 热门帖子数 |
|------|----------------|-----------|
"""
        
        for category, posts in results.items():
            count = len(self.SUBREDDITS.get(category, []))
            report += f"| {category.upper()} | {count} | {len(posts)} |\n"
        
        report += "\n---\n\n"
        
        # AI 类别
        if results.get('ai'):
            report += "## 🤖 AI 热门话题\n\n"
            for i, post in enumerate(results['ai'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post.get('score', 0):,}\n"
                report += f"- **评论**: 💬 {post.get('num_comments', 0)}\n"
                report += f"- **链接**: [🔗 {post['url']}]({post['url']})\n\n"
        
        # 数据库类别
        if results.get('database'):
            report += "## 🗄️ 数据库热门话题\n\n"
            for i, post in enumerate(results['database'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post.get('score', 0):,}\n"
                report += f"- **评论**: 💬 {post.get('num_comments', 0)}\n"
                report += f"- **链接**: [🔗 {post['url']}]({post['url']})\n\n"
        
        # 技术类别
        if results.get('tech'):
            report += "## 💻 技术热门话题\n\n"
            for i, post in enumerate(results['tech'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post.get('score', 0):,}\n"
                report += f"- **评论**: 💬 {post.get('num_comments', 0)}\n"
                report += f"- **链接**: [🔗 {post['url']}]({post['url']})\n\n"
        
        report += "---\n\n"
        report += f"*报告生成时间：{now} (Asia/Shanghai)*\n"
        
        return report
    
    def save_report(self, report: str, output_dir: str = None):
        """保存报告到文件"""
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'reports',
                'reddit'
            )
        
        os.makedirs(output_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_path = os.path.join(output_dir, f'{date_str}-reddit-trending.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 报告已保存：{output_path}")
        return output_path


def main():
    """主函数"""
    print("=" * 60)
    print("  Reddit 热门话题挖掘工具 (RSS)")
    print("=" * 60)
    
    # 检查依赖
    try:
        import feedparser
    except ImportError:
        print("\n❌ 缺少依赖：feedparser")
        print("请运行：pip install feedparser")
        return
    
    # 创建挖掘器
    miner = RedditTrendingRSS(limit=10)
    
    # 抓取数据
    results = miner.fetch_all()
    
    # 生成报告
    report = miner.generate_report(results)
    
    # 保存报告
    output_path = miner.save_report(report)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("  热门话题 TOP 5")
    print("=" * 60)
    
    all_posts = []
    for posts in results.values():
        all_posts.extend(posts)
    
    top_posts = sorted(all_posts, key=lambda x: x.get('score', 0), reverse=True)[:5]
    
    for i, post in enumerate(top_posts, 1):
        title = post.get('title', 'N/A')[:60]
        print(f"\n{i}. {title}...")
        print(f"   r/{post.get('subreddit', 'unknown')} | ⬆️ {post.get('score', 0):,} | 💬 {post.get('num_comments', 0)}")
    
    print("\n" + "=" * 60)
    print("  完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
