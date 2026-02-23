#!/usr/bin/env python3
"""
自动更新投资洞察报告 - 集成 Finnhub + 东方财富市场数据 + RSS KOL 观点
每日运行，自动抓取并生成报告
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from fetch_rss_kol import fetch_kol_rss, format_for_insights
from finnhub_client import FinnhubClient, get_market_overview, get_stocks_performance
from cn_market_data import CNMarketClient, get_a_share_indices, get_a_share_stocks, get_hk_stocks

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
    
    # 初始化中国股市客户端
    try:
        cn_client = CNMarketClient()
        print(f"✅ 中国股市 API 已连接\n")
    except Exception as e:
        print(f"⚠️ 中国股市初始化失败：{e}")
        cn_client = None
    
    # 获取美股数据
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
            print(f"⚠️ 美股数据获取失败：{e}")
    
    # 获取 A 股和港股数据
    if cn_client:
        try:
            # A 股指数
            a_indices = get_a_share_indices(cn_client)
            market_data['a_indices'] = a_indices
            
            # A 股个股
            a_stocks = ['600519', '000858', '300750', '002594', '601318']
            a_performance = get_a_share_stocks(cn_client, a_stocks)
            market_data['a_stocks'] = a_performance
            
            # 港股
            hk_stocks = ['00700', '09988', '03690', '01810', '02318']
            hk_performance = get_hk_stocks(cn_client, hk_stocks)
            market_data['hk_stocks'] = hk_performance
        except Exception as e:
            print(f"⚠️ 中港股市数据获取失败：{e}")
    
    # 获取 KOL 观点
    print(f"\n🔄 正在获取 {date_str} 的 KOL 观点...")
    results = fetch_kol_rss(max_items=2)
    insights = format_for_insights(results)
    
    # 生成投资者观点表格
    investor_views = []
    for item in insights[:5]:  # 取前 5 条
        investor_views.append(f"| **{item['investor']}** | \"{item['view']}\" | {item['market']} |")
    
    # 生成市场概览文本（美股 + A 股）
    market_summary_lines = []
    if market_data.get('us_indices'):
        for name, data in market_data['us_indices'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                market_summary_lines.append(f"{name} {data['current']:.2f} ({sign}{data['change_percent']:.2f}%)")
    
    # A 股概览
    if market_data.get('a_indices'):
        for name, data in market_data['a_indices'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                market_summary_lines.append(f"{name} {data['current']:.2f} ({sign}{data['change_percent']:.2f}%)")
    
    # 美股领涨领跌
    us_leaders = []
    us_laggards = []
    if market_data.get('us_stocks'):
        for symbol, data in market_data['us_stocks'].items():
            if data and data['change_percent'] != 0:
                if data['change_percent'] > 0:
                    us_leaders.append((symbol, data['change_percent']))
                else:
                    us_laggards.append((symbol, data['change_percent']))
        us_leaders.sort(key=lambda x: x[1], reverse=True)
        us_laggards.sort(key=lambda x: x[1])
    
    # A 股领涨领跌
    a_leaders = []
    a_laggards = []
    if market_data.get('a_stocks'):
        for symbol, data in market_data['a_stocks'].items():
            if data and data['change_percent'] != 0:
                if data['change_percent'] > 0:
                    a_leaders.append((symbol, data['name'], data['change_percent']))
                else:
                    a_laggards.append((symbol, data['name'], data['change_percent']))
        a_leaders.sort(key=lambda x: x[2], reverse=True)
        a_laggards.sort(key=lambda x: x[2])
    
    # 港股领涨领跌
    hk_leaders = []
    hk_laggards = []
    if market_data.get('hk_stocks'):
        for symbol, data in market_data['hk_stocks'].items():
            if data and data['change_percent'] != 0:
                if data['change_percent'] > 0:
                    hk_leaders.append((symbol, data['name'], data['change_percent']))
                else:
                    hk_laggards.append((symbol, data['name'], data['change_percent']))
        hk_leaders.sort(key=lambda x: x[2], reverse=True)
        hk_laggards.sort(key=lambda x: x[2])
    
    # 生成报告
    report = f"""# 📈 每日投资洞察 | {date_str}

**市场概览**: {' | '.join(market_summary_lines[:4]) if market_summary_lines else '数据暂不可用'}

---

## 🔥 核心观点

**美股**: {' | '.join([f"{s} {p:+.2f}%" for s, p in us_leaders[:3]]) if us_leaders else '待更新'}

**A 股**: {' | '.join([f"{n} {p:+.2f}%" for s, n, p in a_leaders[:3]]) if a_leaders else '待更新'}

**港股**: {' | '.join([f"{n} {p:+.2f}%" for s, n, p in hk_leaders[:3]]) if hk_leaders else '待更新'}

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
"""
    
    if market_data.get('a_indices'):
        report += "| 指数 | 当前价 | 涨跌 |\n|------|--------|------|\n"
        for name, data in market_data['a_indices'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                report += f"| {name} | {data['current']:.2f} | {sign}{data['change_percent']:.2f}% |\n"
    
    report += "\n### 个股表现\n"
    
    if market_data.get('a_stocks'):
        report += "| 股票 | 名称 | 当前价 | 涨跌幅 |\n|------|------|--------|--------|\n"
        for symbol, data in market_data['a_stocks'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                report += f"| {symbol} | {data['name']} | {data['current']:.2f} | {sign}{data['change_percent']:.2f}% |\n"
    
    report += f"""
---

## 🇭🇰 港股市场

### 个股表现
"""
    
    if market_data.get('hk_stocks'):
        report += "| 代码 | 名称 | 当前价 | 涨跌幅 |\n|------|------|--------|--------|\n"
        for symbol, data in market_data['hk_stocks'].items():
            if data:
                sign = '+' if data['change_percent'] > 0 else ''
                report += f"| {symbol} | {data['name']} | {data['current']:.2f} | {sign}{data['change_percent']:.2f}% |\n"
    
    report += f"""
---

## 📅 本周前瞻

### 重点事件
*待更新*

---

## 💡 交易策略建议

"""
    
    # 美股建议
    if us_leaders:
        top = us_leaders[0]
        report += f"**美股强势**: {top[0]} (+{top[1]:.2f}%) 领涨\n\n"
    if us_laggards:
        top = us_laggards[0]
        report += f"**美股风险**: {top[0]} (-{abs(top[1]):.2f}%) 回调\n\n"
    
    # A 股建议
    if a_leaders:
        top = a_leaders[0]
        report += f"**A 股强势**: {top[1]} (+{top[2]:.2f}%) 领涨\n\n"
    if a_laggards:
        top = a_laggards[0]
        report += f"**A 股风险**: {top[1]} (-{abs(top[2]):.2f}%) 回调\n\n"
    
    # 港股建议
    if hk_leaders:
        top = hk_leaders[0]
        report += f"**港股强势**: {top[1]} (+{top[2]:.2f}%) 领涨\n\n"
    if hk_laggards:
        top = hk_laggards[0]
        report += f"**港股风险**: {top[1]} (-{abs(top[2]):.2f}%) 回调\n\n"
    
    report += f"""---

**数据来源**: X (Twitter) KOL RSS | Finnhub (美股) | 东方财富 (A 股/港股)
**发布时间**: {date_str} 17:30 (Asia/Shanghai)
**免责声明**: 本报告仅供学习交流，不构成投资建议

---

*本报告由 OpenClaw Agent 自动生成，市场数据来自实时/最近交易日*
"""
    
    # 保存报告
    output_path = f"../{year}/{month}/{date_str}.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已生成：{output_path}")
    print(f"📊 包含 {len(insights)} 条投资者观点")
    if market_data.get('us_stocks'):
        print(f"📈 包含 {len(market_data['us_stocks'])} 只美股数据")
    if market_data.get('a_stocks'):
        print(f"📈 包含 {len(market_data['a_stocks'])} 只 A 股数据")
    if market_data.get('hk_stocks'):
        print(f"📈 包含 {len(market_data['hk_stocks'])} 只港股数据")
    
    return output_path

if __name__ == "__main__":
    # 支持命令行参数指定日期，默认今天
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generate_insight_report(date_arg)
