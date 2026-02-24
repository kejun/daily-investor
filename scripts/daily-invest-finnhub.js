#!/usr/bin/env node
/**
 * 每日投资洞察脚本 - 使用 Finnhub API
 * 自动获取美股、A 股、港股数据，生成交易指导洞察
 * 
 * 数据源:
 * 1. Finnhub API (美股实时数据)
 * 2. 东方财富 API (A 股/港股实时数据)
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 读取 .env 文件
const envPath = path.join(__dirname, '..', '.env');
const envContent = fs.readFileSync(envPath, 'utf-8');
const finnubMatch = envContent.match(/FINNHUB_API_KEY=(.+)/);

if (!finnubMatch) {
  console.error('❌ FINNHUB_API_KEY not found in .env file');
  process.exit(1);
}

const FINNHUB_API_KEY = finnubMatch[1].trim();
console.log(`✅ Finnhub API Key loaded\n`);

// 美股代码列表
const US_STOCKS = {
  indices: {
    '标普 500': 'SPY',  // 使用 ETF 代替指数
    '纳斯达克': 'QQQ',
    '道琼斯': 'DIA'
  },
  stocks: ['NVDA', 'AAPL', 'TSLA', 'META', 'MSFT', 'GOOGL', 'AMD']
};

// A 股和港股代码（通过 Python 脚本获取）
const CN_STOCKS = {
  a_indices: ['上证指数', '深证成指', '创业板指', '沪深 300'],
  a_stocks: ['600519', '000858', '300750', '002594', '601318'],
  hk_index: '恒生指数',
  hk_stocks: ['00700', '09988', '03690', '01810', '02318']
};

/**
 * 从 Finnhub 获取美股数据
 */
async function fetchUSMarketData() {
  console.log('📊 获取美股数据 (Finnhub)...');
  
  const result = {
    indices: {},
    stocks: {}
  };
  
  // 获取主要指数
  for (const [name, symbol] of Object.entries(US_STOCKS.indices)) {
    try {
      const response = await axios.get('https://finnhub.io/api/v1/quote', {
        params: { symbol, token: FINNHUB_API_KEY }
      });
      
      const data = response.data;
      if (data.c !== undefined) {
        const current = data.c;
        const prevClose = data.pc;
        const change = current - prevClose;
        const changePercent = ((change / prevClose) * 100);
        
        result.indices[name] = {
          current,
          change,
          change_percent: parseFloat(changePercent.toFixed(2))
        };
        
        console.log(`  ✓ ${name}: ${current.toFixed(2)} (${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%)`);
      } else {
        console.log(`  ✗ ${name}: 数据无效`);
      }
    } catch (error) {
      console.log(`  ✗ ${name}: ${error.message}`);
    }
    
    // 速率限制：至少间隔 1 秒
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // 获取热门个股
  for (const symbol of US_STOCKS.stocks) {
    try {
      const response = await axios.get('https://finnhub.io/api/v1/quote', {
        params: { symbol, token: FINNHUB_API_KEY }
      });
      
      const data = response.data;
      if (data.c !== undefined) {
        const current = data.c;
        const prevClose = data.pc;
        const change = current - prevClose;
        const changePercent = ((change / prevClose) * 100);
        
        result.stocks[symbol] = {
          current: parseFloat(current.toFixed(2)),
          change: parseFloat(change.toFixed(2)),
          change_percent: parseFloat(changePercent.toFixed(2))
        };
        
        console.log(`  ✓ ${symbol}: $${current.toFixed(2)} (${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%)`);
      }
    } catch (error) {
      console.log(`  ✗ ${symbol}: ${error.message}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return result;
}

/**
 * 调用 Python 脚本获取 A 股和港股数据
 */
async function fetchCNHKMarketData() {
  console.log('\n📈 获取 A 股和港股数据 (东方财富)...');
  
  try {
    const scriptPath = path.join(__dirname, 'cn_market_data.py');
    const output = execSync(`python3 ${scriptPath}`, { encoding: 'utf-8' });
    
    // 解析 Python 脚本的输出（JSON 格式）
    const lines = output.trim().split('\n');
    const jsonLine = lines.find(line => line.startsWith('{'));
    
    if (jsonLine) {
      const data = JSON.parse(jsonLine);
      console.log('  ✓ A 股和港股数据获取成功');
      return data;
    }
  } catch (error) {
    console.log(`  ✗ A 股/港股数据获取失败：${error.message}`);
  }
  
  return null;
}

/**
 * 生成投资洞察文本
 */
function generateInsights(usData, cnhkData) {
  const insights = [];
  
  // 美股洞察
  if (usData && usData.indices) {
    const sp500 = usData.indices['标普 500'];
    if (sp500 && sp500.change_percent > 0.5) {
      insights.push(`美股强势上涨，标普 500 涨幅达 ${sp500.change_percent}%，市场情绪乐观`);
    } else if (sp500 && sp500.change_percent < -0.5) {
      insights.push(`美股回调，标普 500 下跌 ${Math.abs(sp500.change_percent)}%，注意风险`);
    }
  }
  
  // 领涨股票
  if (usData && usData.stocks) {
    const topGainer = Object.entries(usData.stocks)
      .sort((a, b) => b[1].change_percent - a[1].change_percent)[0];
    
    if (topGainer && topGainer[1].change_percent > 2) {
      insights.push(`${topGainer[0]} 领涨科技股，涨幅 ${topGainer[1].change_percent}%`);
    }
  }
  
  // A 股洞察
  if (cnhkData && cnhkData.a_indices) {
    const sh = cnhkData.a_indices['上证指数'];
    if (sh && sh.change_percent > 0.3) {
      insights.push(`A 股企稳反弹，上证涨超 ${sh.change_percent}%，关注成交量变化`);
    }
  }
  
  return insights;
}

/**
 * 生成 Markdown 报告
 */
function generateReport(dateStr, usData, cnhkData) {
  const year = dateStr.substring(0, 4);
  const month = dateStr.substring(5, 7);
  
  let report = `# 📊 每日投资洞察 | Daily Investment Insights\n`;
  report += `**${dateStr}** | 自动生成\n\n`;
  report += `---\n\n`;
  
  // 数据来源说明
  report += `**数据来源**: \n`;
  report += `- 美股：**Finnhub API** (实时行情)\n`;
  report += `- A 股/港股：**东方财富 API** (实时行情)\n\n`;
  report += `> ✅ 所有数据均为真实市场数据，无模拟成分\n\n`;
  report += `---\n\n`;
  
  // 市场概览
  report += `## 🌍 市场概览\n\n`;
  
  // 美股
  report += `### 美股\n\n`;
  report += `| 指数 | 当前 | 涨跌 |\n`;
  report += `|------|------|------|\n`;
  
  if (usData && usData.indices) {
    for (const [name, data] of Object.entries(usData.indices)) {
      if (data) {
        const sign = data.change_percent >= 0 ? '+' : '';
        report += `| **${name}** | ${data.current.toFixed(2)} | ${sign}${data.change_percent.toFixed(2)}% |\n`;
      }
    }
  }
  report += `\n`;
  
  // A 股
  report += `### A 股\n\n`;
  if (cnhkData && cnhkData.a_indices) {
    report += `| 指数 | 当前 | 涨跌 |\n`;
    report += `|------|------|------|\n`;
    
    for (const [name, data] of Object.entries(cnhkData.a_indices)) {
      if (data) {
        const sign = data.change_percent >= 0 ? '+' : '';
        report += `| **${name}** | ${data.current.toFixed(2)} | ${sign}${data.change_percent.toFixed(2)}% |\n`;
      }
    }
    report += `\n`;
  }
  
  // 港股
  report += `### 港股\n\n`;
  if (cnhkData && cnhkData.hk_indices) {
    report += `| 指数 | 当前 | 涨跌 |\n`;
    report += `|------|------|------|\n`;
    
    for (const [name, data] of Object.entries(cnhkData.hk_indices)) {
      if (data) {
        const sign = data.change_percent >= 0 ? '+' : '';
        report += `| **${name}** | ${data.current.toFixed(2)} | ${sign}${data.change_percent.toFixed(2)}% |\n`;
      }
    }
    report += `\n`;
  }
  
  // 美股个股表现
  report += `## 📈 美股个股\n\n`;
  report += `| 股票 | 价格 | 涨跌 |\n`;
  report += `|------|------|------|\n`;
  
  if (usData && usData.stocks) {
    const sortedStocks = Object.entries(usData.stocks)
      .sort((a, b) => b[1].change_percent - a[1].change_percent);
    
    for (const [symbol, data] of sortedStocks) {
      const sign = data.change_percent >= 0 ? '+' : '';
      report += `| ${symbol} | $${data.current.toFixed(2)} | ${sign}${data.change_percent.toFixed(2)}% |\n`;
    }
  }
  report += `\n`;
  
  // A 股板块
  report += `## 🇨🇳 A 股板块\n\n`;
  if (cnhkData && cnhkData.sectors) {
    report += `| 板块 | 涨幅 |\n`;
    report += `|------|------|\n`;
    
    for (const [sector, change] of Object.entries(cnhkData.sectors)) {
      const sign = change >= 0 ? '+' : '';
      report += `| ${sector} | ${sign}${change.toFixed(2)}% |\n`;
    }
    report += `\n`;
  }
  
  // 投资洞察
  report += `## 💡 投资洞察\n\n`;
  const insights = generateInsights(usData, cnhkData);
  
  if (insights.length > 0) {
    insights.forEach(insight => {
      report += `- ${insight}\n`;
    });
  } else {
    report += `- 市场震荡，建议观望\n`;
    report += `- 关注成交量变化和北向资金流向\n`;
  }
  report += `\n`;
  
  // 技术面
  report += `## 📐 技术面分析\n\n`;
  if (cnhkData && cnhkData.a_indices && cnhkData.a_indices['上证指数']) {
    const sh = cnhkData.a_indices['上证指数'];
    const support = (sh.current * 0.98).toFixed(0);
    const resistance = (sh.current * 1.02).toFixed(0);
    
    report += `**上证指数**:\n`;
    report += `- 支撑位：${support}\n`;
    report += `- 阻力位：${resistance}\n`;
    report += `- 策略：${sh.change_percent > 0 ? '持股待涨' : '逢低布局'}\n`;
  }
  report += `\n`;
  
  // 风险提示
  report += `## ⚠️ 风险提示\n\n`;
  report += `- 本文仅供参考，不构成投资建议\n`;
  report += `- 市场有风险，投资需谨慎\n`;
  report += `- 请结合个人风险承受能力独立决策\n\n`;
  
  report += `---\n`;
  report += `*自动生成于 ${new Date().toISOString()}*\n`;
  
  return report;
}

/**
 * 主函数
 */
async function main() {
  const dateStr = new Date().toISOString().split('T')[0];
  console.log(`📅 生成 ${dateStr} 的投资洞察报告\n`);
  
  // 获取美股数据
  const usData = await fetchUSMarketData();
  
  // 获取 A 股和港股数据
  const cnhkData = await fetchCNHKMarketData();
  
  // 生成报告
  console.log('\n📝 生成报告...');
  const report = generateReport(dateStr, usData, cnhkData);
  
  // 保存文件
  const year = dateStr.substring(0, 4);
  const month = dateStr.substring(5, 7);
  const dir = path.join(__dirname, '..', year, month);
  
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  const filePath = path.join(dir, `${dateStr}.md`);
  fs.writeFileSync(filePath, report, 'utf-8');
  
  console.log(`✅ 报告已保存至：${filePath}`);
  
  // Git 提交（可选）
  try {
    console.log('\n🔄 推送到 GitHub...');
    execSync('git add .', { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
    execSync(`git commit -m "Update: 每日投资洞察 ${dateStr}"`, { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
    execSync('git push origin main', { cwd: path.join(__dirname, '..'), stdio: 'ignore' });
    console.log('✅ Git 推送成功');
  } catch (error) {
    console.log('⚠️ Git 操作失败，请手动推送');
  }
}

// 运行
main().catch(error => {
  console.error('❌ 错误:', error.message);
  process.exit(1);
});
