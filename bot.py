import os
import json
import requests
import google.generativeai as genai
from datetime import datetime

# 1. 配置 API
# 建议在本地测试时手动填入，上传 GitHub 前确保使用 os.environ
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
UNSPLASH_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
model = genai.GenerativeModel('gemini-1.5-flash')

categories = ["今日热点", "深度共鸣", "生活智慧", "扎心现实", "晚年智慧"]
prompts = [
    "搜集今日中国最火的民生或感人热点，以‘深度思考、传递正能量’为基调，写一篇标题党、情绪激昂的短文。",
    "针对50-60岁父母，写一篇关于‘为子女操碎心、却得不到理解’的心声感悟。语气要温柔且委屈。",
    "写一篇关于‘坚持几个好习惯，比吃药管用’的科学生活指南。文风要像专家叮嘱，专业且亲切。",
    "针对中老年人，拆穿一些社会交往或亲戚关系的现实（如人走茶凉）。语气要犀利、扎心。",
    "写一段送给退休人群的晚年哲学，关于‘舍弃无效社交、富养自己’。文风要知性、富有禅意。"
]

def get_img(word):
    # 增加 timeout 防止 GitHub Actions 卡死
    url = f"https://api.unsplash.com/photos/random?query={word}&client_id={UNSPLASH_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        return res['urls']['regular']
    except Exception as e:
        print(f"图片抓取失败: {e}")
        return "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=1000" # 默认一张新闻感图片

results = []

for cat, p in zip(categories, prompts):
    print(f"正在生成赛道: {cat}...")
    
    # 优化 Prompt：明确要求不要包含 Markdown 代码块标签 (```html)
    full_prompt = f"""
    {p} 
    要求：
    1. 生成一个震撼的标题。
    2. 正文300字左右。
    3. 最后给一个配图关键词如 Keyword:xxx (必须用英文)。
    4. 使用HTML格式，段落用<p>，关键短语用<strong>加粗并显绿色(#07c160)。
    5. 直接输出 HTML 内容，不要包含 ```html 等 Markdown 格式标记。
    """
    
    try:
        response = model.generate_content(full_prompt)
        text = response.text
        
        # 优化解析逻辑：防止 AI 输出 Markdown 导致网页乱码
        clean_text = text.replace('```html', '').replace('```', '').strip()
        
        # 提取标题（假设第一行是标题）
        lines = [l for l in clean_text.split('\n') if l.strip()]
        title = lines[0].replace('#', '').strip()
        
        # 提取关键词
        keyword = "nature"
        if "Keyword:" in clean_text:
            keyword = clean_text.split("Keyword:")[-1].strip().split()[0]
        
        # 提取正文：去掉标题和关键词部分
        body = clean_text.replace(lines[0], '', 1)
        if "Keyword:" in body:
            body = body.split("Keyword:")[0]

        results.append({
            "category": cat,
            "title": title,
            "img_url": get_img(keyword),
            "body": body.strip()
        })
    except Exception as e:
        print(f"{cat} 生成失败: {e}")

# 读取模板并替换
# 增加 encoding='utf-8' 防止 Windows/Linux 环境编码冲突
try:
    with open('index_template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    final_html = template.replace('{{DATA_JSON}}', json.dumps(results, ensure_ascii=False))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("成功：index.html 已生成！")
except FileNotFoundError:
    print("错误：未找到 index_template.html 文件，请检查文件名。")