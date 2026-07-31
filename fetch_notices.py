import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

# 更完整的浏览器模拟头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

sources = [
    # ===== 市级 =====
    {
        "name": "深圳市工业和信息化局",
        "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/",
        "type": "normal",
    },
    {
        "name": "深圳市科技创新局",
        "url": "http://stic.sz.gov.cn/xxgk/tzgg/",
        "type": "normal",
    },
    {
        "name": "深圳市中小企业服务局",
        "url": "https://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html",
        "type": "normal",
    },
    # ===== 福田区 =====
    {
        "name": "福田区工业和信息化局",
        "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/",
        "type": "normal",
    },
    {
        "name": "福田区科技创新局",
        "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html",
        "type": "normal",
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
    },
    {
        "name": "龙岗区工业和信息化局",
        "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/",
        "type": "normal",
    },
    # ===== 龙华区 =====
    {
        "name": "龙华区工业和信息化局",
        "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/",
        "type": "normal",
    },
    {
        "name": "龙华区科技创新局",
        "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/",
        "type": "normal",
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

# 过滤无关内容的黑名单
TITLE_BLACKLIST = [
    "Language", "FRANÇAIS", "العربية", "首页", "下一页", "上一页",
    "无障碍", "长者助手", "繁体", "English", "日本語", "한국어",
    "网站地图", "关于我们", "联系我们", "法律声明",
]

def is_valid_title(title):
    """检查标题是否有效"""
    if len(title) < 5:
        return False
    for bad in TITLE_BLACKLIST:
        if bad.lower() in title.lower():
            return False
    return True

def extract_date_from_text(text):
    """从文本中提取日期"""
    patterns = [
        r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
    return None

all_notices = []

for src in sources:
    print(f"正在抓取: {src['name']}...")
    try:
        # 增加重试和等待
        resp = None
        for attempt in range(3):
            try:
                resp = requests.get(src["url"], headers=headers, timeout=30, allow_redirects=True)
                if resp.status_code == 200:
                    break
                time.sleep(3)
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(5)
        
        if not resp or resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code if resp else 'error'}")
            continue
        
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        items = []
        
        if src["type"] == "normal":
            # 尝试多种选择器
            selectors = [
                "ul.list-main li a",
                "ul li a",
                ".list-content li a",
                ".news-list li a",
                "ul.list li a",
            ]
            
            for selector in selectors:
                items = soup.select(selector)
                if len(items) > 0:
                    # 过滤掉明显不是公告的链接
                    valid_items = []
                    for a in items:
                        title = a.get_text(strip=True)
                        if is_valid_title(title):
                            valid_items.append(a)
                    if len(valid_items) > 0:
                        items = valid_items
                        print(f"  使用选择器 '{selector}' 找到 {len(items)} 条有效公告")
                        break
            
            if len(items) == 0:
                # 通用匹配：找所有包含 content/post_ 的链接
                all_links = soup.find_all("a", href=True)
                for a in all_links:
                    href = a.get("href", "")
                    title = a.get_text(strip=True)
                    if ("/content/post_" in href or "/tzgg/" in href) and is_valid_title(title):
                        items.append(a)
                if len(items) > 0:
                    print(f"  使用通用匹配找到 {len(items)} 条有效公告")
            
            for a_tag in items[:30]:
                try:
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get("href", "")
                    
                    if not is_valid_title(title) or not link:
                        continue
                    
                    # 清理标题（去掉前面的序号和特殊字符）
                    title = re.sub(r'^[\d\.\、\s]+', '', title)
                    
                    # 补全链接
                    if link.startswith("/"):
                        base_match = re.match(r"(https?://[^/]+)", src["url"])
                        if base_match:
                            link = base_match.group(1) + link
                    elif not link.startswith("http"):
                        link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                    
                    # 提取日期
                    pub_date = extract_date_from_text(str(a_tag.parent)) or extract_date_from_text(title)
                    if not pub_date:
                        pub_date = datetime.now().strftime("%Y-%m-%d")
                    
                    all_notices.append({
                        "source": src["name"],
                        "title": title,
                        "link": link,
                        "date": pub_date,
                    })
                    print(f"  ✅ {title[:50]}... {pub_date}")
                    
                except Exception as e:
                    continue
        
        elif src["type"] == "gkmlpt":
            # 政府信息公开平台
            doc_links = soup.find_all("a", class_="document-number")
            if len(doc_links) == 0:
                doc_links = soup.select("a[href*='content/post_']")
            
            print(f"  找到 {len(doc_links)} 条记录")
            
            for a_tag in doc_links[:30]:
                try:
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get("href", "")
                    
                    if not is_valid_title(title) or not link:
                        continue
                    
                    # 补全链接
                    if link.startswith("//"):
                        link = "https:" + link
                    elif link.startswith("/"):
                        base_match = re.match(r"(https?://[^/]+)", src["url"])
                        if base_match:
                            link = base_match.group(1) + link
                    elif not link.startswith("http"):
                        link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                    
                    # 提取日期
                    pub_date = extract_date_from_text(str(a_tag.parent)) or extract_date_from_text(title)
                    if not pub_date:
                        pub_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # 清理标题
                    title = re.sub(r'^[\d\.\、\s]+', '', title)
                    
                    all_notices.append({
                        "source": src["name"],
                        "title": title,
                        "link": link,
                        "date": pub_date,
                    })
                    print(f"  ✅ {title[:50]}... {pub_date}")
                    
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
print(f"来源分布:")
from collections import Counter
sources_count = Counter(n["source"] for n in unique_notices)
for name, count in sources_count.most_common():
    print(f"  {name}: {count} 条")
