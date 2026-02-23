#!/usr/bin/env python3
"""
自动更新投资洞察报告 - 集成 Finnhub 实时市场数据 + RSS KOL 观点
每日运行，自动抓取并生成报告
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from fetch_rss_kol import fetch_kol_rss, format_for_insights
from finnhub_client import FinnhubClient, get_market_overview, get_stocks_performance

def generate_insight_report(date_str=None):
    """生成每日投资洞察报告"""
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    year = date_str[:4]
    month = date_str[5:7]
    
    # 确保目录存在
    os.makedirs(f"../{year}/{month}", exist_ok=True)
    
    # 初始化 Finnhub 客户端
    try:
        finnhub = FinnhubClient()
        print(f"✅ Finnhub API 已连接\n")
    except Exception as e:
        print(f"⚠️ Finnhub 初始化失败：{e}")
        finnhub = None
    
    # 获取市场数据
    market_data = {}
    if finnhub:
        try:
            # 美股主要指数
            overview = get_market_overview(finnhub)
            market_data['us_indices'] = overview
            
            # 热门个股
            stocks = ['NVDA', 'AAPL', 'TSLA', 'META', 'MSFT', 'GOOGL', 'AMD']
            performance = get_stocks_performance(finnhub, stocks)
            market_data['us_stocks'] = performance
        except Exception as e:
            print(f"⚠️ 市场数据获取失败：{e}")
            market_data = {}
    
    # 获取 KOL 观点
    print(f"\n🔄 正在获取 {date_str} 的 KOL 观点...")
    results = fetch_kol_rss(max_items=2)
    insights = format_for_insights(results)
    
    # 生成投资者观点表格
    investor_views = []
    for item in insights[:5]:  # 取前 5 条
        investor_views.append(f"| **{item['investor']}** | \"{item['view']}\" | {item['market']} |")
    
    # 生成市场概览文本
    market_summary_lines = []
    if market_data.get('us_indices'):
        for name, data in market_data['us_indices'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                market_summary_lines.append(f"{name} {data['current']:.2f} ({sign}{data['change_percent']:.2f}%)")
    
    # 领涨领跌
    leaders = []
    laggards = []
    if market_data.get('us_stocks'):
        for symbol, data in market_data['us_stocks'].items():
            if data and data['change_percent'] != 0:
                if data['change_percent'] > 0:
                    leaders.append((symbol, data['change_percent']))
                else:
                    laggards.append((symbol, data['change_percent']))
        
        leaders.sort(key=lambda x: x[1], reverse=True)
        laggards.sort(key=lambda x: x[1])
    
    # 生成报告
    report = f"""# 📈 每日投资洞察 | {date_str}

**市场概览**: {' | '.join(market_summary_lines) if market_summary_lines else '数据暂不可用'}

---

## 🔥 核心观点

**美股**: {' | '.join([f"{s} {p:+.2f}%" for s, p in leaders[:3]]) if leaders else '待更新'}

**A 股**: [需接入国内数据源]

**港股**: [需接入国内数据源]

---

## 🎙️ 投资者观点

| 投资者 | 核心观点 | 影响市场 |
|--------|---------|---------|
{chr(10).join(investor_views)}

*注：观点来自 X (Twitter) 公开信息，通过 RSS 自动获取，不构成投资建议*

---

## 🇺🇸 美股市场

### 大盘表现
"""
    
    if market_data.get('us_indices'):
        report += "| 指数 | 当前价 | 涨跌 |\n|------|--------|------|\n"
        for name, data in market_data['us_indices'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                report += f"| {name} | {data['current']:.2f} | {sign}{data['change_percent']:.2f}% |\n"
    
    report += "\n### 个股表现\n"
    
    if market_data.get('us_stocks'):
        report += "| 股票 | 当前价 | 涨跌额 | 涨跌幅 |\n|------|--------|--------|--------|\n"
        for symbol, data in market_data['us_stocks'].items():
            if data:
                sign = '+' if data['change'] > 0 else ''
                sign_pct = '+' if data['change_percent'] > 0 else ''
                report += f"| {symbol} | ${data['current']:.2f} | {sign}{data['change']:.2f} | {sign_pct}{data['change_percent']:.2f}% |\n"
    
    report += f"""
---

## 🇨🇳 A 股市场

### 大盘表现
*需接入国内数据源（东方财富/新浪财经 API）*

---

## 🇭🇰 港股市场

### 大盘表现
*需接入国内数据源*

---

## 📅 本周前瞻

### 重点事件
*待更新*

---

## 💡 交易策略建议

"""
    
    if leaders:
        top_leader = leaders[0]
        report += f"**强势板块**: {top_leader[0]} (+{top_leader[1]:.2f}%) 领涨，关注相关产业链机会\n\n"
    
    if laggards:
        top_laggard = laggards[0]
        report += f"**风险提示**: {top_laggard[0]} (-{abs(top_laggard[1]):.2f}%) 回调，注意仓位控制\n\n"
    
    report += f"""---

**数据来源**: X (Twitter) KOL RSS, Finnhub (实时美股), [待接入：A 股/港股数据源]
**发布时间**: {date_str} 09:30 (Asia/Shanghai)
**免责声明**: 本报告仅供学习交流，不构成投资建议

---

*本报告部分内容由 AI 自动生成，投资者观点通过 RSS 自动抓取，市场数据来自 Finnhub 实时 API*
"""
    
    # 保存报告
    output_path = f"../{year}/{month}/{date_str}.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已生成：{output_path}")
    print(f"📊 包含 {len(insights)} 条投资者观点")
    if market_data.get('us_stocks'):
        print(f"📈 包含 {len(market_data['us_stocks'])} 只美股实时数据")
    
    return output_path

if __name__ == "__main__":
    # 支持命令行参数指定日期，默认今天
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generate_insight_report(date_arg)
