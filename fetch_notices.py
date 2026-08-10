import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

static_sources = [
    {"name": "深圳市工业和信息化局", "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/"},
    {"name": "深圳市科技创新局", "url": "http://stic.sz.gov.cn/xxgk/tzgg/"},
    {"name": "龙岗区科技创新局", "url": "http://www.lg.gov.cn/bmzz/kjj/xxgk/qt/tzgg/"},
    {"name": "龙岗区工业和信息化局", "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/"},
    {"name": "龙华区工业和信息化局", "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/"},
    {"name": "龙华区科技创新局", "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/"},
    {"name": "福田区工业和信息化局", "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/"},
    {"name": "福田区科技创新局", "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html"},
    {"name": "深圳市中小企业服务局", "url": "http://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html"},
]

api_sources = [
    {"name": "罗湖区科技和工业信息化局", "api": "http://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "坪山区科技创新局", "api": "http://www.szpsq.gov.cn/pskjcxfws/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "坪山区工业和信息化局", "api": "http://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "光明区科技创新局", "api": "http://www.szgm.gov.cn/gmkjcxj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "光明区工业和信息化局", "api": "http://www.szgm.gov.cn/gmjjfw/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "大鹏新区科技和工业信息化局", "api": "http://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "宝安区科技创新局", "api": "http://www.baoan.gov.cn/bakj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "宝安区工业和信息化局", "api": "http://www.baoan.gov.cn/bajjcj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "南山区科技创新局", "api": "http://www.szns.gov.cn/nsqkcj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "南山区工业和信息化局", "api": "http://www.szns.gov.cn/nsqjjcjj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "盐田区科技创新局", "api": "http://www.yantian.gov.cn/ytkcj/gkmlpt/api/all/0?page=1&sid=755325"},
    {"name": "盐田区工业和信息化局", "api": "http://www.yantian.gov.cn/ytgyhxxhj/gkmlpt/api/all/0?page=1&sid=755325"},
]

TITLE_BLACKLIST = [
    "Language", "FRANÇAIS", "首页", "下一页", "上一页",
    "无障碍", "长者助手", "网站地图", "关于我们", "跳转", "收藏",
    "政务公开", "政务服务", "政民互动", "政府信息公开",
    "法定主动公开", "机构职能", "规划计划", "财政审计",
    "招标采购", "建议提案", "监督渠道", "信息公开年报",
    "政策", "政府信息公开指南", "政府信息公开制度",
    "栏目更新情况说明", "职责", "主办单位",
    "English", "Special", "日本語", "한국어", "Francais",
    "Arabic", "Portugues", "Español",
]

def is_valid_title(title):
    if len(title) < 5:
        return False
    for bad in TITLE_BLACKLIST:
        if bad.lower() in title.lower():
            return False
    return True

def is_valid_link(link):
    bad_patterns = ["/english/", "/Special/", "/welcome/", "/ALB/", "/FR/", "/JP/", "/KR/"]
    for pattern in bad_patterns:
        if pattern.lower() in link.lower():
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

print("=" * 50)
print("静态网站")
print("=" * 50)

for src in static_sources:
    print(f"\n{src['name']}...")
    try:
        html = fetch_url(src["url"])
        if not html:
            print(f"  [失败] 无法访问")
            continue
        
        soup = BeautifulSoup(html, "html.parser")
        items = []
        
        selectors = ["ul.list-main li a", "ul li a", ".list-content li a", ".news-list li a", "ul.list li a"]
        for sel in selectors:
            candidates = soup.select(sel)
            valid = [a for a in candidates if is_valid_title(a.get_text(strip=True))]
            if valid:
                items = valid
                break
        
        if not items:
            all_a = soup.find_all("a", href=True)
            items = [a for a in all_a if "/content/post_" in a.get("href","") and is_valid_title(a.get_text(strip=True))]
        
        print(f"  {len(items)} 条")
        
        for a_tag in items[:30]:
            try:
                title = re.sub(r'^[\d\.\、\s]+', '', a_tag.get_text(strip=True))
                link = a_tag.get("href", "")
                if not title or not link or not is_valid_link(link):
                    continue
                
                if link.startswith("//"):
                    link = "https:" + link
                elif link.startswith("/"):
                    base = re.match(r"(https?://[^/]+)", src["url"])
                    if base:
                        link = base.group(1) + link
                
                pub_date = extract_date(str(a_tag.parent)) or extract_date(title) or datetime.now().strftime("%Y-%m-%d")
                
                all_notices.append({"source": src["name"], "title": title, "link": link, "date": pub_date})
            except:
                continue
    except Exception as e:
        print(f"  [失败] {str(e)[:80]}")

print("\n" + "=" * 50)
print("API 网站")
print("=" * 50)

api_headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

for src in api_sources:
    print(f"\n{src['name']}...")
    try:
        resp = requests.get(src["api"], headers=api_headers, timeout=15)
        if resp.status_code != 200:
            print(f"  [失败] HTTP {resp.status_code}")
            continue
        
        data = resp.json()
        articles = data.get("articles", [])
        
        print(f"  {len(articles)} 条")
        
        for item in articles[:30]:
            title = item.get("title", "")
            link_id = item.get("id", "")
            
            if not title or not link_id:
                continue
            
            if not is_valid_title(title):
                continue
            
            base = src["api"].split("/gkmlpt")[0]
            link = f"{base}/gkmlpt/content/12/{str(link_id)[:5]}/post_{link_id}.html"
            
            if not is_valid_link(link):
                continue
            
            all_notices.append({
                "source": src["name"],
                "title": title.strip(),
                "link": link,
                "date": datetime.now().strftime("%Y-%m-%d"),
            })
    except Exception as e:
        print(f"  [失败] {str(e)[:80]}")

seen = set()
unique = [n for n in all_notices if n["link"] not in seen and not seen.add(n["link"])]
unique.sort(key=lambda x: x["date"], reverse=True)

with open("notices.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"\n总共 {len(unique)} 条")
from collections import Counter
for name, count in Counter(n["source"] for n in unique).most_common():
    print(f"  {name}: {count} 条")
