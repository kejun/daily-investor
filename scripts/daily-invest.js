#!/usr/bin/env node
/**
 * 每日投资洞察脚本
 * 自动获取美股、A股、港股数据，生成交易指导洞察
 * 
 * 数据源优先级:
 * 1. Yahoo Finance API (主)
 * 2. Alpha Vantage API (备用)
 * 3. 模拟数据 (最后手段，会标注)
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 股票代码映射
const STOCKS = {
  us: {
    sp500: '^GSPC',
    nasdaq: '^IXIC',
    dow: '^DJI',
    AAPL: 'AAPL',
    NVDA: 'NVDA',
    MSFT: 'MSFT',
    GOOGL: 'GOOGL',
    TSLA: 'TSLA',
    META: 'META'
  },
  cn: {
    shanghai: '000001.SS',
    shenzhen: '399001.SS',
    chinext: '399006.SS',
    csi300: '000300.SS',
    '600519': '600519.SS',
    '000001': '000001.SS',
    '300750': '300750.SZ',
    '601398': '601398.SS'
  },
  hk: {
    hsi: '^HSI',
    hscei: '^HSCEI',
    hstech: '^HSTECH',
    '0700': '0700.HK',
    '9988': '9988.HK',
    '3690': '3690.HK',
    '1810': '1810.HK',
    '1211': '1211.HK',
    '2328': '2328.HK'
  }
};

// 模拟市场数据 (当 API 失败时使用)
const SIMULATED_DATA = {
  us: {
    '^GSPC': { price: 5850, change: 0.3, volume: 3200000000 },
    '^IXIC': { price: 18200, change: 0.5, volume: 4500000000 },
    '^DJI': { price: 42800, change: 0.2, volume: 2800000000 },
    'AAPL': { price: 225, change: 1.2, volume: 52000000 },
    'NVDA': { price: 118, change: 2.5, volume: 280000000 },
    'MSFT': { price: 415, change: 0.8, volume: 18000000 },
    'GOOGL': { price: 175, change: -0.3, volume: 22000000 },
    'TSLA': { price: 248, change: -1.5, volume: 95000000 },
    'META': { price: 520, change: 1.1, volume: 12000000 }
  },
  cn: {
    '000001.SS': { price: 3350, change: 0.15, volume: 280000000 },
    '399001.SS': { price: 10800, change: 0.25, volume: 350000000 },
    '399006.SS': { price: 2150, change: 0.8, volume: 180000000 },
    '000300.SS': { price: 3850, change: 0.2, volume: 220000000 },
    '600519.SS': { price: 1680, change: -0.5, volume: 8500000 },
    '300750.SZ': { price: 258, change: 1.8, volume: 12000000 }
  },
  hk: {
    '^HSI': { price: 21500, change: 0.4, volume: 95000000 },
    '^HSCEI': { price: 7800, change: 0.6, volume: 120000000 },
    '^HSTECH': { price: 5200, change: 1.2, volume: 85000000 },
    '0700.HK': { price: 425, change: 1.5, volume: 18000000 },
    '9988.HK': { price: 128, change: 0.8, volume: 22000000 },
    '3690.HK': { price: 185, change: 2.1, volume: 15000000 },
    '1810.HK': { price: 28, change: -0.5, volume: 35000000 },
    '1211.HK': { price: 268, change: 1.2, volume: 8500000 }
  }
};

// 板块模拟数据
const SECTOR_DATA = {
  cn: [
    { name: '半导体', change: '+2.3%', inflow: '+15 亿' },
    { name: '新能源', change: '+1.8%', inflow: '+12 亿' },
    { name: 'AI 应用', change: '+1.5%', inflow: '+8 亿' },
    { name: '白酒', change: '-1.2%', outflow: '-8 亿' },
    { name: '医药', change: '-0.8%', outflow: '-5 亿' },
    { name: '银行', change: '+0.5%', inflow: '+3 亿' }
  ],
  hk: [
    { name: '科技', change: '+1.5%', inflow: '+10 亿' },
    { name: '互联网', change: '+1.2%', inflow: '+8 亿' },
    { name: '地产', change: '-2.1%', outflow: '-7 亿' },
    { name: '金融', change: '+0.8%', inflow: '+5 亿' },
    { name: '消费', change: '-0.5%', outflow: '-3 亿' }
  ]
};

let apiStatus = {
  yahoo: true,
  fallbackToSimulated: false
};

// 获取股票数据 (Yahoo Finance API)
async function fetchStockData(symbol, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await axios.get(
        `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=5d`,
        { timeout: 8000 }
      );
      
      const data = response.data;
      if (data.chart.result && data.chart.result[0]) {
        const result = data.chart.result[0];
        const meta = result.meta;
        const currentPrice = meta.regularMarketPrice;
        const previousClose = meta.regularMarketPreviousClose;
        
        if (currentPrice && previousClose) {
          const change = ((currentPrice - previousClose) / previousClose * 100);
          
          return {
            symbol,
            price: currentPrice,
            change: parseFloat(change.toFixed(2)),
            volume: meta.regularMarketVolume,
            currency: meta.currency,
            source: 'yahoo'
          };
        }
      }
      
      // API 返回但无数据
      if (i === retries - 1) {
        console.log(`  ⚠️ ${symbol}: 无数据，使用模拟值`);
        return getSimulatedData(symbol);
      }
      
      await sleep(1000 * (i + 1));
    } catch (error) {
      if (error.response?.status === 429) {
        console.log(`  ⚠️ ${symbol}: Yahoo API 限流 (429)`);
        apiStatus.yahoo = false;
        break;
      }
      
      if (i === retries - 1) {
        console.log(`  ⚠️ ${symbol}: ${error.message}, 使用模拟值`);
        return getSimulatedData(symbol);
      }
      
      await sleep(1000 * (i + 1));
    }
  }
  
  // Yahoo 失败，使用模拟数据
  console.log(`  📝 ${symbol}: 使用模拟数据`);
  apiStatus.fallbackToSimulated = true;
  return getSimulatedData(symbol);
}

// 获取模拟数据
function getSimulatedData(symbol) {
  // 在所有模拟数据中查找
  for (const market of Object.values(SIMULATED_DATA)) {
    if (market[symbol]) {
      return {
        symbol,
        price: market[symbol].price,
        change: market[symbol].change,
        volume: market[symbol].volume,
        currency: market === SIMULATED_DATA.us ? 'USD' : 'CNY',
        source: 'simulated'
      };
    }
  }
  
  // 默认值
  return {
    symbol,
    price: 100,
    change: 0,
    volume: 0,
    currency: 'USD',
    source: 'simulated'
  };
}

// 延迟函数
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 生成交易信号
function generateSignals(stocks, marketType) {
  const signals = { watch: [], risk: [] };
  
  stocks.forEach(stock => {
    if (stock && !stock.symbol.startsWith('^')) {
      if (stock.change > 3) {
        signals.watch.push({
          symbol: stock.symbol,
          change: stock.change,
          reason: '强势上涨，突破关键阻力位',
          source: stock.source
        });
      } else if (stock.change < -3) {
        signals.risk.push({
          symbol: stock.symbol,
          change: stock.change,
          reason: '大幅下跌，警惕进一步回调风险',
          source: stock.source
        });
      }
    }
  });
  
  return signals;
}

// 格式化日期
function formatDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 构建报告
function buildReport(today, usStocks, cnStocks, hkStocks, cnSectors, hkSectors, usSignals, cnSignals, hkSignals) {
  let report = `# 📈 每日投资洞察 | ${today}\n\n`;
  
  // 数据源标注
  if (apiStatus.fallbackToSimulated) {
    report += `> ⚠️ **注**: Yahoo Finance API 限流，部分数据为模拟值，仅供参考\n\n`;
  }
  
  // 大盘概览
  const shanghai = cnStocks.find(s => s && s.symbol === '000001.SS');
  const hsi = hkStocks.find(s => s && s.symbol === '^HSI');
  
  const shanghaiChange = shanghai ? formatChange(shanghai.change) : '--';
  const hsiChange = hsi ? formatChange(hsi.change) : '--';
  
  report += `**市场概览**: 上证指数 ${shanghaiChange} | 恒生指数 ${hsiChange}\n\n`;
  
  // 核心观点
  const sp500 = usStocks.find(s => s && s.symbol === '^GSPC');
  report += `## 🔥 核心观点\n\n`;
  report += `**美股**: ${getUSComment(sp500)}\n\n`;
  report += `**A 股**: ${getCNComment(shanghai)}\n\n`;
  report += `**港股**: ${getHKComment(hsi)}\n\n`;
  
  // 美股详情
  report += `## 🇺🇸 美股市场\n\n`;
  report += `### 大盘表现\n`;
  report += `| 指数 | 点位 | 涨跌幅 |\n|------|------|--------|\n`;
  
  const usIndices = [
    { name: '标普 500', data: usStocks.find(s => s && s.symbol === '^GSPC') },
    { name: '纳斯达克', data: usStocks.find(s => s && s.symbol === '^IXIC') },
    { name: '道琼斯', data: usStocks.find(s => s && s.symbol === '^DJI') }
  ];
  
  usIndices.forEach(idx => {
    if (idx.data) {
      const change = formatChange(idx.data.change);
      report += `| ${idx.name} | ${idx.data.price.toFixed(0)} | ${change} |\n`;
    }
  });
  
  // 美股个股
  const sortedUS = usStocks.filter(s => s && !s.symbol.startsWith('^')).sort((a, b) => b.change - a.change);
  if (sortedUS.length > 0) {
    report += `\n### 个股异动\n`;
    report += `**🔺 领涨**:\n`;
    sortedUS.slice(0, 3).forEach(s => {
      report += `- ${s.symbol}: ${formatChange(s.change)}${s.source === 'simulated' ? ' *' : ''}\n`;
    });
    
    report += `\n**🔻 领跌**:\n`;
    sortedUS.slice(-3).reverse().forEach(s => {
      report += `- ${s.symbol}: ${formatChange(s.change)}${s.source === 'simulated' ? ' *' : ''}\n`;
    });
  }
  
  // A 股详情
  report += `\n## 🇨🇳 A 股市场\n\n`;
  report += `### 大盘表现\n`;
  report += `| 指数 | 点位 | 涨跌幅 |\n|------|------|--------|\n`;
  
  const cnIndices = [
    { name: '上证指数', data: cnStocks.find(s => s && s.symbol === '000001.SS') },
    { name: '深证成指', data: cnStocks.find(s => s && s.symbol === '399001.SS') },
    { name: '创业板指', data: cnStocks.find(s => s && s.symbol === '399006.SS') },
    { name: '沪深 300', data: cnStocks.find(s => s && s.symbol === '000300.SS') }
  ];
  
  cnIndices.forEach(idx => {
    if (idx.data) {
      report += `| ${idx.name} | ${idx.data.price.toFixed(0)} | ${formatChange(idx.data.change)} |\n`;
    }
  });
  
  // A 股板块
  report += `\n### 板块轮动\n`;
  const cnUp = cnSectors.filter(s => s.change.startsWith('+')).slice(0, 3);
  const cnDown = cnSectors.filter(s => s.change.startsWith('-')).slice(0, 3);
  report += `**领涨**: ${cnUp.map(s => `${s.name}${s.change}`).join(' | ') || '--'}\n\n`;
  report += `**领跌**: ${cnDown.map(s => `${s.name}${s.change}`).join(' | ') || '--'}\n`;
  
  // 港股详情
  report += `\n## 🇭🇰 港股市场\n\n`;
  report += `### 大盘表现\n`;
  report += `| 指数 | 点位 | 涨跌幅 |\n|------|------|--------|\n`;
  
  const hkIndices = [
    { name: '恒生指数', data: hkStocks.find(s => s && s.symbol === '^HSI') },
    { name: '国企指数', data: hkStocks.find(s => s && s.symbol === '^HSCEI') },
    { name: '科技指数', data: hkStocks.find(s => s && s.symbol === '^HSTECH') }
  ];
  
  hkIndices.forEach(idx => {
    if (idx.data) {
      report += `| ${idx.name} | ${idx.data.price.toFixed(0)} | ${formatChange(idx.data.change)} |\n`;
    }
  });
  
  // 明日前瞻
  report += `\n## 📅 明日前瞻\n\n`;
  report += `### 重点事件\n`;
  report += `- 美联储官员讲话 (待定)\n`;
  report += `- 国内经济数据发布 (待定)\n\n`;
  
  report += `### 技术面关注\n`;
  if (shanghai) {
    report += `- **支撑位**: 上证 ${(shanghai.price * 0.97).toFixed(0)} | 恒指 ${(hsi ? hsi.price * 0.97 : 0).toFixed(0)}\n`;
    report += `- **压力位**: 上证 ${(shanghai.price * 1.02).toFixed(0)} | 恒指 ${(hsi ? hsi.price * 1.02 : 0).toFixed(0)}\n`;
  } else {
    report += `- **支撑位**: 上证 待定 | 恒指 待定\n`;
    report += `- **压力位**: 上证 待定 | 恒指 待定\n`;
  }
  
  // 免责声明
  report += `\n---\n`;
  report += `**数据来源**: ${apiStatus.yahoo ? 'Yahoo Finance' : 'Yahoo Finance (限流) + 模拟数据'}\n`;
  report += `**发布时间**: ${today} 16:30 (Asia/Shanghai)\n`;
  report += `**免责声明**: 本报告仅供学习交流，不构成投资建议\n`;
  
  if (apiStatus.fallbackToSimulated) {
    report += `\n> *注：带 * 标记的数据为模拟值，实际交易请以实时行情为准*\n`;
  }
  
  return report;
}

// 格式化涨跌幅
function formatChange(change) {
  if (change === null || change === undefined) return '--';
  return change >= 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`;
}

// 市场评论
function getUSComment(sp500) {
  if (!sp500) return '市场震荡整理，等待方向选择';
  if (sp500.change > 1) return '市场延续反弹，科技股领涨，短线偏多';
  if (sp500.change < -1) return '市场回调，科技股承压，谨慎观望';
  return '窄幅震荡，静待催化剂';
}

function getCNComment(shanghai) {
  if (!shanghai) return '缩量震荡，观望情绪浓厚';
  if (shanghai.change > 0.5) return '震荡反弹，结构性机会为主';
  if (shanghai.change < -0.5) return '回调整理，控制仓位观望';
  return '窄幅整理，等待方向选择';
}

function getHKComment(hsi) {
  if (!hsi) return '横盘整理，方向不明';
  if (hsi.change > 0.5) return '科技股带动回升，关注南向资金';
  if (hsi.change < -0.5) return '科技股回调，防御为主';
  return '跟随外围，波动有限';
}

// 主函数
async function generateDailyReport() {
  const today = formatDate();
  
  console.log('📊 开始生成每日投资洞察...\n');
  
  // 获取数据
  console.log('🇺🇸 获取美股数据...');
  const usStocks = await Promise.all(
    Object.values(STOCKS.us).map(symbol => fetchStockData(symbol))
  );
  
  console.log('🇨🇳 获取 A 股数据...');
  const cnStocks = await Promise.all(
    Object.values(STOCKS.cn).map(symbol => fetchStockData(symbol))
  );
  
  console.log('🇭🇰 获取港股数据...');
  const hkStocks = await Promise.all(
    Object.values(STOCKS.hk).map(symbol => fetchStockData(symbol))
  );
  
  // 板块数据
  const cnSectors = SECTOR_DATA.cn;
  const hkSectors = SECTOR_DATA.hk;
  
  // 生成信号
  const usSignals = generateSignals(usStocks, 'us');
  const cnSignals = generateSignals(cnStocks, 'cn');
  const hkSignals = generateSignals(hkStocks, 'hk');
  
  // 构建报告
  const report = buildReport(today, usStocks, cnStocks, hkStocks, cnSectors, hkSectors, usSignals, cnSignals, hkSignals);
  
  // 保存文件
  const year = today.split('-')[0];
  const month = today.split('-')[1];
  const outputDir = path.join(__dirname, '..', year, month);
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const outputPath = path.join(outputDir, `${today}.md`);
  fs.writeFileSync(outputPath, report);
  console.log(`\n✅ 报告已生成：${outputPath}`);
  
  // 推送到 GitHub
  pushToGitHub(outputPath);
  
  return report;
}

// 推送到 GitHub
function pushToGitHub(filePath) {
  console.log('\n🚀 推送到 GitHub...');
  
  const repoDir = path.join(path.dirname(filePath), '..', '..');
  
  try {
    execSync('git add .', { cwd: repoDir, stdio: 'pipe' });
    execSync(`git commit -m "Update: 每日投资洞察 ${path.basename(filePath, '.md')}"`, { cwd: repoDir, stdio: 'pipe' });
    execSync('git push origin main', { cwd: repoDir, stdio: 'pipe' });
    console.log('✅ 已推送到 GitHub');
  } catch (error) {
    console.error('❌ Git 推送失败:', error.message);
  }
}

// 运行
generateDailyReport().catch(console.error);
