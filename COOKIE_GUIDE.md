# 🐦 X (Twitter) Cookie 获取指南

## ⚠️ 重要提示 (2026-02-23 更新)

由于 X (Twitter) 频繁更改 API 政策和认证机制，直接使用 Cookie 访问 API 可能不稳定。

**当前状态**:
- ❌ GraphQL API 需要额外的浏览器验证步骤
- ⚠️ Cookie 可能在几小时内失效
- ✅ **演示模式**仍然可用（生成模拟数据）

**推荐方案**:
1. **使用演示模式** - 日常测试足够
2. **等待官方 API** - 申请 X API 访问权限
3. **使用浏览器自动化** - Playwright/Selenium 模拟真实浏览

---

## 📋 获取步骤（Chrome/Edge 浏览器）

### 第 1 步：登录 X
1. 打开浏览器（建议使用 Chrome 或 Edge）
2. 访问 https://twitter.com 或 https://x.com
3. 使用 **@kejunz** 账号登录

### 第 2 步：打开开发者工具
1. 按 `F12` 或右键 → "检查" (Inspect)
2. 切换到 **Application**（应用程序）标签
3. 左侧展开 **Cookies** → 选择 `https://twitter.com`

### 第 3 步：复制 Cookie 值

找到以下三个关键字段并复制它们的值：

| 字段名 | 说明 | 示例格式 |
|--------|------|----------|
| `auth_token` | 认证 Token | `70f981fed062e6ebb64eace4ddebadca...` |
| `ct0` | CSRF Token | `543e3c8d128c61362e9d8cef3a5ecdc9...` (长字符串) |
| `twid` | Twitter ID | `u=16020505` |

**⚠️ 注意：**
- `ct0` 是一个很长的字符串（约 100+ 字符），确保完整复制
- 不要复制引号或多余空格
- 如果找不到某个字段，刷新页面后再试

### 第 4 步：更新配置文件

编辑 `daily-investor/.env.cookie` 文件：

```bash
# X (Twitter) Cookie 配置
# 更新于 YYYY-MM-DD

# kejunz 账号 Cookie
X_AUTH_TOKEN=你的 auth_token 值
X_CT0=你的 ct0 值
X_TWID=u=16020505
```

### 第 5 步：测试

运行测试脚本验证 Cookie 是否有效：

```bash
cd daily-investor/scripts
python3 x_home_analysis.py
```

如果看到 "✅ 获取 200 条推文" 说明成功！

---

## 🔍 故障排查

### 问题 1: 401 Unauthorized
- **原因**: Cookie 已过期
- **解决**: 重新按上述步骤获取最新 Cookie

### 问题 2: 找不到 ct0
- **原因**: 页面未完全加载
- **解决**: 刷新页面，等待几秒后再查看

### 问题 3: 获取推文数量为 0
- **原因**: API 限流或账号异常
- **解决**: 等待 15 分钟再试，或检查账号状态

---

## 📅 建议

- **每月更新一次** Cookie（设置日历提醒）
- 在 Cookie 失效前主动更新，避免中断服务
- 可将获取步骤保存为书签或笔记

---

## 🔐 安全提示

- ⚠️ **不要分享** Cookie 给他人
- ⚠️ **不要提交**到公开 Git 仓库（已加入 .gitignore）
- ⚠️ 如怀疑泄露，立即登出所有设备并重置密码

---

*最后更新：2026-02-23*
