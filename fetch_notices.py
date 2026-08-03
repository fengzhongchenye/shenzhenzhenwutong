import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ===== 静态网站 =====
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

# ===== 动态网站 =====
dynamic_sources = [
    {"name": "罗湖区科技和工业信息化局", "url": "http://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt/index"},
    {"name": "坪山区科技创新局", "url": "http://www.szpsq.gov.cn/pskjcxfws/gkmlpt/index"},
    {"name": "坪山区工业和信息化局", "url": "http://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt/index"},
    {"name": "光明区科技创新局", "url": "http://www.szgm.gov.cn/gmkjcxj/gkmlpt/index"},
    {"name": "光明区工业和信息化局", "url": "http://www.szgm.gov.cn/gmjjfw/gkmlpt/index"},
    {"name": "大鹏新区科技和工业信息化局", "url": "http://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt/index"},
    {"name": "宝安区科技创新局", "url": "http://www.baoan.gov.cn/bakj/gkmlpt/index"},
    {"name": "宝安区工业和信息化局", "url": "http://www.baoan.gov.cn/bajjcj/gkmlpt/index"},
    {"name": "南山区科技创新局", "url": "http://www.szns.gov.cn/nsqkcj/gkmlpt/index"},
    {"name": "南山区工业和信息化局", "url": "http://www.szns.gov.cn/nsqjjcjj/gkmlpt/index"},
    {"name": "盐田区科技创新局", "url": "http://www.yantian.gov.cn/ytkcj/gkmlpt/index"},
    {"name": "盐田区工业和信息化局", "url": "http://www.yantian.gov.cn/ytgyhxxhj/gkmlpt/index"},
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

def fetch_url(url):
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            return resp
    except:
        pass
    
    if url.startswith("https://"):
        try:
            http_url = url.replace("https://", "http://", 1)
            resp = requests.get(http_url, headers=headers, timeout=15, allow_redirects=True)
            if resp.status_code == 200:
                return resp
        except:
            pass
    return None

all_notices = []

# ========== 第一部分：静态网站 ==========
print("=" * 50)
print("第一部分：抓取静态网站（requests）")
print("=" * 50)

for src in static_sources:
    print(f"\n正在抓取: {src['name']}...")
    try:
        resp = fetch_url(src["url"])
        if not resp or resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code if resp else 'error'}")
            continue
        
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        
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
                
                all_notices.append({
                    "source": src["name"],
                    "title": title,
                    "link": link,
                    "date": pub_date,
                })
                print(f"  ✅ {title[:50]}... {pub_date}")
            except:
                continue
        
        if not items:
            print(f"  ❌ 未提取到公告")
            
    except Exception as e:
        print(f"  ❌ {str(e)[:100]}")

# ========== 第二部分：动态网站 ==========
print("\n" + "=" * 50)
print("第二部分：抓取动态网站（Playwright）")
print("=" * 50)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--dns-prefetch-disable",
            "--host-resolver-rules=MAP * 114.114.114.114",  # 使用国内DNS
        ]
    )
    
    for src in dynamic_sources:
        print(f"\n正在抓取: {src['name']} ({src['url']})...")
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_https_errors=True,
            )
            page = context.new_page()
            
            # 增加超时时间，先尝试 http
            try:
                page.goto(src["url"], timeout=60000, wait_until="networkidle")
            except Exception as e1:
                print(f"  首次访问失败: {str(e1)[:80]}")
                # 尝试 https
                if src["url"].startswith("http://"):
                    try:
                        https_url = src["url"].replace("http://", "https://", 1)
                        print(f"  尝试 https: {https_url}")
                        page.goto(https_url, timeout=60000, wait_until="networkidle")
                    except Exception as e2:
                        print(f"  ❌ 最终无法访问: {str(e2)[:80]}")
                        context.close()
                        continue
                else:
                    context.close()
                    continue
            
            # 等待动态内容加载
            page.wait_for_timeout(8000)
            
            # 获取所有链接
            links = page.query_selector_all("a")
            print(f"  页面共有 {len(links)} 个链接")
            count = 0
            for a_tag in links[:50]:
                try:
                    title = a_tag.inner_text().strip()
                    href = a_tag.get_attribute("href") or ""
                    
                    if not is_valid_title(title) or not href:
                        continue
                    
                    if "/content/post_" not in href and "/tzgg/" not in href:
                        continue
                    
                    if href.startswith("//"):
                        href = "https:" + href
                    elif href.startswith("/"):
                        domain = src["url"].split("/")[0] + "//" + src["url"].split("/")[2]
                        href = domain + href
                    
                    parent_text = a_tag.evaluate("el => el.parentElement?.innerText || ''")
                    pub_date = extract_date(parent_text) or extract_date(title) or datetime.now().strftime("%Y-%m-%d")
                    
                    all_notices.append({
                        "source": src["name"],
                        "title": re.sub(r'^[\d\.\、\s]+', '', title),
                        "link": href,
                        "date": pub_date,
                    })
                    count += 1
                except:
                    continue
            
            print(f"  ✅ 抓到 {count} 条")
            context.close()
            
        except Exception as e:
            print(f"  ❌ {str(e)[:150]}")
    
    browser.close()

# ========== 去重和排序 ==========
seen = set()
unique = [n for n in all_notices if n["link"] not in seen and not seen.add(n["link"])]
unique.sort(key=lambda x: x["date"], reverse=True)

with open("notices.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"\n{'=' * 50}")
print(f"✅ 总共 {len(unique)} 条公告")
print(f"{'=' * 50}")
from collections import Counter
for name, count in Counter(n["source"] for n in unique).most_common():
    print(f"  {name}: {count} 条")
