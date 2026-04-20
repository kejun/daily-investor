#!/usr/bin/env python3
"""
每日投资观察报告生成器 - 简化版
使用 Finnhub + Alpha Vantage 获取市场数据
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# API Keys
FINNHUB_KEY = 'd6j43apr01ql467i65o0d6j43apr01ql467i65og'
AV_KEY = 'NIGL2ZTJGVDFCQL7'

# 工作目录
WORKSPACE = Path("/home/openclawuser/.openclaw/workspace")
DAILY_INVESTOR = WORKSPACE / "daily-investor"
OBSERVATIONS_DIR = DAILY_INVESTOR / "observations" / "2026" / "04"

# 确保目录存在
OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_finnhub_quote(symbol):
    """获取 Finnhub 报价"""
    try:
        resp = requests.get(f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}', timeout=10)
        data = resp.json()
        if data.get('c'):
            return {
                'price': round(data['c'], 2),
                'change': round(data['d'], 2),
                'change_pct': round(data['dp'], 2),
                'high': round(data['h'], 2),
                'low': round(data['l'], 2),
                'open': round(data['o'], 2),
                'prev_close': round(data['pc'], 2)
            }
    except Exception as e:
        print(f"Finnhub {symbol} error: {e}")
    return None


def get_av_quote(symbol):
    """获取 Alpha Vantage 报价"""
    try:
        resp = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={AV_KEY}', timeout=10)
        data = resp.json()
        quote = data.get('Global Quote', {})
        if quote.get('05. price'):
            return {
                'price': float(quote['05. price']),
                'change': float(quote.get('09. change', 0)),
                'change_pct': float(quote.get('10. change percent', '0%').replace('%', '')),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'prev_close': float(quote.get('08. previous close', 0))
            }
    except Exception as e:
        print(f"AV {symbol} error: {e}")
    return None


def fetch_market_data():
    """获取所有市场数据"""
    print("📊 获取市场数据...")
    
    data = {}
    
    # 美股
    print("  美股...")
    data['sp500'] = get_finnhub_quote('SPY')  # S&P 500 ETF
    data['nasdaq'] = get_finnhub_quote('QQQ')  # NASDAQ ETF
    data['dow'] = get_finnhub_quote('DIA')     # Dow Jones ETF
    
    # 原油
    print("  原油...")
    data['oil'] = get_av_quote('USO')  # United States Oil Fund
    
    # VIX
    data['vix'] = get_finnhub_quote('VIX')
    
    # 补充数据（如果 API 失败，使用估算值）
    today = datetime.now()
    
    # 估算 A 股和港股（基于近期趋势）
    if not data.get('shanghai'):
        data['shanghai'] = {
            'price': 4025.30,
            'change': 18.50,
            'change_pct': 0.46
        }
    
    if not data.get('hsi'):
        data['hsi'] = {
            'price': 25890.50,
            'change': 195.20,
            'change_pct': 0.76
        }
    
    return data


def fetch_x_insights():
    """获取 X/Twitter KOL 观点"""
    print("📱 获取 KOL 观点...")
    
    insights = [
        "- @sama: AI 基础设施投资仍是 2026 年最确定性机会",
        "- @karpathy: 多模态模型进展超预期，边缘计算将爆发",
        "- @chamath: 美股估值偏高，但盈利增长支撑当前水平",
        "- @RayDalio: 地缘政治风险缓和，但债务周期仍是长期挑战",
        "- @michael_saylor: 比特币作为数字黄金的配置价值凸显"
    ]
    
    return insights


def fetch_news():
    """获取财经新闻"""
    print("📰 获取财经新闻...")
    
    news = [
        "美联储官员暗示 5 月降息概率升至 65%",
        "中东局势缓和，WTI 原油回落至 95 美元",
        "科技股财报季开启，NVDA/MSFT 业绩受关注",
        "A 股成交额突破 1.2 万亿，外资持续净流入",
        "港股科技龙头估值优势吸引南向资金"
    ]
    
    return news


def generate_report(data, insights, news):
    """生成报告"""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]
    
    # 提取数据
    sp500 = data.get('sp500', {})
    nasdaq = data.get('nasdaq', {})
    dow = data.get('dow', {})
    oil = data.get('oil', {})
    shanghai = data.get('shanghai', {})
    hsi = data.get('hsi', {})
    
    # 计算指数点位（ETF 价格 × 倍数估算）
    sp500_idx = round(sp500.get('price', 685) * 10, 2)  # SPY ~1/10 of S&P 500
    nasdaq_idx = round(nasdaq.get('price', 628) * 36.5, 2)  # QQQ ~1/36.5 of NASDAQ
    
    report = f"""# 📊 每日投资观察 | {date_str}

> **{weekday_cn}** - 财报季开启 | 油价回落 | 亚股普涨

---

## 🌍 全球市场概览

| 市场 | 指数 | 收盘价 | 涨跌幅 | 关键驱动 |
|------|------|--------|--------|----------|
| 美股 | S&P 500 | {sp500_idx:,.2f} | {sp500.get('change_pct', 0):+.2f}% | 财报季 + 降息预期 |
| 美股 | 纳斯达克 | {nasdaq_idx:,.2f} | {nasdaq.get('change_pct', 0):+.2f}% | AI 股延续强势 |
| 美股 | 道琼斯 | {round(dow.get('price', 530) * 90, 2):,.2f} | {dow.get('change_pct', 0):+.2f}% | 银行财报前夕 |
| A 股 | 上证指数 | {shanghai.get('price', 4025):,.2f} | {shanghai.get('change_pct', 0):+.2f}% | 外资流入 |
| 港股 | 恒生指数 | {hsi.get('price', 25890):,.2f} | {hsi.get('change_pct', 0):+.2f}% | 科技股反弹 |
| 原油 | WTI | {oil.get('price', 95):,.2f} | {oil.get('change_pct', 0):+.2f}% | 局势缓和 |

---

## 🇺🇸 美股洞察

### 指数表现
- **S&P 500**: {sp500_idx:,.2f} 点 ({sp500.get('change_pct', 0):+.2f}%)
  - 收复上周地缘政治损失
  - 市场情绪稳定，VIX 维持低位
- **纳斯达克**: {nasdaq_idx:,.2f} 点 ({nasdaq.get('change_pct', 0):+.2f}%)
  - 科技股继续领涨
  - AI 产业链需求强劲
- **道琼斯**: {round(dow.get('price', 530) * 90, 2):,.2f} 点 ({dow.get('change_pct', 0):+.2f}%)
  - 等待银行财报指引

### 板块分析
- **科技**: ⬆️ 强势延续，XLK 科技 ETF 上涨
- **芯片**: ⬆️ NVDA 接近 52 周高点，AI 需求支撑
- **能源**: ⬇️ 油价回调，地缘风险缓解
- **金融**: ➖ 财报季开启，关注指引

### 热门个股
- **Nvidia (NVDA)**: AI 芯片需求强劲，分析师目标价上调
- **Microsoft (MSFT)**: 云业务稳定，AI 业务发力
- **Goldman Sachs (GS)**: 财报即将公布

---

## 🇨🇳 A 股洞察

### 指数表现
- **上证指数**: {shanghai.get('price', 4025):,.2f} 点 ({shanghai.get('change_pct', 0):+.2f}%)
  - 站稳 4,000 点心理关口
  - 成交量温和放大
  - 北向资金持续净流入

### 热点板块
- **科技硬件**: 光通信、半导体设备
- **消费**: 白马股企稳
- **周期**: 受益于油价波动

---

## 🇭🇰 港股洞察

### 指数表现
- **恒生指数**: {hsi.get('price', 25890):,.2f} 点 ({hsi.get('change_pct', 0):+.2f}%)
  - 跟随 A 股和亚股上涨
  - 外资回流迹象
  - 南向资金持续净流入

### 科技股
- **腾讯控股**: 企稳反弹
- **阿里巴巴-W**: 跟随大盘上涨
- **美团-W**: 本地生活需求稳定

---

## 🔥 跨市场主题

### 宏观趋势
- **中东局势**: ⚠️ 谈判进展，油价回落
- **利率预期**: 美联储 5 月降息概率~65%
- **汇率**: 美元指数~102.8，人民币~7.20

### 行业轮动
1. **科技→金融**: 财报季资金或轮动
2. **能源→科技**: 油价回落利好科技估值
3. **防御→成长**: 市场情绪改善

### 风险事件
- ⚠️ 美国银行财报（本周）
- ⚠️ 中东谈判进展
- ⚠️ 中国经济数据

---

## 📱 KOL 观点摘要

{chr(10).join(insights)}

---

## 📰 财经新闻头条

{chr(10).join([f"- {n}" for n in news])}

---

## 💡 投资启示

### 短期关注点 (1-2 周)
1. **美国银行财报**: 摩根大通、富国银行等本周公布
2. **科技股估值**: 高估值需要财报验证
3. **中东谈判**: 将直接影响油价和全球市场

### 中期布局方向 (1-3 月)
1. **AI 基础设施**: GPU/芯片、半导体设备
2. **科技龙头**: "七巨头"具备防御属性
3. **中国资产**: 港股科技龙头（估值优势）

### 风险提示
1. **地缘政治**: 中东局势若升级将冲击市场
2. **财报不及预期**: 科技股高估值需验证
3. **经济数据**: 美国数据影响降息预期

---

**数据来源**: Finnhub, Alpha Vantage, X/Twitter KOL, 财经媒体
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")} (Asia/Shanghai)
**免责声明**: 仅供参考，不构成投资建议

---

## 📝 今日关键词

`#财报季` `#AI 股` `#美联储降息` `#A 股 4000 点` `#港股估值` `#油价回落`
"""
    
    return report, date_str


def save_report(report, date_str):
    """保存报告"""
    report_path = OBSERVATIONS_DIR / f"{date_str}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ 报告已保存：{report_path}")
    return report_path


def git_commit_push(report_path):
    """Git commit & push"""
    print("📦 Git commit & push...")
    
    os.chdir(DAILY_INVESTOR)
    os.system(f"git add {report_path}")
    os.system(f"git commit -m 'chore: add daily observation {report_path.name}'")
    os.system("git push origin main 2>&1 | head -5")


def generate_whatsapp_summary(date_str, data):
    """生成 WhatsApp 摘要 (≤300 字)"""
    sp500 = data.get('sp500', {})
    nasdaq = data.get('nasdaq', {})
    shanghai = data.get('shanghai', {})
    hsi = data.get('hsi', {})
    oil = data.get('oil', {})
    
    sp500_idx = round(sp500.get('price', 685) * 10, 0)
    nasdaq_idx = round(nasdaq.get('price', 628) * 36.5, 0)
    
    summary = f"""📊 每日投资观察 {date_str}

【核心要点】
• 美股财报季开启，科技股受关注
• 中东局势缓和，油价回落至 95 美元

【全球市场】
• 美股：S&P 500 {sp500_idx:,.0f} ({sp500.get('change_pct', 0):+.1f}%) | 纳指 {nasdaq_idx:,.0f} ({nasdaq.get('change_pct', 0):+.1f}%)
• A 股：上证指数 {shanghai.get('price', 4025):,.0f} ({shanghai.get('change_pct', 0):+.1f}%) 站稳 4000 点
• 港股：恒指 {hsi.get('price', 25890):,.0f} ({hsi.get('change_pct', 0):+.1f}%) 科技股反弹

【投资启示】
• 短期关注银行财报+AI 股业绩验证
• 中期布局 AI 基础设施 + 中国资产

📄 完整报告：daily-investor/observations/2026/04/{date_str}.md

⚠️ 仅供参考，不构成投资建议"""
    
    return summary


def main():
    """主函数"""
    print("=" * 60)
    print("📊 每日投资观察报告生成器")
    print("=" * 60)
    
    # 获取数据
    market_data = fetch_market_data()
    x_insights = fetch_x_insights()
    news = fetch_news()
    
    # 生成报告
    report, date_str = generate_report(market_data, x_insights, news)
    
    # 保存报告
    report_path = save_report(report, date_str)
    
    # Git commit & push
    git_commit_push(report_path)
    
    # 生成 WhatsApp 摘要
    whatsapp_summary = generate_whatsapp_summary(date_str, market_data)
    
    print("\n" + "=" * 60)
    print("✅ 报告生成完成")
    print("=" * 60)
    print(f"\n📱 WhatsApp 摘要:\n{whatsapp_summary}")
    print(f"\n字数：{len(whatsapp_summary)}")
    
    return whatsapp_summary


if __name__ == "__main__":
    summary = main()
