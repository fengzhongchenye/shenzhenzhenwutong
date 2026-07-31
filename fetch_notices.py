import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 失败的网站使用代理
USE_PROXY = True

def fetch_url(url, use_proxy=False):
    """获取网页，可选择使用代理"""
    # 直接请求
    if not use_proxy:
        try:
            resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            if resp.status_code == 200:
                return resp
        except:
            pass

    # 使用 allorigins 代理（免费、稳定）
    proxy_url = f"https://api.allorigins.win/raw?url={url}"
    resp = requests.get(proxy_url, headers={**headers, "Host": None}, timeout=30)
    return resp


sources = [
    # ===== 市级（正常网站）=====
    {"name": "深圳市工业和信息化局", "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/", "type": "normal", "proxy": False},
    {"name": "深圳市科技创新局", "url": "http://stic.sz.gov.cn/xxgk/tzgg/", "type": "normal", "proxy": False},
    # ===== 龙岗区（正常网站）=====
    {"name": "龙岗区科技创新局", "url": "http://www.lg.gov.cn/bmzz/kjj/xxgk/qt/tzgg/", "type": "normal", "proxy": False},
    {"name": "龙岗区工业和信息化局", "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/", "type": "normal", "proxy": False},
    # ===== 龙华区（正常网站）=====
    {"name": "龙华区工业和信息化局", "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/", "type": "normal", "proxy": False},
    {"name": "龙华区科技创新局", "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/", "type": "normal", "proxy": False},
    # ===== 以下网站使用代理 =====
    {"name": "深圳市中小企业服务局", "url": "https://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html", "type": "normal", "proxy": True},
    {"name": "福田区工业和信息化局", "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/", "type": "normal", "proxy": True},
    {"name": "福田区科技创新局", "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html", "type": "normal", "proxy": True},
    {"name": "罗湖区科技和工业信息化局", "url": "https://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "坪山区科技创新局", "url": "https://www.szpsq.gov.cn/pskjcxfws/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "坪山区工业和信息化局", "url": "https://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "光明区科技创新局", "url": "https://www.szgm.gov.cn/gmkjcxj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "光明区工业和信息化局", "url": "https://www.szgm.gov.cn/gmjjfw/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "大鹏新区科技和工业信息化局", "url": "https://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "宝安区科技创新局", "url": "https://www.baoan.gov.cn/bakj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "宝安区工业和信息化局", "url": "https://www.baoan.gov.cn/bajjcj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "南山区科技创新局", "url": "https://www.szns.gov.cn/nsqkcj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "南山区工业和信息化局", "url": "https://www.szns.gov.cn/nsqjjcjj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "盐田区科技创新局", "url": "https://www.yantian.gov.cn/ytkcj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
    {"name": "盐田区工业和信息化局", "url": "https://www.yantian.gov.cn/ytgyhxxhj/gkmlpt/index", "type": "gkmlpt", "proxy": True},
]

TITLE_BLACKLIST = [
    "Language", "FRANÇAIS", "العربية", "首页", "下一页", "上一页",
    "无障碍", "长者助手", "繁体", "English", "日本語", "한국어",
    "网站地图", "关于我们", "联系我们", "法律声明", "无障碍浏览",
]

def is_valid_title(title):
    if len(title) < 5:
        return False
    for bad in TITLE_BLACKLIST:
        if bad.lower() in title.lower():
            return False
    return True

def extract_date(text):
    patterns = [
        r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return None

all_notices = []

for src in sources:
    print(f"正在抓取: {src['name']} {'(代理)' if src['proxy'] else ''}...")
    try:
        resp = fetch_url(src["url"], use_proxy=src["proxy"])
        if not resp or resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code if resp else 'error'}")
            continue
        
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        
        if src["type"] == "normal":
            selectors = ["ul.list-main li a", "ul li a", ".list-content li a", ".news-list li a", "ul.list li a"]
            for sel in selectors:
                candidates = soup.select(sel)
                valid = [a for a in candidates if is_valid_title(a.get_text(strip=True))]
                if valid:
                    items = valid
                    print(f"  选择器 '{sel}' -> {len(items)} 条")
                    break
            
            if not items:
                all_a = soup.find_all("a", href=True)
                items = [a for a in all_a if ("/content/post_" in a.get("href","") or "/tzgg/" in a.get("href","")) and is_valid_title(a.get_text(strip=True))]
                if items:
                    print(f"  通用匹配 -> {len(items)} 条")
        
        else:  # gkmlpt
            items = soup.find_all("a", class_="document-number")
            if not items:
                items = soup.select("a[href*='content/post_']")
            items = [a for a in items if is_valid_title(a.get_text(strip=True))]
            print(f"  gkmlpt 匹配 -> {len(items)} 条")
        
        for a_tag in items[:30]:
            try:
                title = re.sub(r'^[\d\.\、\s]+', '', a_tag.get_text(strip=True))
                link = a_tag.get("href", "")
                if not title or not link:
                    continue
                
                # 补全链接
                if link.startswith("//"):
                    link = "https:" + link
                elif link.startswith("/"):
                    base = re.match(r"(https?://[^/]+)", src["url"])
                    if base:
                        link = base.group(1) + link
                elif not link.startswith("http"):
                    link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                
                pub_date = extract_date(str(a_tag.parent)) or extract_date(title) or datetime.now().strftime("%Y-%m-%d")
                
                all_notices.append({
                    "source": src["name"],
                    "title": title,
                    "link": link,
                    "date": pub_date,
                })
                print(f"  ✅ {title[:50]}... {pub_date}")
            except:
                continue
    except Exception as e:
        print(f"  ❌ {str(e)[:100]}")

# 去重
seen = set()
unique = [n for n in all_notices if n["link"] not in seen and not seen.add(n["link"])]
unique.sort(key=lambda x: x["date"], reverse=True)

with open("notices.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"\n✅ 共 {len(unique)} 条")
from collections import Counter
for name, count in Counter(n["source"] for n in unique).most_common():
    print(f"  {name}: {count} 条")
