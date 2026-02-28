# Reddit 热门话题挖掘工具

## 📦 工具说明

使用 Reddit RSS 源抓取热门话题，无需 API 凭证。

**覆盖领域**：
- 🤖 AI：r/artificial, r/MachineLearning, r/LocalLLaMA, r/singularity, r/ChatGPT, r/ClaudeAI, r/OpenAI
- 🗄️ 数据库：r/database, r/PostgreSQL, r/MongoDB, r/redis, r/sql, r/ClickHouse
- 💻 技术：r/technology, r/programming, r/webdev, r/devops, r/coding

## 🚀 使用方法

### 安装依赖

```bash
pip install feedparser --break-system-packages
```

### 运行脚本

```bash
cd /home/openclawuser/.openclaw/workspace/daily-investor/scripts
python3 reddit_trending_rss.py
```

### 输出位置

报告保存在：`~/daily-investor/reports/reddit/YYYY-MM-DD-reddit-trending.md`

## 📅 Cron 任务配置

添加定时任务（每天上午 9 点执行）：

```json
{
  "name": "Reddit 热门话题挖掘",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "cd /home/openclawuser/.openclaw/workspace/daily-investor/scripts && python3 reddit_trending_rss.py && cd /home/openclawuser/.openclaw/workspace/daily-investor && git add reports/reddit/ && git commit -m 'Add: Reddit 热门话题 $(date +%Y-%m-%d)' && git push"
  },
  "delivery": {
    "mode": "none"
  },
  "sessionTarget": "isolated"
}
```

## 📊 数据用途

1. **内容灵感**：发现 AI/数据库领域热门讨论
2. **趋势分析**：追踪技术话题演变
3. **社区洞察**：了解开发者关注点
4. **整合到日报**：作为每日技术新闻的数据源之一

## 🔧 故障排查

### RSS 源无法访问

```bash
# 测试 RSS 源
curl -I https://www.reddit.com/r/artificial/.rss
```

### 分数显示为 0

RSS 源解析可能失败，检查 `summary` 字段格式是否变化。

### 需要更多 Subreddits

编辑 `reddit_trending_rss.py` 中的 `SUBREDDITS` 字典添加新的目标。

## 📝 示例输出

```markdown
# 🔥 Reddit 热门话题 | 2026-02-28

## 🤖 AI 热门话题

### 1. Anthropic says it will challenge Pentagon's supply chain risk designation

- **Subreddit**: r/artificial
- **分数**: ⬆️ 1,234
- **评论**: 💬 156
- **链接**: [🔗 reddit.com/...](...)
```
