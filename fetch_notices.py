import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

sources = [
    # ===== 静态网站 =====
    {"name": "深圳市工业和信息化局", "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/"},
    {"name": "深圳市科技创新局", "url": "http://stic.sz.gov.cn/xxgk/tzgg/"},
    {"name": "龙岗区科技创新局", "url": "http://www.lg.gov.cn/bmzz/kjj/xxgk/qt/tzgg/"},
    {"name": "龙岗区工业和信息化局", "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/"},
    {"name": "龙华区工业和信息化局", "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/"},
    {"name": "龙华区科技创新局", "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/"},
    {"name": "福田区工业和信息化局", "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/"},
    {"name": "福田区科技创新局", "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html"},
    {"name": "深圳市中小企业服务局", "url": "http://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html"},
    # ===== 动态网站（加 ?page=1）=====
    {"name": "罗湖区科技和工业信息化局", "url": "https://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt/index?page=1"},
    {"name": "坪山区科技创新局", "url": "https://www.szpsq.gov.cn/pskjcxfws/gkmlpt/index?page=1"},
    {"name": "坪山区工业和信息化局", "url": "https://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt/index?page=1"},
    {"name": "光明区科技创新局", "url": "https://www.szgm.gov.cn/gmkjcxj/gkmlpt/index?page=1"},
    {"name": "光明区工业和信息化局", "url": "https://www.szgm.gov.cn/gmjjfw/gkmlpt/index?page=1"},
    {"name": "大鹏新区科技和工业信息化局", "url": "https://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt/index?page=1"},
    {"name": "宝安区科技创新局", "url": "https://www.baoan.gov.cn/bakj/gkmlpt/index?page=1"},
    {"name": "宝安区工业和信息化局", "url": "https://www.baoan.gov.cn/bajjcj/gkmlpt/index?page=1"},
    {"name": "南山区科技创新局", "url": "https://www.szns.gov.cn/nsqkcj/gkmlpt/index?page=1"},
    {"name": "南山区工业和信息化局", "url": "https://www.szns.gov.cn/nsqjjcjj/gkmlpt/index?page=1"},
    {"name": "盐田区科技创新局", "url": "https://www.yantian.gov.cn/ytkcj/gkmlpt/index?page=1"},
    {"name": "盐田区工业和信息化局", "url": "https://www.yantian.gov.cn/ytgyhxxhj/gkmlpt/index?page=1"},
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
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text) or re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return None

def fetch_url(url):
    try:
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            resp.encoding = "utf-8"
            return resp.text
    except:
        pass
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            resp.encoding = "utf-8"
            return resp.text
    except:
        pass
    if url.startswith("https://"):
        try:
            resp = requests.get(url.replace("https://", "http://", 1), headers=headers, timeout=15)
            if resp.status_code == 200:
                resp.encoding = "utf-8"
                return resp.text
        except:
            pass
    return None

all_notices = []

for src in sources:
    print(f"正在抓取: {src['name']}...")
    try:
        html = fetch_url(src["url"])
        if not html:
            print(f"  ❌ 无法访问")
            continue
        
        soup = BeautifulSoup(html, "html.parser")
        items = []
        
        # 先尝试常见选择器
        selectors = ["ul.list-main li a", "ul li a", ".list-content li a", ".news-list li a", "ul.list li a"]
        for sel in selectors:
            candidates = soup.select(sel)
            valid = [a for a in candidates if is_valid_title(a.get_text(strip=True))]
            if valid:
                items = valid
                break
        
        # 如果没找到，找所有 content/post_ 链接
        if not items:
            all_a = soup.find_all("a", href=True)
            items = [a for a in all_a if "/content/post_" in a.get("href","") and is_valid_title(a.get_text(strip=True))]
        
        print(f"  找到 {len(items)} 条")
        
        for a_tag in items[:30]:
            try:
                title = re.sub(r'^[\d\.\、\s]+', '', a_tag.get_text(strip=True))
                link = a_tag.get("href", "")
                if not title or not link:
                    continue
                
                if link.startswith("//"):
                    link = "https:" + link
                elif link.startswith("/"):
                    base = re.match(r"(https?://[^/]+)", src["url"])
                    if base:
                        link = base.group(1) + link
                elif not link.startswith("http"):
                    link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                
                pub_date = extract_date(str(a_tag.parent)) or extract_date(title) or datetime.now().strftime("%Y-%m-%d")
                
                all_notices.append({"source": src["name"], "title": title, "link": link, "date": pub_date})
            except:
                continue
    except Exception as e:
        print(f"  ❌ {str(e)[:80]}")

# 去重排序
seen = set()
unique = [n for n in all_notices if n["link"] not in seen and not seen.add(n["link"])]
unique.sort(key=lambda x: x["date"], reverse=True)

with open("notices.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"\n✅ 总共 {len(unique)} 条")
from collections import Counter
for name, count in Counter(n["source"] for n in unique).most_common():
    print(f"  {name}: {count} 条")
