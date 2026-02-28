#!/usr/bin/env python3
"""
Reddit 热门话题挖掘工具
抓取 AI、数据库等相关 Subreddit 的热门帖子

用法：
    python3 reddit_trending.py
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any
import os

class RedditTrending:
    """Reddit 热门话题挖掘器"""
    
    # 目标 Subreddits
    SUBREDDITS = {
        'ai': [
            'artificial',
            'MachineLearning',
            'LocalLLaMA',
            'AI_Agents',
            'singularity'
        ],
        'database': [
            'database',
            'PostgreSQL',
            'MongoDB',
            'redis',
            'sql'
        ],
        'tech': [
            'technology',
            'programming',
            'webdev',
            'devops'
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
    
    def fetch_subreddit(self, subreddit: str, sort: str = 'hot') -> List[Dict[str, Any]]:
        """
        抓取 Subreddit 热门帖子（使用旧版 Reddit 界面，无需认证）
        
        Args:
            subreddit: Subreddit 名称
            sort: 排序方式 (hot/new/top)
            
        Returns:
            帖子列表
        """
        # 使用旧版 Reddit 界面（不需要 API 认证）
        url = f'https://old.reddit.com/r/{subreddit}/{sort}.json'
        params = {'limit': self.limit}
        
        try:
            resp = self.session.get(url, params=params, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
            
            posts = []
            if 'data' in data and 'children' in data['data']:
                for child in data['data']['children']:
                    post = child['data']
                    posts.append({
                        'subreddit': subreddit,
                        'title': post.get('title', ''),
                        'url': f"https://reddit.com{post.get('permalink', '')}",
                        'score': post.get('score', 0),
                        'num_comments': post.get('num_comments', 0),
                        'created_utc': post.get('created_utc', 0),
                        'author': post.get('author', '[deleted]'),
                        'selftext': post.get('selftext', '')[:500],  # 截取前 500 字
                        'upvote_ratio': post.get('upvote_ratio', 0)
                    })
            
            return posts
            
        except Exception as e:
            print(f"❌ 抓取 r/{subreddit} 失败：{e}")
            return []
    
    def fetch_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """抓取所有目标 Subreddits"""
        results = {}
        
        for category, subreddits in self.SUBREDDITS.items():
            print(f"\n📂 抓取 {category} 类别...")
            results[category] = []
            
            for subreddit in subreddits:
                print(f"  └─ r/{subreddit}")
                posts = self.fetch_subreddit(subreddit)
                results[category].extend(posts)
                
                # 按分数排序并保留 top
                results[category] = sorted(
                    results[category],
                    key=lambda x: x['score'],
                    reverse=True
                )[:self.limit * 2]
        
        return results
    
    def generate_report(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成 Markdown 报告"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""# 🔥 Reddit 热门话题 | {now}

**数据来源**: Reddit API (无需认证)  
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
                report += f"- **分数**: ⬆️ {post['score']:,}\n"
                report += f"- **评论**: 💬 {post['num_comments']}\n"
                report += f"- **好评率**: {post['upvote_ratio']*100:.0f}%\n"
                report += f"- **链接**: [{post['url']}]({post['url']})\n\n"
        
        # 数据库类别
        if results.get('database'):
            report += "## 🗄️ 数据库热门话题\n\n"
            for i, post in enumerate(results['database'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post['score']:,}\n"
                report += f"- **评论**: 💬 {post['num_comments']}\n"
                report += f"- **链接**: [{post['url']}]({post['url']})\n\n"
        
        # 技术类别
        if results.get('tech'):
            report += "## 💻 技术热门话题\n\n"
            for i, post in enumerate(results['tech'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post['score']:,}\n"
                report += f"- **评论**: 💬 {post['num_comments']}\n"
                report += f"- **链接**: [{post['url']}]({post['url']})\n\n"
        
        report += "---\n\n"
        report += f"*报告生成时间：{now} (Asia/Shanghai)*\n"
        
        return report
    
    def save_report(self, report: str, output_dir: str = None):
        """保存报告到文件"""
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'daily-investor',
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
    print("  Reddit 热门话题挖掘工具")
    print("=" * 60)
    
    # 创建挖掘器
    miner = RedditTrending(limit=15)
    
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
    
    top_posts = sorted(all_posts, key=lambda x: x['score'], reverse=True)[:5]
    
    for i, post in enumerate(top_posts, 1):
        print(f"\n{i}. {post['title'][:60]}...")
        print(f"   r/{post['subreddit']} | ⬆️ {post['score']:,} | 💬 {post['num_comments']}")
        print(f"   {post['url']}")
    
    print("\n" + "=" * 60)
    print("  完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
