#!/usr/bin/env python3
"""
改进版 Nitter RSS 客户端
多实例轮换 + 智能重试 + 备用方案
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import time
import random

class NitterRSSClient:
    """改进版 Nitter RSS 客户端"""
    
    # Nitter 实例列表（按可靠性排序）
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.d420.de",
        "https://nitter.space",
        "https://nitter.cz",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.working_instance = None
    
    def _test_instance(self, instance):
        """测试实例是否可用"""
        try:
            # 用 Elon Musk 测试
            url = f"{instance}/elonmusk/rss"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _find_working_instance(self):
        """找到可用的实例"""
        if self.working_instance and self._test_instance(self.working_instance):
            return self.working_instance
        
        # 随机打乱，避免总是用同一个
        instances = self.NITTER_INSTANCES.copy()
        random.shuffle(instances)
        
        for instance in instances:
            if self._test_instance(instance):
                self.working_instance = instance
                print(f"  ✅ 使用实例: {instance}")
                return instance
        
        return None
    
    def get_user_feed(self, username, max_items=5, retries=3):
        """
        获取用户 RSS Feed（带重试）
        
        Args:
            username: Twitter 用户名
            max_items: 获取数量
            retries: 重试次数
        """
        # 找到可用实例
        instance = self._find_working_instance()
        if not instance:
            print(f"  ❌ 所有 Nitter 实例都不可用")
            return []
        
        for attempt in range(retries):
            try:
                url = f"{instance}/{username}/rss"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return self._parse_rss(response.text, max_items)
                elif response.status_code == 404:
                    # 用户不存在或实例问题，尝试其他实例
                    instance = self._find_working_instance()
                    if not instance:
                        break
                else:
                    print(f"  ⚠️ 状态码 {response.status_code}，重试...")
                    
            except Exception as e:
                print(f"  ⚠️ 第 {attempt + 1} 次尝试失败: {e}")
                time.sleep(1)
        
        return []
    
    def _parse_rss(self, xml_content, max_items):
        """解析 RSS XML（增强版）"""
        try:
            root = ET.fromstring(xml_content)
            items = []
            
            # RSS 2.0 格式
            for item in root.findall('.//item')[:max_items]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                
                # 清理 HTML
                text = self._clean_html(description.text) if description is not None else ""
                
                # 解析时间
                pub_time = self._parse_time(pub_date.text) if pub_date is not None else ""
                
                items.append({
                    'title': title.text if title is not None else "",
                    'link': link.text if link is not None else "",
                    'published': pub_time,
                    'text': text
                })
            
            return items
            
        except ET.ParseError as e:
            # 尝试修复常见 XML 错误
            print(f"  ⚠️ XML 解析失败，尝试修复...")
            try:
                # 移除非法字符后重试
                cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', xml_content)
                root = ET.fromstring(cleaned)
                # ... 简化处理
                return []
            except:
                return []
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            return []
    
    def _clean_html(self, html):
        """清理 HTML 标签"""
        if not html:
            return ""
        # 移除 HTML 标签
        clean = re.sub('<.*?>', ' ', html)
        # 解码 HTML 实体
        clean = clean.replace('&quot;', '"').replace('&amp;', '&')
        clean = clean.replace('&lt;', '<').replace('&gt;', '>')
        clean = clean.replace('&#39;', "'").replace('&nbsp;', ' ')
        # 合并多余空格
        clean = ' '.join(clean.split())
        return clean.strip()
    
    def _parse_time(self, time_str):
        """解析时间字符串"""
        if not time_str:
            return ""
        try:
            # 简化显示
            return time_str[:20] if len(time_str) > 20 else time_str
        except:
            return time_str

def fetch_kol_insights(category=None, max_items=3, include_raw=False):
    """
    获取 KOL 观点（改进版）
    
    Args:
        category: 分类名称，None 表示全部
        max_items: 每个 KOL 获取的推文数量
        include_raw: 是否包含原始数据
    """
    
    # KOL 清单（更新版）
    KOL_LIST = {
        "美股宏观/科技": [
            "chamath",      # Social Capital 创始人
            "RayDalio",     # 桥水基金
            "jimcramer",    # CNBC
            "elonmusk",     # Tesla/SpaceX（备选）
        ],
        "中概/港股": [
            "HaoHongCFA",   # 洪灏
            "maoxian",      # 美股交易员
            "realDawningW", # 中概深度
        ],
        "技术分析": [
            "traderstewie",
            "markminervini",
            "sentimentrader",
        ],
        "宏观研究": [
            "biancoresearch",
            "downtownjbrown",
        ],
        "价值投资": [
            "peterlynchquotes",
            "howardmarksbook",
            "mohnishpabrai",
        ]
    }
    
    client = NitterRSSClient()
    results = {}
    
    categories = [category] if category else KOL_LIST.keys()
    
    for cat in categories:
        results[cat] = []
        print(f"\n📊 获取 {cat} 的观点...")
        
        for username in KOL_LIST[cat]:
            try:
                tweets = client.get_user_feed(username, max_items)
                
                if tweets:
                    results[cat].append({
                        'username': username,
                        'tweets': tweets
                    })
                    # 显示预览
                    preview = tweets[0]['text'][:60] + '...' if len(tweets[0]['text']) > 60 else tweets[0]['text']
                    print(f"  ✅ @{username}: {len(tweets)} 条 | {preview}")
                else:
                    print(f"  ⚠️ @{username}: 无数据")
                
                # 延迟避免被封
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"  ❌ @{username}: {str(e)[:50]}")
    
    return results

def format_for_report(results, max_per_category=2):
    """格式化为投资洞察报告"""
    insights = []
    
    for category, users in results.items():
        count = 0
        for user in users:
            if count >= max_per_category:
                break
            
            if user['tweets']:
                tweet = user['tweets'][0]  # 最新一条
                text = tweet['text'].replace('\n', ' ')
                
                # 过滤太短或太长的
                if len(text) < 20:
                    continue
                if len(text) > 120:
                    text = text[:120] + '...'
                
                insights.append({
                    'investor': f"@{user['username']}",
                    'view': text,
                    'category': category.split('/')[0]
                })
                count += 1
    
    return insights

def generate_daily_report():
    """生成每日完整报告"""
    print("=" * 70)
    print(f"📈 X KOL 投资观点日报 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    results = fetch_kol_insights(max_items=2)
    insights = format_for_report(results)
    
    print("\n" + "=" * 70)
    print("📋 格式化输出（用于投资洞察报告）")
    print("=" * 70)
    
    for item in insights:
        print(f"\n{item['investor']} ({item['category']}):")
        print(f"  \"{item['view']}\"")
    
    return insights

if __name__ == "__main__":
    # 运行日报生成
    generate_daily_report()
