# 🐦 X 首页 Top 30 集成指南

## 📋 功能概述

每日自动生成 @kejunz 账号的 X 首页热度分析，并将 Top 30 推文集成到 RSS 日报中。

**数据来源**:
- 🔍 **为你推荐** (For You): 200 条
- 👥 **正在关注** (Following): 200 条
- 🤖 **AI 列表**: 200 条

**输出内容**:
- 🏆 综合热度 TOP 10 表格
- 📌 分类精选（每类 3 条亮点）
- 🔥 热度分数（点赞 + 转推×1.5 + 回复×2）

---

## 🔧 配置步骤

### 第 1 步：获取 X Cookie

详见 [`COOKIE_GUIDE.md`](./COOKIE_GUIDE.md)

**快速步骤**:
1. 浏览器登录 https://twitter.com (使用 @kejunz)
2. F12 → Application → Cookies → twitter.com
3. 复制 `auth_token` 和 `ct0` 值

### 第 2 步：更新配置文件

编辑 `.env.cookie` 文件：

```bash
# X (Twitter) Cookie 配置
# 更新于 YYYY-MM-DD

# kejunz 账号 Cookie
X_AUTH_TOKEN=你的 auth_token 值
X_CT0=你的 ct0 值（长字符串）
X_TWID=u=16020505
```

### 第 3步：测试配置

```bash
cd daily-investor/scripts
python3 x_home_analysis.py
```

**成功标志**:
```
✅ 获取 200 条推文
🔥 分析热度，提取 Top 30...
✅ 报告已保存
```

**失败处理**:
```
⚠️ API 失败：401 Unauthorized
ℹ️ 切换到演示模式
```
→ Cookie 已过期，请重新获取

---

## 📊 生成日报

### 手动生成

```bash
cd daily-investor/scripts
python3 x_daily_report.py
```

生成的报告会包含：
- AI 科技 & 财经日报全文
- **新增**: X 首页热度 Top 30 章节

### 自动生成（Cron）

如果已配置定时任务，每日会自动运行并推送。

---

## 📁 文件结构

```
daily-investor/
├── .env.cookie                      # Cookie 配置文件（需更新）
├── COOKIE_GUIDE.md                  # Cookie 获取指南
├── X_TOP30_INTEGRATION.md          # 本文件
├── scripts/
│   ├── x_home_analysis.py          # X 首页分析器
│   ├── x_daily_report.py           # RSS 日报生成器（已集成）
│   └── ...
└── reports/
    └── x_home_analysis.md          # 独立分析报告
```

---

## 🔍 输出示例

### 综合热度 TOP 10

| 排名 | 作者 | 内容摘要 | 👍 | 🔄 | 💬 | 热度 |
|------|------|----------|----|----|----|------|
| 1 | @sama | GPT-5 训练进展超预期... | 9838 | 1951 | 203 | 13170 |
| 2 | @karpathy | Agent 工作流新框架... | 9732 | 1728 | 262 | 12848 |
| ... | ... | ... | ... | ... | ... | ... |

### 分类精选

**🔍 为你推荐亮点:**
- @elonmusk: SpaceX 最新发射计划公布... (🔥12402)
- @pmarca: AI 投资趋势分析... (🔥11823)

**👥 正在关注亮点:**
- @ylecun: 自监督学习新突破... (🔥12662)

**🤖 AI 列表亮点:**
- @gdb: Claude 3.5 使用技巧... (🔥11500)

---

## ⚠️ 常见问题

### Q1: 401 Unauthorized
**A**: Cookie 过期，按 `COOKIE_GUIDE.md` 重新获取

### Q2: 获取数量为 0
**A**: 
- 检查网络连接
- 等待 15 分钟（API 限流）
- 验证账号状态正常

### Q3: 只有演示数据
**A**: Cookie 未正确配置，检查 `.env.cookie` 文件格式

### Q4: 日报中没有 Top 30
**A**: 
- 确认 `x_daily_report.py` 已更新
- 检查是否有 `self.x_top30` 数据
- 查看控制台日志

---

## 📅 维护建议

### 每周检查
- [ ] 验证 Cookie 是否仍然有效
- [ ] 检查 Top 30 数据质量

### 每月更新
- [ ] 主动更新 Cookie（即使未过期）
- [ ] 审查热度算法是否需要调整

### 季度优化
- [ ] 分析哪些类型的推文更受欢迎
- [ ] 调整分类策略（如增加新的列表）

---

## 🔐 安全提醒

- ⚠️ **不要分享** Cookie 给他人
- ⚠️ **不要提交**到公开 Git 仓库（已加入 .gitignore）
- ⚠️ 定期更换密码，尤其在怀疑泄露时

---

## 📞 技术支持

遇到问题？检查以下文件：
1. `COOKIE_GUIDE.md` - Cookie 获取详细步骤
2. `memory/2026-02-23.md` - 开发和调试记录
3. GitHub Issues - 已知问题和解决方案

---

*最后更新：2026-02-23*
*版本：v1.0*
