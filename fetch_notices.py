import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# 所有单位配置
sources = [
    # ===== 正常页面（静态网站）=====
    {"name": "深圳市工业和信息化局", "url": "http://gxj.sz.gov.cn/xxgk/xxgkml/qt/tzgg/"},
    {"name": "深圳市科技创新局", "url": "http://stic.sz.gov.cn/xxgk/tzgg/"},
    {"name": "龙岗区科技创新局", "url": "http://www.lg.gov.cn/bmzz/kjj/xxgk/qt/tzgg/"},
    {"name": "龙岗区工业和信息化局", "url": "http://www.lg.gov.cn/bmzz/gxj/xxgk/qt/tzgg/"},
    {"name": "龙华区工业和信息化局", "url": "http://www.szlhq.gov.cn/bmxxgk/jjcjj/dtxx_124217/tzgg_124219/"},
    {"name": "龙华区科技创新局", "url": "http://www.szlhq.gov.cn/bmxxgk/kjcxj/dtxx_124254/tzgg_124256/"},
    {"name": "福田区工业和信息化局", "url": "https://www.szft.gov.cn/bmxx/qgxj/tzgg/"},
    {"name": "福田区科技创新局", "url": "https://www.szft.gov.cn/bmxx/qkjj/tzgg/index.html"},
    {"name": "深圳市中小企业服务局", "url": "http://zxqyj.sz.gov.cn/zwgk/zfxxgkml/tzgg/index.html"},
    # ===== 动态页面（政府信息公开平台）=====
    {"name": "罗湖区科技和工业信息化局", "url": "https://www.szlh.gov.cn/lhqkjhgyxxhj/gkmlpt/index"},
    {"name": "坪山区科技创新局", "url": "https://www.szpsq.gov.cn/pskjcxfws/gkmlpt/index"},
    {"name": "坪山区工业和信息化局", "url": "https://www.szpsq.gov.cn/psjjhkjcjj/gkmlpt/index"},
    {"name": "光明区科技创新局", "url": "https://www.szgm.gov.cn/gmkjcxj/gkmlpt/index"},
    {"name": "光明区工业和信息化局", "url": "https://www.szgm.gov.cn/gmjjfw/gkmlpt/index"},
    {"name": "大鹏新区科技和工业信息化局", "url": "https://www.dpxq.gov.cn/dpkjcxjjfwj/gkmlpt/index"},
    {"name": "宝安区科技创新局", "url": "https://www.baoan.gov.cn/bakj/gkmlpt/index"},
    {"name": "宝安区工业和信息化局", "url": "https://www.baoan.gov.cn/bajjcj/gkmlpt/index"},
    {"name": "南山区科技创新局", "url": "https://www.szns.gov.cn/nsqkcj/gkmlpt/index"},
    {"name": "南山区工业和信息化局", "url": "https://www.szns.gov.cn/nsqjjcjj/gkmlpt/index"},
    {"name": "盐田区科技创新局", "url": "https://www.yantian.gov.cn/ytkcj/gkmlpt/index"},
    {"name": "盐田区工业和信息化局", "url": "https://www.yantian.gov.cn/ytgyhxxhj/gkmlpt/index"},
]

TITLE_BLACKLIST = [
    "Language", "FRANÇAIS", "العربية", "首页", "下一页", "上一页",
    "无障碍", "长者助手", "繁体", "English", "日本語", "한국어",
    "网站地图", "关于我们", "联系我们", "法律声明", "无障碍浏览",
]

def is_valid_title(title):
    return len(title) >= 5 and not any(bad.lower() in title.lower() for bad in TITLE_BLACKLIST)

def extract_date(text):
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text) or re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    return None

all_notices = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    page = context.new_page()
    
    for src in sources:
        print(f"正在抓取: {src['name']}...")
        try:
            page.goto(src["url"], timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(3000)  # 等3秒确保动态内容加载
            
            # 获取所有包含公告链接的a标签
            links = page.query_selector_all("a")
            count = 0
            for a_tag in links[:50]:
                try:
                    title = a_tag.inner_text().strip()
                    href = a_tag.get_attribute("href") or ""
                    
                    if not is_valid_title(title) or not href:
                        continue
                    
                    # 只取政府信息公开内容链接
                    if "/content/post_" not in href and "/tzgg/" not in href:
                        continue
                    
                    # 补全链接
                    if href.startswith("//"):
                        href = "https:" + href
                    elif href.startswith("/"):
                        href = page.url.split("/")[0] + "//" + page.url.split("/")[2] + href
                    
                    # 提取日期
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
        except Exception as e:
            print(f"  ❌ {str(e)[:100]}")
    
    browser.close()

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
