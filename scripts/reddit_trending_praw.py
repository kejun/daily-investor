#!/usr/bin/env python3
"""
Reddit 热门话题挖掘工具（使用 PRAW 库）

安装依赖：
    pip install praw

配置：
    在 .env 文件中设置 Reddit API 凭证（可选，无凭证也可匿名访问）
    REDDIT_CLIENT_ID=your_client_id
    REDDIT_CLIENT_SECRET=your_client_secret
    REDDIT_USER_AGENT=your_user_agent

用法：
    python3 reddit_trending_praw.py
"""

import praw
import json
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class RedditTrendingPRAW:
    """Reddit 热门话题挖掘器（基于 PRAW）"""
    
    # 目标 Subreddits
    SUBREDDITS = {
        'ai': [
            'artificial',
            'MachineLearning',
            'LocalLLaMA',
            'AI_Agents',
            'singularity',
            'ChatGPT',
            'ClaudeAI'
        ],
        'database': [
            'database',
            'PostgreSQL',
            'MongoDB',
            'redis',
            'sql',
            'ClickHouse',
            'duckdb'
        ],
        'tech': [
            'technology',
            'programming',
            'webdev',
            'devops',
            'coding',
            'learnprogramming'
        ]
    }
    
    def __init__(self, limit: int = 15):
        """
        初始化
        
        Args:
            limit: 每个 Subreddit 抓取帖子数量
        """
        self.limit = limit
        
        # 尝试使用 API 凭证，失败则匿名访问
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID', 'anonymous'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET', 'anonymous'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditTrendingBot/1.0 by OpenClaw'),
                check_for_async=False
            )
            print("✅ 使用 Reddit API 连接")
        except Exception as e:
            print(f"⚠️  API 连接失败，使用匿名模式：{e}")
            self.reddit = None
    
    def fetch_subreddit(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        抓取 Subreddit 热门帖子
        
        Args:
            subreddit_name: Subreddit 名称
            
        Returns:
            帖子列表
        """
        posts = []
        
        try:
            if self.reddit:
                subreddit = self.reddit.subreddit(subreddit_name)
                hot_posts = subreddit.hot(limit=self.limit)
            else:
                # 匿名模式：使用网页搜索替代
                print(f"  ⚠️  匿名模式无法直接抓取，使用替代数据源")
                return self._fallback_search(subreddit_name)
            
            for post in hot_posts:
                posts.append({
                    'subreddit': subreddit_name,
                    'title': post.title[:200] if post.title else '',
                    'url': f"https://reddit.com{post.permalink}",
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'created_utc': post.created_utc,
                    'author': str(post.author) if post.author else '[deleted]',
                    'selftext': post.selftext[:500] if post.selftext else '',
                    'upvote_ratio': post.upvote_ratio
                })
            
            return posts
            
        except Exception as e:
            print(f"  ❌ 抓取 r/{subreddit_name} 失败：{e}")
            return self._fallback_search(subreddit_name)
    
    def _fallback_search(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        备用方案：使用 web_search 搜索 Reddit 热门话题
        
        Args:
            subreddit_name: Subreddit 名称
            
        Returns:
            模拟帖子列表
        """
        try:
            from web_search import web_search
            query = f"site:reddit.com/r/{subreddit_name} hot trending"
            results = web_search(query, count=5)
            
            posts = []
            for result in results.get('results', []):
                posts.append({
                    'subreddit': subreddit_name,
                    'title': result.get('title', '')[:200],
                    'url': result.get('url', ''),
                    'score': 0,
                    'num_comments': 0,
                    'created_utc': datetime.now().timestamp(),
                    'author': 'unknown',
                    'selftext': result.get('description', '')[:500],
                    'upvote_ratio': 0
                })
            
            return posts
        except:
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
                    key=lambda x: x.get('score', 0),
                    reverse=True
                )[:self.limit * 2]
        
        return results
    
    def generate_report(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成 Markdown 报告"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        report = f"""# 🔥 Reddit 热门话题 | {now}

**数据来源**: Reddit PRAW API  
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
                if post.get('upvote_ratio', 0) > 0:
                    report += f"- **好评率**: {post['upvote_ratio']*100:.0f}%\n"
                report += f"- **链接**: [{post['url']}]({post['url']})\n\n"
        
        # 数据库类别
        if results.get('database'):
            report += "## 🗄️ 数据库热门话题\n\n"
            for i, post in enumerate(results['database'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post.get('score', 0):,}\n"
                report += f"- **评论**: 💬 {post.get('num_comments', 0)}\n"
                report += f"- **链接**: [{post['url']}]({post['url']})\n\n"
        
        # 技术类别
        if results.get('tech'):
            report += "## 💻 技术热门话题\n\n"
            for i, post in enumerate(results['tech'][:10], 1):
                report += f"### {i}. {post['title']}\n\n"
                report += f"- **Subreddit**: r/{post['subreddit']}\n"
                report += f"- **分数**: ⬆️ {post.get('score', 0):,}\n"
                report += f"- **评论**: 💬 {post.get('num_comments', 0)}\n"
                report += f"- **链接**: [{post['url']}]({post['url']})\n\n"
        
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
    print("  Reddit 热门话题挖掘工具 (PRAW)")
    print("=" * 60)
    
    # 创建挖掘器
    miner = RedditTrendingPRAW(limit=15)
    
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
        print(f"   {post.get('url', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("  完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
