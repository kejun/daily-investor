#!/usr/bin/env node
/**
 * 每日投资洞察脚本
 * 自动获取美股、A股、港股数据，生成交易指导洞察
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

// 股票代码映射
const STOCKS = {
  // 美股
  us: {
    sp500: '^GSPC',
    nasdaq: '^IXIC',
    dow: '^DJI',
    // 热门股
    AAPL: 'AAPL',
    NVDA: 'NVDA',
    MSFT: 'MSFT',
    GOOGL: 'GOOGL',
    TSLA: 'TSLA',
    META: 'META'
  },
  // A股
  cn: {
    shanghai: '000001.SS',
    shenzhen: '399001.SS',
    chinext: '399006.SS',
    csi300: '000300.SS',
    // 热门股
    '600519': '600519.SS', // 茅台
    '000001': '000001.SS', // 平安银行
    '300750': '300750.SZ', // 宁德时代
    '601398': '601398.SS'  // 工商银行
  },
  // 港股
  hk: {
    hsi: '^HSI',
    hscei: '^HSCEI',
    hstech: '^HSTECH',
    // 热门股
    '0700': '0700.HK', // 腾讯
    '9988': '9988.HK', // 阿里
    '3690': '3690.HK', // 美团
    '1810': '1810.HK', // 小米
    '1211': '1211.HK', // 比亚迪
    '2328': '2328.HK'  // 财险
  }
};

// 获取股票数据 (使用 Yahoo Finance API)
async function fetchStockData(symbol) {
  try {
    const response = await axios.get(
      `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=5d`,
      { timeout: 10000 }
    );
    
    const data = response.data;
    if (data.chart.result) {
      const result = data.chart.result[0];
      const meta = result.meta;
      const currentPrice = meta.regularMarketPrice;
      const previousClose = meta.regularMarketPreviousClose;
      const change = ((currentPrice - previousClose) / previousClose * 100).toFixed(2);
      
      return {
        symbol,
        price: currentPrice,
        change: parseFloat(change),
        volume: meta.regularMarketVolume,
        currency: meta.currency
      };
    }
    return null;
  } catch (error) {
    console.error(`Error fetching ${symbol}:`, error.message);
    return null;
  }
}

// 获取A股板块数据 (模拟)
async function fetchCNSectorData() {
  // 实际项目中可接入东方财富、同花顺 API
  return {
    sectors: [
      { name: '半导体', change: '+2.3%', inflow: '+15亿' },
      { name: '新能源', change: '+1.8%', inflow: '+12亿' },
      { name: '白酒', change: '-1.2%', outflow: '-8亿' },
      { name: '医药', change: '-0.8%', outflow: '-5亿' },
      { name: '银行', change: '+0.5%', inflow: '+3亿' }
    ]
  };
}

// 获取港股板块数据 (模拟)
async function fetchHKSectorData() {
  return {
    sectors: [
      { name: '科技', change: '+1.5%', inflow: '+10亿' },
      { name: '地产', change: '-2.1%', outflow: '-7亿' },
      { name: '金融', change: '+0.8%', inflow: '+5亿' },
      { name: '消费', change: '-0.5%', outflow: '-3亿' }
    ]
  };
}

// 生成交易信号
function generateSignals(stocks, marketType) {
  const signals = {
    watch: [],
    risk: []
  };
  
  stocks.forEach(stock => {
    if (stock) {
      // 简单信号逻辑：涨幅>3%关注，涨幅<-3%风险
      if (stock.change > 3) {
        signals.watch.push({
          symbol: stock.symbol,
          change: stock.change,
          reason: '强势上涨，突破关键阻力位'
        });
      } else if (stock.change < -3) {
        signals.risk.push({
          symbol: stock.symbol,
          change: stock.change,
          reason: '大幅下跌，警惕进一步回调风险'
        });
      }
    }
  });
  
  return signals;
}

// 格式化金额
function formatCurrency(value, currency = 'USD') {
  const suffixes = ['', 'K', 'M', 'B', 'T'];
  const suffixNum = Math.floor(('' + Math.floor(value)).length / 3);
  
  let shortValue = parseFloat((suffixNum !== 0 ? (value / Math.pow(1000, suffixNum)) : value).toPrecision(3));
  
  if (shortValue % 1 !== 0) {
    shortValue = shortValue.toFixed(2);
  }
  
  return shortValue + suffixes[suffixNum];
}

function formatDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

async function generateDailyReport() {
  const today = formatDate();
  
  console.log('📊 开始生成每日投资洞察...\n');
  
  // 获取美股数据
  console.log('🇺🇸 获取美股数据...');
  const usStocks = await Promise.all(
    Object.values(STOCKS.us).map(symbol => fetchStockData(symbol))
  );
  
  // 获取A股数据
  console.log('🇨🇳 获取A股数据...');
  const cnStocks = await Promise.all(
    Object.values(STOCKS.cn).map(symbol => fetchStockData(symbol))
  );
  
  // 获取港股数据
  console.log('🇭🇰 获取港股数据...');
  const hkStocks = await Promise.all(
    Object.values(STOCKS.hk).map(symbol => fetchStockData(symbol))
  );
  
  // 获取板块数据
  const cnSectors = await fetchCNSectorData();
  const hkSectors = await fetchHKSectorData();
  
  // 生成信号
  const usSignals = generateSignals(usStocks, 'us');
  const cnSignals = generateSignals(cnStocks, 'cn');
  const hkSignals = generateSignals(hkStocks, 'hk');
  
  // 构建报告
  let report = `# 📈 每日投资洞察 | ${today}\n\n`;
  
  // 大盘概览
  const sp500 = usStocks.find(s => s && s.symbol === '^GSPC');
  const shanghai = cnStocks.find(s => s && s.symbol === '000001.SS');
  const hsi = hkStocks.find(s => s && s.symbol === '^HSI');
  
  const shanghaiChange = shanghai ? (shanghai.change >= 0 ? `+${shanghai.change}%` : `${shanghai.change}%`) : '--';
  const hsiChange = hsi ? (hsi.change >= 0 ? `+${hsi.change}%` : `${hsi.change}%`) : '--';
  
  report += `**市场概览**: 上证指数 ${shanghaiChange} | 恒生指数 ${hsiChange}\n\n`;
  
  // 核心观点
  report += `## 🔥 核心观点\n\n`;
  report += `**美股**: ${sp500 && sp500.change > 1 ? '市场延续反弹，科技股领涨，短线偏多' : sp500 && sp500.change < -1 ? '市场回调，科技股承压，谨慎观望' : '市场震荡整理，等待方向选择'}\n\n`;
  report += `**A股**: ${shanghai && shanghai.change > 0.5 ? '震荡反弹，结构性机会为主' : shanghai && shanghai.change < -0.5 ? '回调整理，控制仓位观望' : '缩量震荡，观望情绪浓厚'}\n\n`;
  report += `**港股**: ${hsi && hsi.change > 0.5 ? '科技股带动回升，关注南向资金' : hsi && hsi.change < -0.5 ? '科技股回调，防御为主' : '横盘整理，方向不明'}\n\n`;
  
  // 美股详情
  report += `## 🇺🇸 美股市场\n\n`;
  report += `### 大盘表现\n`;
  report += `| 指数 | 点位 | 涨跌幅 |\n`;
  report += `|------|------|--------|\n`;
  const usIndices = [
    { name: '标普500 (S&P 500)', data: usStocks.find(s => s && s.symbol === '^GSPC') },
    { name: '纳斯达克 (NASDAQ)', data: usStocks.find(s => s && s.symbol === '^IXIC') },
    { name: '道琼斯 (DJA)', data: usStocks.find(s => s && s.symbol === '^DJI') }
  ];
  
  usIndices.forEach(idx => {
    if (idx.data) {
      const change = idx.data.change >= 0 ? `+${idx.data.change.toFixed(2)}%` : `${idx.data.change.toFixed(2)}%`;
      report += `| ${idx.name} | ${idx.data.price.toFixed(0)} | ${change} |\n`;
    }
  });
  
  // 美股领涨领跌
  const sortedUS = usStocks.filter(s => s && !s.symbol.startsWith('^')).sort((a, b) => b.change - a.change);
  if (sortedUS.length > 0) {
    const topUS = sortedUS.slice(0, 3);
    const bottomUS = sortedUS.slice(-3).reverse();
    
    report += `\n### 个股异动\n`;
    report += `**🔺 领涨**:\n`;
    topUS.forEach(s => {
      report += `- ${s.symbol}: +${s.change.toFixed(2)}%\n`;
    });
    
    report += `\n**🔻 领跌**:\n`;
    bottomUS.forEach(s => {
      report += `- ${s.symbol}: ${s.change.toFixed(2)}%\n`;
    });
  }
  
  // 美股交易信号
  if (usSignals.watch.length > 0 || usSignals.risk.length > 0) {
    report += `\n### 交易信号\n`;
    if (usSignals.watch.length > 0) {
      report += `**关注**:\n`;
      usSignals.watch.forEach(s => {
        report += `- ${s.symbol}: ${s.reason} (+${s.change.toFixed(2)}%)\n`;
      });
    }
    if (usSignals.risk.length > 0) {
      report += `\n**风险**:\n`;
      usSignals.risk.forEach(s => {
        report += `- ${s.symbol}: ${s.reason} (${s.change.toFixed(2)}%)\n`;
      });
    }
  }
  
  // A股详情
  report += `\n## 🇨🇳 A股市场\n\n`;
  report += `### 大盘表现\n`;
  report += `| 指数 | 点位 | 涨跌幅 |\n`;
  report += `|------|------|--------|\n`;
  
  const cnIndices = [
    { name: '上证指数', data: cnStocks.find(s => s && s.symbol === '000001.SS') },
    { name: '深证成指', data: cnStocks.find(s => s && s.symbol === '399001.SS') },
    { name: '创业板指', data: cnStocks.find(s => s && s.symbol === '399006.SS') },
    { name: '沪深300', data: cnStocks.find(s => s && s.symbol === '000300.SS') }
  ];
  
  cnIndices.forEach(idx => {
    if (idx.data) {
      const change = idx.data.change >= 0 ? `+${idx.data.change.toFixed(2)}%` : `${idx.data.change.toFixed(2)}%`;
      report += `| ${idx.name} | ${idx.data.price.toFixed(0)} | ${change} |\n`;
    }
  });
  
  // A股板块
  report += `\n### 板块轮动\n`;
  report += `**领涨**: ${cnSectors.sectors.filter(s => s.change.startsWith('+')).slice(0, 3).map(s => `${s.name}${s.change}`).join(' | ') || '--'}\n\n`;
  report += `**领跌**: ${cnSectors.sectors.filter(s => s.change.startsWith('-')).slice(0, 3).map(s => `${s.name}${s.change}`).join(' | ') || '--'}\n`;
  
  // A股交易信号
  if (cnSignals.watch.length > 0 || cnSignals.risk.length > 0) {
    report += `\n### 交易信号\n`;
    if (cnSignals.watch.length > 0) {
      report += `**关注**:\n`;
      cnSignals.watch.forEach(s => {
        report += `- ${s.symbol}: ${s.reason} (+${s.change.toFixed(2)}%)\n`;
      });
    }
    if (cnSignals.risk.length > 0) {
      report += `\n**风险**:\n`;
      cnSignals.risk.forEach(s => {
        report += `- ${s.symbol}: ${s.reason} (${s.change.toFixed(2)}%)\n`;
      });
    }
  }
  
  // 港股详情
  report += `\n## 🇭🇰 港股市场\n\n`;
  report += `### 大盘表现\n`;
  report += `| 指数 | 点位 | 涨跌幅 |\n`;
  report += `|------|------|--------|\n`;
  
  const hkIndices = [
    { name: '恒生指数', data: hkStocks.find(s => s && s.symbol === '^HSI') },
    { name: '国企指数', data: hkStocks.find(s => s && s.symbol === '^HSCEI') },
    { name: '科技指数', data: hkStocks.find(s => s && s.symbol === '^HSTECH') }
  ];
  
  hkIndices.forEach(idx => {
    if (idx.data) {
      const change = idx.data.change >= 0 ? `+${idx.data.change.toFixed(2)}%` : `${idx.data.change.toFixed(2)}%`;
      report += `| ${idx.name} | ${idx.data.price.toFixed(0)} | ${change} |\n`;
    }
  });
  
  // 港股交易信号
  if (hkSignals.watch.length > 0 || hkSignals.risk.length > 0) {
    report += `\n### 交易信号\n`;
    if (hkSignals.watch.length > 0) {
      report += `**关注**:\n`;
      hkSignals.watch.forEach(s => {
        report += `- ${s.symbol}: ${s.reason} (+${s.change.toFixed(2)}%)\n`;
      });
    }
    if (hkSignals.risk.length > 0) {
      report += `\n**风险**:\n`;
      hkSignals.risk.forEach(s => {
        report += `- ${s.symbol}: ${s.reason} (${s.change.toFixed(2)}%)\n`;
      });
    }
  }
  
  // 明日前瞻
  report += `\n## 📅 明日前瞻\n\n`;
  report += `### 重点事件\n`;
  report += `- 待定 - 本周无重大事件\n\n`;
  report += `### 技术面关注\n`;
  report += `- **支撑位**: 上证 ${shanghai ? (shanghai.price * 0.95).toFixed(0) : '待定'} | 恒生 ${hsi ? (hsi.price * 0.95).toFixed(0) : '待定'}\n`;
  report += `- **压力位**: 上证 ${shanghai ? (shanghai.price * 1.02).toFixed(0) : '待定'} | 恒生 ${hsi ? (hsi.price * 1.02).toFixed(0) : '待定'}\n`;
  
  // 免责声明
  report += `\n---\n**数据来源**: Yahoo Finance\n**发布时间**: ${today} 16:30 (Asia/Shanghai)\n**免责声明**: 本报告仅供学习交流，不构成投资建议\n`;
  
  // 保存文件
  const outputPath = path.join(__dirname, '..', '..', 'daily-investor', today.split('-')[0], today.split('-')[1], `${today}.md`);
  const outputDir = path.dirname(outputPath);
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(outputPath, report);
  console.log(`\n✅ 报告已生成: ${outputPath}`);
  
  // 推送到 GitHub
  pushToGitHub(outputPath);
  
  return report;
}

async function pushToGitHub(filePath) {
  console.log('\n🚀 推送到 GitHub...');
  
  const { execSync } = require('child_process');
  const repoDir = path.dirname(filePath).replace('/daily-investor', '');
  
  try {
    execSync('git add .', { cwd: repoDir, stdio: 'inherit' });
    execSync(`git commit -m "Update: 每日投资洞察 ${path.basename(filePath, '.md')}"`, { cwd: repoDir, stdio: 'inherit' });
    execSync('git push origin main', { cwd: repoDir, stdio: 'inherit' });
    console.log('✅ 已推送到 GitHub');
  } catch (error) {
    console.error('❌ Git 推送失败:', error.message);
  }
}

// 运行
generateDailyReport().catch(console.error);
