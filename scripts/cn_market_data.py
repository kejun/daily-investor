#!/usr/bin/env python3
"""
中国股市数据客户端 - A 股 + 港股
使用东方财富 K 线接口获取最近交易日数据
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CNMarketClient:
    """中国市场数据客户端"""
    
    def __init__(self):
        self.kline_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        self.session = requests.Session()
        self.last_call_time = 0
        self.cache = {}
        self.cache_time = 0
        self.cache_ttl = 300
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        })
    
    def _rate_limit(self, min_interval: float = 0.3):
        now = time.time()
        elapsed = now - self.last_call_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_call_time = time.time()
    
    def _get_latest_kline(self, secid: str) -> Optional[Dict]:
        """获取最近一根 K 线数据"""
        try:
            params = {
                'secid': secid,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57',
                'klt': '101',  # 日线
                'fqt': '1',    # 前复权
                'end': '20500101',
                'lmt': '2'     # 最近 2 天（计算涨跌幅需要）
            }
            
            self._rate_limit()
            resp = self.session.get(self.kline_url, params=params, timeout=10)
            result = resp.json()
            
            data = result.get('data', {})
            klines = data.get('klines', [])
            
            if len(klines) >= 1:
                # 格式：日期,开盘,收盘,最高,最低,成交量,成交额
                latest = klines[-1].split(',')
                
                kline_data = {
                    'date': latest[0],
                    'open': float(latest[1]),
                    'current': float(latest[2]),
                    'high': float(latest[3]),
                    'low': float(latest[4]),
                    'volume': int(latest[5]),
                    'amount': float(latest[6]),
                    'name': data.get('name', '')
                }
                
                # 计算涨跌幅
                if len(klines) >= 2:
                    prev = klines[-2].split(',')
                    prev_close = float(prev[2])
                    kline_data['prev_close'] = prev_close
                    kline_data['change'] = kline_data['current'] - prev_close
                    kline_data['change_percent'] = (kline_data['change'] / prev_close * 100) if prev_close else 0
                else:
                    # 使用接口提供的 preKPrice
                    pre_price = data.get('preKPrice', kline_data['open'])
                    kline_data['prev_close'] = pre_price
                    kline_data['change'] = kline_data['current'] - pre_price
                    kline_data['change_percent'] = (kline_data['change'] / pre_price * 100) if pre_price else 0
                
                return kline_data
            
            return None
        
        except Exception as e:
            return None
    
    def get_a_share_indices(self) -> Dict:
        """获取 A 股主要指数"""
        print("📊 获取 A 股指数...")
        
        indices_map = {
            '上证指数': ('1.000001', '000001'),
            '深证成指': ('0.399001', '399001'),
            '创业板指': ('0.399006', '399006'),
            '科创 50': ('1.000688', '000688')
        }
        
        result = {}
        for name, (secid, code) in indices_map.items():
            data = self._get_latest_kline(secid)
            
            if data:
                result[name] = {
                    'current': data['current'],
                    'change': data['change'],
                    'change_percent': data['change_percent']
                }
                sign = '+' if data['change_percent'] > 0 else ''
                print(f"  ✓ {name}: {data['current']:.2f} ({sign}{data['change_percent']:.2f}%) [{data['date']}]")
            else:
                result[name] = None
                print(f"  ✗ {name}: 无数据")
        
        return result
    
    def get_a_share_stocks(self, symbols: List[str]) -> Dict:
        """获取 A 股个股表现"""
        print("\n📈 获取 A 股个股...")
        
        result = {}
        for symbol in symbols:
            code = symbol[:6]
            
            # 确定市场代码
            if code.startswith('6') or code.startswith('5'):
                secid = f'1.{code}'  # 上交所
            elif code.startswith(('0', '3')):
                secid = f'0.{code}'  # 深交所
            elif code.startswith(('8', '4')):
                secid = f'0.{code}'  # 北交所
            else:
                secid = f'1.{code}'
            
            data = self._get_latest_kline(secid)
            
            if data:
                result[code] = {
                    'name': data['name'],
                    'current': data['current'],
                    'change': data['change'],
                    'change_percent': data['change_percent'],
                    'open': data.get('open', 0),
                    'high': data.get('high', 0),
                    'low': data.get('low', 0),
                    'prev_close': data.get('prev_close', 0),
                    'date': data['date']
                }
                sign = '+' if data['change_percent'] > 0 else ''
                print(f"  ✓ {code} {data['name']}: {data['current']:.2f} ({sign}{data['change_percent']:.2f}%) [{data['date']}]")
            else:
                result[code] = None
                print(f"  ✗ {code}: 无数据")
        
        return result
    
    def get_hk_stocks(self, symbols: List[str]) -> Dict:
        """获取港股实时行情"""
        print("\n📈 获取港股个股...")
        
        result = {}
        for symbol in symbols:
            code = symbol.replace('hk', '')[:5].zfill(5)
            secid = f'116.{code}'  # 港股市场代码
            
            data = self._get_latest_kline(secid)
            
            if data:
                result[code] = {
                    'name': data['name'],
                    'current': data['current'],
                    'change': data['change'],
                    'change_percent': data['change_percent'],
                    'date': data['date']
                }
                sign = '+' if data['change_percent'] > 0 else ''
                print(f"  ✓ {code} {data['name']}: {data['current']:.2f} ({sign}{data['change_percent']:.2f}%) [{data['date']}]")
            else:
                result[code] = None
                print(f"  ✗ {code}: 无数据")
        
        return result


def get_a_share_indices(client: CNMarketClient) -> Dict:
    return client.get_a_share_indices()


def get_a_share_stocks(client: CNMarketClient, symbols: List[str]) -> Dict:
    return client.get_a_share_stocks(symbols)


def get_hk_stocks(client: CNMarketClient, symbols: List[str]) -> Dict:
    return client.get_hk_stocks(symbols)


if __name__ == "__main__":
    client = CNMarketClient()
    
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 测试 A 股指数
    a_indices = get_a_share_indices(client)
    
    # 测试 A 股个股
    a_stocks = ['600519', '000858', '300750', '002594', '601318']
    a_performance = get_a_share_stocks(client, a_stocks)
    
    # 测试港股
    hk_stocks = ['00700', '09988', '03690', '01810', '02318']
    hk_performance = get_hk_stocks(client, hk_stocks)
    
    print(f"\n✅ 测试完成")
