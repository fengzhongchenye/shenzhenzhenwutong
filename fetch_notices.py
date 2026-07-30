import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

# 模拟真实浏览器的请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 所有需要抓取的单位
sources = [
    {
        "name": "深圳市工业和信息化局",
        "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/tzgg/",
        "list_selector": "ul.list-main li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "深圳市科技创新局",
        "url": "http://stic.sz.gov.cn/xxgk/tzgg/",
        "list_selector": "ul.list-main li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "深圳市中小企业服务局",
        "url": "http://zxqyj.sz.gov.cn/zwgk/tzgg/",
        "list_selector": "ul.list-main li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    # 福田区
    {
        "name": "福田区工业和信息化局",
        "url": "http://www.szft.gov.cn/bmxx/qgxj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "福田区科技创新局",
        "url": "http://www.szft.gov.cn/bmxx/qkjj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    # 罗湖区
    {
        "name": "罗湖区工业和信息化局",
        "url": "http://www.szlh.gov.cn/xxgk/ztzl/lhqgxj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "罗湖区科技创新局",
        "url": "http://www.szlh.gov.cn/xxgk/ztzl/lhqkjj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
]

all_notices = []

for src in sources:
    print(f"正在抓取: {src['name']}...")
    try:
        # 增加重试机制
        for attempt in range(2):
            try:
                resp = requests.get(src["url"], headers=headers, timeout=30)
                break
            except:
                if attempt == 1:
                    raise
                time.sleep(3)
        
        resp.encoding = "utf-8"
        
        # 检查是否成功获取页面
        if resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code}")
            continue
            
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(src["list_selector"])
        
        print(f"  找到 {len(items)} 个列表项")
        
        if len(items) == 0:
            # 尝试其他可能的选择器
            alt_selectors = ["ul li", "div.list ul li", "div.news-list li", ".list-content li"]
            for alt_sel in alt_selectors:
                items = soup.select(alt_sel)
                if len(items) > 0:
                    print(f"  使用备用选择器 '{alt_sel}' 找到 {len(items)} 项")
                    break
        
        for item in items[:20]:  # 最多取前20条
            try:
                title_tag = item.select_one(src["title_selector"])
                link_tag = item.select_one(src["link_selector"])
                date_tag = item.select_one(src["date_selector"])
                
                if not (title_tag and link_tag and date_tag):
                    # 尝试找任意 a 标签和包含日期的元素
                    all_links = item.find_all("a")
                    if all_links:
                        title_tag = all_links[0]
                        link_tag = all_links[0]
                    date_tag = item.find("span")
                    if not (title_tag and link_tag and date_tag):
                        continue
                
                title = title_tag.get_text(strip=True)
                link = link_tag.get("href", "")
                date_str = date_tag.get_text(strip=True)
                
                if not title or not link:
                    continue
                
                # 补全相对链接
                if link.startswith("/"):
                    base_match = re.match(r"(https?://[^/]+)", src["url"])
                    if base_match:
                        base = base_match.group(1)
                        link = base + link
                    else:
                        continue
                elif not link.startswith("http"):
                    if src["url"].endswith("/"):
                        link = src["url"] + link
                    else:
                        link = src["url"] + "/" + link
                
                # 提取日期
                date_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", date_str)
                if date_match:
                    pub_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"
                else:
                    continue
                
                all_notices.append({
                    "source": src["name"],
                    "title": title,
                    "link": link,
                    "date": pub_date,
                })
                print(f"  ✅ {title[:30]}... {pub_date}")
                
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
