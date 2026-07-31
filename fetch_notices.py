import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.sz.gov.cn/",
}

def fetch_url(url, as_json=False):
    """获取网页或JSON数据"""
    try:
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code == 200:
            if as_json:
                return resp.json()
            return resp
    except:
        pass
    
    # 如果是 https 失败，尝试 http
    if url.startswith("https://"):
        try:
            http_url = url.replace("https://", "http://", 1)
            resp = requests.get(http_url, headers=headers, timeout=30, allow_redirects=True)
            if resp.status_code == 200:
                if as_json:
                    return resp.json()
                return resp
        except:
            pass
    
    return None


# 网站配置
sources = [
    # ===== 正常列表页网站 =====
    {"name": "深圳市工业和信息化局", "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/", "type": "normal"},
    {"name": "深圳市科技创新局", "url": "http://stic.sz.gov.cn/xxgk/tzgg/", "type": "normal"},
    {"name": "龙岗区科技创新局", "url": "http://www.lg.gov.cn/bmzz/kjj/xxgk/qt/tzgg/", "type": "normal"},
    {"name": "龙岗区工业和信息化局", "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/", "type": "normal"},
    {"name": "龙华区工业和信息化局", "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/", "type": "normal"},
    {"name": "龙华区科技创新局", "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/", "type": "normal"},
    {"name": "福田区工业和信息化局", "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/", "type": "normal"},
    {"name": "福田区科技创新局", "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html", "type": "normal"},
    {"name": "深圳市中小企业服务局", "url": "http://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html", "type": "normal"},
    
    # ===== 政府信息公开平台（使用JSON接口）=====
    # 格式：https://www.xxx.gov.cn/xxx/gkmlpt/api/xxx/infoList?page=1&rows=20
    {"name": "罗湖区科技和工业信息化局", "url": "https://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt", "type": "gkmlpt"},
    {"name": "坪山区科技创新局", "url": "https://www.szpsq.gov.cn/pskjcxfws/gkmlpt", "type": "gkmlpt"},
    {"name": "坪山区工业和信息化局", "url": "https://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt", "type": "gkmlpt"},
    {"name": "光明区科技创新局", "url": "https://www.szgm.gov.cn/gmkjcxj/gkmlpt", "type": "gkmlpt"},
    {"name": "光明区工业和信息化局", "url": "https://www.szgm.gov.cn/gmjjfw/gkmlpt", "type": "gkmlpt"},
    {"name": "大鹏新区科技和工业信息化局", "url": "https://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt", "type": "gkmlpt"},
    {"name": "宝安区科技创新局", "url": "https://www.baoan.gov.cn/bakj/gkmlpt", "type": "gkmlpt"},
    {"name": "宝安区工业和信息化局", "url": "https://www.baoan.gov.cn/bajjcj/gkmlpt", "type": "gkmlpt"},
    {"name": "南山区科技创新局", "url": "https://www.szns.gov.cn/nsqkcj/gkmlpt", "type": "gkmlpt"},
    {"name": "南山区工业和信息化局", "url": "https://www.szns.gov.cn/nsqjjcjj/gkmlpt", "type": "gkmlpt"},
    {"name": "盐田区科技创新局", "url": "https://www.yantian.gov.cn/ytkcj/gkmlpt", "type": "gkmlpt"},
    {"name": "盐田区工业和信息化局", "url": "https://www.yantian.gov.cn/ytgyhxxhj/gkmlpt", "type": "gkmlpt"},
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
    print(f"正在抓取: {src['name']}...")
    try:
        if src["type"] == "normal":
            # 正常网页抓取
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
        
        else:  # gkmlpt 类型 - 使用JSON接口
            # 构建JSON接口URL
            # 从 gkmlpt URL 中提取信息ID，尝试多种接口格式
            base_url = src["url"].rstrip("/")
            
            # 尝试多个接口格式
            api_urls = []
            
            # 从URL中提取可能的catalogId
            # 例如 https://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt
            # 尝试各种可能的API路径
            path_parts = base_url.split("/")
            if len(path_parts) >= 2:
                catalog = path_parts[-1] if path_parts[-1] != "gkmlpt" else path_parts[-2]
                
                # 尝试多种接口格式
                domain = "/".join(path_parts[:3])  # https://www.xxx.gov.cn
                
                api_urls = [
                    f"{base_url}/api/{catalog}/infoList?page=1&rows=30",
                    f"{base_url}/api/infoList?page=1&rows=30",
                    f"{domain}/gkmlpt/api/infoList?catalogId={catalog}&page=1&rows=30",
                    f"{domain}/api/gkmlpt/infoList?catalogId={catalog}&page=1&rows=30",
                ]
            
            # 同时也尝试解析HTML页面，看是否有初始数据
            resp = fetch_url(base_url + "/index")
            if not resp:
                resp = fetch_url(base_url + "/index.html")
            if not resp:
                resp = fetch_url(base_url)
            
            items = []
            
            # 先尝试从HTML中提取
            if resp and resp.status_code == 200:
                resp.encoding = "utf-8"
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 查找 document-number 类的链接
                doc_links = soup.find_all("a", class_="document-number")
                if not doc_links:
                    doc_links = soup.select("a[href*='content/post_']")
                
                if doc_links:
                    items = [a for a in doc_links if is_valid_title(a.get_text(strip=True))]
                    print(f"  HTML匹配 -> {len(items)} 条")
            
            # 如果HTML没有，尝试JSON接口
            if not items:
                for api_url in api_urls:
                    try:
                        data = fetch_url(api_url, as_json=True)
                        if data:
                            rows = data.get("rows") or data.get("data") or data.get("list") or []
                            if isinstance(rows, list) and len(rows) > 0:
                                print(f"  JSON接口成功 -> {len(rows)} 条")
                                for row in rows[:30]:
                                    try:
                                        title = row.get("title") or row.get("articleTitle") or row.get("infoTitle", "")
                                        link = row.get("url") or row.get("articleUrl") or row.get("infoUrl", "")
                                        pub_date_str = row.get("publishDate") or row.get("createDate") or row.get("pubDate", "")
                                        
                                        if not title or not link:
                                            continue
                                        
                                        # 清理标题
                                        title = re.sub(r'<[^>]+>', '', title)
                                        title = re.sub(r'^[\d\.\、\s]+', '', title)
                                        
                                        # 补全链接
                                        if link.startswith("./"):
                                            link = base_url + link[1:]
                                        elif link.startswith("/"):
                                            domain = "/".join(base_url.split("/")[:3])
                                            link = domain + link
                                        elif not link.startswith("http"):
                                            link = base_url + "/" + link
                                        
                                        # 提取日期
                                        pub_date = extract_date(pub_date_str)
                                        if not pub_date:
                                            pub_date = datetime.now().strftime("%Y-%m-%d")
                                        
                                        all_notices.append({
                                            "source": src["name"],
                                            "title": title,
                                            "link": link,
                                            "date": pub_date,
                                        })
                                        print(f"  ✅ {title[:50]}... {pub_date}")
                                    except:
                                        continue
                                break
                    except:
                        continue
            
            # 处理HTML提取到的items
            if items:
                for a_tag in items[:30]:
                    try:
                        title = re.sub(r'^[\d\.\、\s]+', '', a_tag.get_text(strip=True))
                        link = a_tag.get("href", "")
                        if not title or not link:
                            continue
                        
                        if link.startswith("//"):
                            link = "https:" + link
                        elif link.startswith("/"):
                            domain = "/".join(base_url.split("/")[:3])
                            link = domain + link
                        elif not link.startswith("http"):
                            link = base_url + "/" + link
                        
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
