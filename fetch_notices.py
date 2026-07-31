import requests
from bs4 import BeautifulSoup
import json
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

sources = [
    # ===== 市级 =====
    {
        "name": "深圳市工业和信息化局",
        "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li, .news-list li",
    },
    {
        "name": "深圳市科技创新局",
        "url": "http://stic.sz.gov.cn/xxgk/tzgg/",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li",
    },
    {
        "name": "深圳市中小企业服务局",
        "url": "https://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li",
    },
    # ===== 福田区 =====
    {
        "name": "福田区工业和信息化局",
        "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/",
        "type": "normal",
        "list_selector": "ul.list li, ul li, .list-content li",
    },
    {
        "name": "福田区科技创新局",
        "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html",
        "type": "normal",
        "list_selector": "ul.list li, ul li, .list-content li",
    },
    # ===== 罗湖区 =====
    {
        "name": "罗湖区科技和工业信息化局",
        "url": "https://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt/index",
        "type": "gkmlpt",
    },
    # ===== 龙岗区 =====
    {
        "name": "龙岗区科技创新局",
        "url": "http://www.lg.gov.cn/bmzz/kjj/xxgk/qt/tzgg/",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li",
    },
    {
        "name": "龙岗区工业和信息化局",
        "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li",
    },
    # ===== 龙华区 =====
    {
        "name": "龙华区工业和信息化局",
        "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li",
    },
    {
        "name": "龙华区科技创新局",
        "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/",
        "type": "normal",
        "list_selector": "ul.list-main li, ul li, .list-content li",
    },
    # ===== 坪山区 =====
    {
        "name": "坪山区科技创新局",
        "url": "https://www.szpsq.gov.cn/pskjcxfws/gkmlpt/index",
        "type": "gkmlpt",
    },
    {
        "name": "坪山区工业和信息化局",
        "url": "https://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt/index",
        "type": "gkmlpt",
    },
    # ===== 光明区 =====
    {
        "name": "光明区科技创新局",
        "url": "https://www.szgm.gov.cn/gmkjcxj/gkmlpt/index",
        "type": "gkmlpt",
    },
    {
        "name": "光明区工业和信息化局",
        "url": "https://www.szgm.gov.cn/gmjjfw/gkmlpt/index",
        "type": "gkmlpt",
    },
    # ===== 大鹏新区 =====
    {
        "name": "大鹏新区科技和工业信息化局",
        "url": "https://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt/index",
        "type": "gkmlpt",
    },
    # ===== 宝安区 =====
    {
        "name": "宝安区科技创新局",
        "url": "https://www.baoan.gov.cn/bakj/gkmlpt/index",
        "type": "gkmlpt",
    },
    {
        "name": "宝安区工业和信息化局",
        "url": "https://www.baoan.gov.cn/bajjcj/gkmlpt/index",
        "type": "gkmlpt",
    },
    # ===== 南山区 =====
    {
        "name": "南山区科技创新局",
        "url": "https://www.szns.gov.cn/nsqkcj/gkmlpt/index",
        "type": "gkmlpt",
    },
    {
        "name": "南山区工业和信息化局",
        "url": "https://www.szns.gov.cn/nsqjjcjj/gkmlpt/index",
        "type": "gkmlpt",
    },
    # ===== 盐田区 =====
    {
        "name": "盐田区科技创新局",
        "url": "https://www.yantian.gov.cn/ytkcj/gkmlpt/index",
        "type": "gkmlpt",
    },
    {
        "name": "盐田区工业和信息化局",
        "url": "https://www.yantian.gov.cn/ytgyhxxhj/gkmlpt/index",
        "type": "gkmlpt",
    },
]

all_notices = []

for src in sources:
    print(f"正在抓取: {src['name']}...")
    try:
        resp = requests.get(src["url"], headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code}")
            continue
        
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        items = []
        
        if src["type"] == "normal":
            # 常规列表页
            for selector in src["list_selector"].split(", "):
                items = soup.select(selector)
                if len(items) > 0:
                    print(f"  使用选择器 '{selector}' 找到 {len(items)} 项")
                    break
            
            if len(items) == 0:
                # 尝试找所有 a 标签中看起来像公告链接的
                all_links = soup.find_all("a", href=True)
                for a in all_links:
                    href = a.get("href", "")
                    if "/content/post_" in href or "/tzgg/" in href:
                        items.append(a)
                if len(items) > 0:
                    print(f"  使用通用匹配找到 {len(items)} 项")
            
            for item in items[:30]:
                try:
                    # 如果 item 本身就是 a 标签
                    if item.name == "a":
                        a_tag = item
                    else:
                        a_tag = item.find("a")
                    
                    if not a_tag:
                        continue
                    
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get("href", "")
                    
                    if not title or not link or len(title) < 5:
                        continue
                    
                    # 补全链接
                    if link.startswith("/"):
                        base_match = re.match(r"(https?://[^/]+)", src["url"])
                        if base_match:
                            link = base_match.group(1) + link
                    elif not link.startswith("http"):
                        link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                    
                    # 尝试提取日期
                    date_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", str(item))
                    if not date_match:
                        date_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", title)
                    
                    if date_match:
                        pub_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                    else:
                        # 如果找不到日期，用当天日期
                        from datetime import datetime
                        pub_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # 清理标题（去掉前面的序号）
                    title = re.sub(r'^\d+[\.\、\s]+', '', title)
                    
                    all_notices.append({
                        "source": src["name"],
                        "title": title,
                        "link": link,
                        "date": pub_date,
                    })
                    print(f"  ✅ {title[:40]}... {pub_date}")
                    
                except Exception as e:
                    continue
        
        elif src["type"] == "gkmlpt":
            # 政府信息公开平台
            # 查找所有 document-number 类的 a 标签
            doc_links = soup.find_all("a", class_="document-number")
            if len(doc_links) == 0:
                # 尝试其他可能的选择器
                doc_links = soup.select("a[href*='content/post_']")
            
            print(f"  找到 {len(doc_links)} 条记录")
            
            for a_tag in doc_links[:30]:
                try:
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get("href", "")
                    
                    if not title or not link or len(title) < 5:
                        continue
                    
                    # 补全链接（gkmlpt 通常用 // 开头）
                    if link.startswith("//"):
                        link = "https:" + link
                    elif link.startswith("/"):
                        base_match = re.match(r"(https?://[^/]+)", src["url"])
                        if base_match:
                            link = base_match.group(1) + link
                    elif not link.startswith("http"):
                        link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                    
                    # 尝试提取日期（从标题或附近找）
                    date_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", str(a_tag.parent))
                    if not date_match:
                        date_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", title)
                    
                    if date_match:
                        pub_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                    else:
                        from datetime import datetime
                        pub_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # 清理标题
                    title = re.sub(r'^\d+[\.\、\s]+', '', title)
                    
                    all_notices.append({
                        "source": src["name"],
                        "title": title,
                        "link": link,
                        "date": pub_date,
                    })
                    print(f"  ✅ {title[:40]}... {pub_date}")
                    
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"  ❌ 抓取失败: {str(e)[:100]}")

# 去重
seen = set()
unique_notices = []
for n in all_notices:
    if n["link"] not in seen:
        seen.add(n["link"])
        unique_notices.append(n)

# 按日期倒序排列
unique_notices.sort(key=lambda x: x["date"], reverse=True)

# 写入文件
with open("notices.json", "w", encoding="utf-8") as f:
    json.dump(unique_notices, f, ensure_ascii=False, indent=2)

print(f"\n✅ 总共抓取到 {len(unique_notices)} 条公告")
