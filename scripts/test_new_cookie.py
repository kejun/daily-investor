#!/usr/bin/env python3
"""
测试新的 X Cookie 访问
使用 twid + ct0
"""

import os
import requests

def load_env(filepath='.env.cookie'):
    """加载环境变量"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# 加载 Cookie（尝试多个路径）
script_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.path.join(script_dir, '.env.cookie'),
    os.path.join(script_dir, '..', '.env.cookie'),
    '.env.cookie'
]
for path in possible_paths:
    if os.path.exists(path):
        load_env(path)
        break

ct0 = os.getenv('X_CT0')
twid = os.getenv('X_TWID')

if not ct0 or not twid:
    print("❌ Cookie 未设置")
    exit(1)

print("🧪 测试 X Cookie 访问...")
print(f"CT0: {ct0[:30]}...")
print(f"TWID: {twid}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
    'x-csrf-token': ct0,
    'Cookie': f'ct0={ct0}; twid={twid}'
}

# 测试 1: 访问主页
print("\n📱 测试访问主页...")
resp = requests.get('https://x.com/home', headers=headers, timeout=10, allow_redirects=True)
print(f"状态码: {resp.status_code}")
print(f"URL: {resp.url}")

if 'login' in resp.url or resp.status_code == 302:
    print("❌ 需要登录")
else:
    print("✅ 可以访问主页")
    # 检查是否有时间线内容
    if 'Home' in resp.text or 'For you' in resp.text:
        print("✅ 检测到时间线内容")

# 测试 2: GraphQL API 获取用户信息
print("\n📊 测试 GraphQL API...")
url = 'https://x.com/i/api/graphql/G3KGOASz96MR-ucTmZNWyA/UserByScreenName'
params = {
    'variables': '{"screen_name":"chamath","withSafetyModeUserFields":true}',
    'features': '{"hidden_profile_likes_enabled":true}'
}

resp2 = requests.get(url, headers=headers, params=params, timeout=10)
print(f"API 状态码: {resp2.status_code}")
if resp2.status_code == 200:
    data = resp2.json()
    user = data.get('data', {}).get('user', {})
    if user:
        print("✅ 可以获取用户数据")
        name = user.get('result', {}).get('legacy', {}).get('name', 'Unknown')
        print(f"   用户: {name}")
    else:
        print("⚠️ 返回数据为空")
else:
    print(f"❌ API 访问失败: {resp2.text[:200]}")

print("\n" + "="*60)
print("总结:")
print("- twid + ct0 可以用于公开数据访问")
print("- 但可能无法执行发帖等操作（需要 auth_token）")
print("="*60)
