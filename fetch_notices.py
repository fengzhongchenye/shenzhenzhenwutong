import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# 所有需要抓取的单位及其通知公告页面配置
# 每个单位包含：名称、URL、列表项的CSS选择器、标题选择器、链接选择器、日期选择器
sources = [
    # ===== 市级 =====
    {
        "name": "深圳市工业和信息化局",
        "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/tzgg/",
        "list_selector": "ul.list-main li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "深圳市科技创新委员会",
        "url": "http://stic.sz.gov.cn/xxgk/tzgg/",
        "list_selector": "ul.list-main li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "深圳市中小企业服务局",
        "url": "http://zxqyj.sz.gov.cn/xxgk/tzgg/",
        "list_selector": "ul.list-main li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    # ===== 福田区 =====
    {
        "name": "福田区工业和信息化局",
        "url": "http://www.szft.gov.cn/ftq/zfbm/gxj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "福田区科技创新局",
        "url": "http://www.szft.gov.cn/ftq/zfbm/kjcxj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    # ===== 罗湖区 =====
    {
        "name": "罗湖区工业和信息化局",
        "url": "http://www.szlh.gov.cn/lhq/zfbm/gxj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    {
        "name": "罗湖区科技创新局",
        "url": "http://www.szlh.gov.cn/lhq/zfbm/kjcxj/tzgg/",
        "list_selector": "ul.list li",
        "title_selector": "a",
        "link_selector": "a",
        "date_selector": "span.date",
    },
    # 你还可以按相同格式继续添加其他区（南山区、盐田区、宝安区、龙岗区、龙华区、坪山区、光明区等）
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

all_notices = []

for src in sources:
    try:
        resp = requests.get(src["url"], headers=headers, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(src["list_selector"])
        for item in items:
            try:
                title_tag = item.select_one(src["title_selector"])
                link_tag = item.select_one(src["link_selector"])
                date_tag = item.select_one(src["date_selector"])
                if not (title_tag and link_tag and date_tag):
                    continue

                title = title_tag.get_text(strip=True)
                link = link_tag.get("href")
                date_str = date_tag.get_text(strip=True)

                # 补全相对链接
                if link and link.startswith("/"):
                    # 取源 URL 的根域名
                    base = re.match(r"(https?://[^/]+)", src["url"]).group(1)
                    link = base + link

                # 日期格式处理（常见：2024-12-01 或 2024-12-01 09:00）
                date_match = re.search(r"\d{4}-\d{2}-\d{2}", date_str)
                if date_match:
                    pub_date = date_match.group(0)
                else:
                    continue  # 没有提取到日期就跳过

                all_notices.append({
                    "source": src["name"],
                    "title": title,
                    "link": link,
                    "date": pub_date,
                })
            except:
                continue
    except Exception as e:
        print(f"抓取 {src['name']} 失败: {e}")

# 去重（按链接）
seen = set()
unique_notices = []
for n in all_notices:
    if n["link"] not in seen:
        seen.add(n["link"])
        unique_notices.append(n)

# 保存为 JSON 文件
with open("notices.json", "w", encoding="utf-8") as f:
    json.dump(unique_notices, f, ensure_ascii=False, indent=2)

print(f"总共抓取到 {len(unique_notices)} 条公告")
