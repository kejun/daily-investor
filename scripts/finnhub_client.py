#!/usr/bin/env python3
"""
Finnhub API 客户端 - 实时美股数据
替代 Yahoo Finance，提供真实市场数据
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class FinnhubClient:
    """Finnhub API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not set")
        
        self.base_url = "https://finnhub.io/api/v1"
        self.session = requests.Session()
        self.call_count = 0
        self.last_call_time = 0
    
    def _rate_limit(self):
        """速率限制：60 calls/min"""
        now = time.time()
        if now - self.last_call_time < 1.0:  # 至少间隔 1 秒
            time.sleep(1.0 - (now - self.last_call_time))
        self.last_call_time = time.time()
        self.call_count += 1
    
    def get_quote(self, symbol: str) -> Dict:
        """获取实时报价"""
        self._rate_limit()
        response = self.session.get(
            f"{self.base_url}/quote",
            params={"symbol": symbol, "token": self.api_key}
        )
        data = response.json()
        
        if 'c' not in data:
            raise ValueError(f"Invalid symbol or API error: {data}")
        
        return {
            'symbol': symbol,
            'current': data['c'],
            'high': data['h'],
            'low': data['l'],
            'open': data['o'],
            'previous_close': data['pc'],
            'change': data['c'] - data['pc'],
            'change_percent': ((data['c'] - data['pc']) / data['pc']) * 100 if data['pc'] else 0,
            'timestamp': datetime.fromtimestamp(data['t']).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_stock_candles(self, symbol: str, resolution: str = 'D', days: int = 30) -> Dict:
        """获取 K 线数据"""
        self._rate_limit()
        
        end = datetime.now()
        start = end - timedelta(days=days)
        
        response = self.session.get(
            f"{self.base_url}/stock/candle",
            params={
                "symbol": symbol,
                "resolution": resolution,
                "from": int(start.timestamp()),
                "to": int(end.timestamp()),
                "token": self.api_key
            }
        )
        data = response.json()
        
        if 's' not in data or data['s'] != 'ok':
            raise ValueError(f"Candle data error: {data}")
        
        return {
            'symbol': symbol,
            'timestamps': [datetime.fromtimestamp(t).strftime('%Y-%m-%d') for t in data.get('t', [])],
            'open': data.get('o', []),
            'high': data.get('h', []),
            'low': data.get('l', []),
            'close': data.get('c', []),
            'volume': data.get('v', [])
        }
    
    def get_company_profile(self, symbol: str) -> Dict:
        """获取公司简介"""
        self._rate_limit()
        
        response = self.session.get(
            f"{self.base_url}/stock/profile2",
            params={"symbol": symbol, "token": self.api_key}
        )
        data = response.json()
        
        return {
            'symbol': symbol,
            'name': data.get('name', ''),
            'industry': data.get('finnhubIndustry', ''),
            'description': data.get('description', '')[:500] if data.get('description') else '',
            'ceo': data.get('ceo', ''),
            'employees': data.get('employeeTotal', 0),
            'headquarters': data.get('address', '')
        }
    
    def get_earnings_surprise(self, symbol: str, limit: int = 4) -> List[Dict]:
        """获取财报惊喜数据"""
        self._rate_limit()
        
        response = self.session.get(
            f"{self.base_url}/stock/earnings-surprise",
            params={"symbol": symbol, "token": self.api_key}
        )
        data = response.json()
        
        if not isinstance(data, list):
            return []
        
        return data[:limit]
    
    def get_market_news(self, category: str = 'general') -> List[Dict]:
        """获取市场新闻"""
        self._rate_limit()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        response = self.session.get(
            f"{self.base_url}/company-news",
            params={
                "symbol": category if category != 'general' else 'AAPL',
                "from": today,
                "to": today,
                "token": self.api_key
            }
        )
        data = response.json()
        
        if not isinstance(data, list):
            return []
        
        return [{
            'headline': item.get('headline', ''),
            'summary': item.get('summary', '')[:200] if item.get('summary') else '',
            'url': item.get('url', ''),
            'source': item.get('source', ''),
            'datetime': datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M:%S')
        } for item in data[:10]]
    
    def get_technical_indicator(self, symbol: str, indicator: str = 'pmi', resolution: str = 'D') -> Dict:
        """获取技术指标"""
        self._rate_limit()
        
        response = self.session.get(
            f"{self.base_url}/indicator",
            params={
                "symbol": symbol,
                "resolution": resolution,
                "indicator": indicator,
                "token": self.api_key
            }
        )
        data = response.json()
        
        return data


def get_market_overview(client: FinnhubClient) -> Dict:
    """获取市场概览"""
    print("📊 获取市场概览...")
    
    # 主要指数（使用 ETF 代替）
    indices = {
        '标普 500': 'SPY',
        '纳斯达克': 'QQQ',
        '道琼斯': 'DIA'
    }
    
    overview = {}
    for name, symbol in indices.items():
        try:
            quote = client.get_quote(symbol)
            overview[name] = {
                'current': quote['current'],
                'change': quote['change'],
                'change_percent': quote['change_percent']
            }
            print(f"  ✓ {name}: {quote['current']:.2f} ({quote['change_percent']:+.2f}%)")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            overview[name] = None
        
        time.sleep(0.5)
    
    return overview


def get_stocks_performance(client: FinnhubClient, symbols: List[str]) -> Dict:
    """获取个股表现"""
    print("\n📈 获取个股表现...")
    
    performance = {}
    for symbol in symbols:
        try:
            quote = client.get_quote(symbol)
            performance[symbol] = {
                'current': quote['current'],
                'change': quote['change'],
                'change_percent': quote['change_percent'],
                'volume': 'N/A'  # Finnhub free tier 不包含成交量
            }
            print(f"  ✓ {symbol}: ${quote['current']:.2f} ({quote['change_percent']:+.2f}%)")
        except Exception as e:
            print(f"  ✗ {symbol}: {e}")
            performance[symbol] = None
        
        time.sleep(0.5)
    
    return performance


if __name__ == "__main__":
    # 测试
    client = FinnhubClient()
    
    print(f"Finnhub API 调用次数：{client.call_count}/60 (每分钟限制)\n")
    
    # 测试市场概览
    overview = get_market_overview(client)
    
    # 测试个股
    stocks = ['NVDA', 'AAPL', 'TSLA', 'META', 'MSFT']
    performance = get_stocks_performance(client, stocks)
    
    print(f"\n✅ 测试完成，总调用次数：{client.call_count}")
