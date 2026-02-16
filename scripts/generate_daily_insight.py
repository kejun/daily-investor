#!/usr/bin/env python3
"""
自动更新投资洞察报告 - 集成 RSS KOL 观点
每日运行，自动抓取并生成报告
"""

import os
import sys
from datetime import datetime, timedelta
from fetch_rss_kol import fetch_kol_rss, format_for_insights

def generate_insight_report(date_str=None):
    """生成每日投资洞察报告"""
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    year = date_str[:4]
    month = date_str[5:7]
    
    # 确保目录存在
    os.makedirs(f"../{year}/{month}", exist_ok=True)
    
    # 获取 KOL 观点
    print(f"🔄 正在获取 {date_str} 的 KOL 观点...")
    results = fetch_kol_rss(max_items=2)
    insights = format_for_insights(results)
    
    # 生成投资者观点表格
    investor_views = []
    for item in insights[:5]:  # 取前5条
        investor_views.append(f"| **{item['investor']}** | \"{item['view']}\" | {item['market']} |")
    
    # 生成报告
    report = f"""# 📈 每日投资洞察 | {date_str}

**市场概览**: [待更新 - 上证指数/恒生指数/标普500当日表现]

---

## 🔥 核心观点

**美股**：[待更新]

**A股**：[待更新]

**港股**：[待更新]

---

## 🎙️ 投资者观点

| 投资者 | 核心观点 | 影响市场 |
|--------|---------|---------|
{chr(10).join(investor_views)}

*注：观点来自 X (Twitter) 公开信息，通过 RSS 自动获取，不构成投资建议*

---

## 🇺🇸 美股市场

### 大盘表现
*待更新*

---

## 🇨🇳 A股市场

### 大盘表现
*待更新*

---

## 🇭🇰 港股市场

### 大盘表现
*待更新*

---

## 📅 本周前瞻

### 重点事件
*待更新*

---

## 💡 交易策略建议

*待更新*

---

**数据来源**: X (Twitter) KOL RSS, Yahoo Finance, 东方财富
**发布时间**: {date_str} 09:30 (Asia/Shanghai)
**免责声明**: 本报告仅供学习交流，不构成投资建议

---

*本报告部分内容由 AI 自动生成，投资者观点通过 RSS 自动抓取*
"""
    
    # 保存报告
    output_path = f"../{year}/{month}/{date_str}.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成: {output_path}")
    print(f"📊 包含 {len(insights)} 条投资者观点")
    
    return output_path

if __name__ == "__main__":
    # 支持命令行参数指定日期，默认今天
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generate_insight_report(date_arg)
