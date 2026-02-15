# Daily Investor

每日投资洞察：美股、A股、港股市场分析，生成可指导交易的洞察。

## 结构

```
daily-investor/
├── README.md
├── 2026/
│   ├── 02/
│   │   └── 2026-02-15.md
│   └── 03/
├── scripts/
│   └── daily-invest.js
├── templates/
│   └── investor-template.md
└── .git/
```

## 数据来源

- **美股**: Yahoo Finance, Alpha Vantage
- **A股**: East Money (东方财富), Sina Finance
- **港股**: Yahoo Finance HK, AAStocks

## 分析维度

1. **大盘趋势** — 指数走势、成交量、波动率
2. **板块轮动** — 领涨/领跌板块分析
3. **资金流向** — 北上资金、南下资金、主力资金
4. **个股信号** — 技术形态突破、异动监控
5. **政策面** — 重大政策、财报季、重要事件

## 推送时间

每日收盘后 16:00-18:00 (Asia/Shanghai)

## License

MIT
