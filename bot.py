import os
import json
import requests
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 配置区
# ==========================================
# 自动检测环境：本地没设 Key 则进入 DEBUG 模式
DEBUG_MODE = os.environ.get("GEMINI_API_KEY") is None 

# 文件夹准备
BASE_DIR = "news-reports"
IMG_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# API 配置
if not DEBUG_MODE:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    UNSPLASH_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
    # 使用你指定的模型名称
    model = genai.GenerativeModel('models/gemini-flash-latest')

categories = ["今日热点", "深度共鸣", "生活智慧", "扎心现实", "晚年智慧"]
prompts = [
    "搜集今日中国最火的民生或感人热点，以‘深度思考、传递正能量’为基调，写一篇标题党、情绪激昂的短文。",
    "针对50-60岁父母，写一篇关于‘为子女操碎心、却得不到理解’的心声感悟。语气要温柔且委屈。",
    "写一篇关于‘坚持几个好习惯，比吃药管用’的科学生活指南。文风要像专家叮嘱，专业且亲切。",
    "针对中老年人，拆穿一些社会交往或亲戚关系的现实（如人走茶凉）。语气要犀利、扎心。",
    "写一段送给退休人群的晚年哲学，关于‘舍弃无效社交、富养自己’。文风要知性、富有禅意。"
]

def download_img(word, index):
    """下载图片并保存到 news-reports/images/"""
    local_filename = f"tab_{index}.jpg"
    local_path = os.path.join(IMG_DIR, local_filename)
    
    if DEBUG_MODE:
        return f"images/{local_filename}" # 调试模式仅返回路径

    search_url = f"https://api.unsplash.com/photos/random?query={word}&client_id={UNSPLASH_KEY}"
    try:
        res = requests.get(search_url, timeout=10).json()
        img_url = res['urls']['regular']
        img_data = requests.get(img_url, timeout=15).content
        with open(local_path, 'wb') as handler:
            handler.write(img_data)
        # 注意：返回给 Markdown 的路径是相对 news-reports 的
        return f"images/{local_filename}"
    except Exception as e:
        print(f"图片下载失败 ({word}): {e}")
        return "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=1000"

# 初始化 Markdown 内容
md_output = f"\n\n"

for i, (cat, p) in enumerate(zip(categories, prompts)):
    print(f"正在处理赛道: {cat}...")
    
    if DEBUG_MODE:
        title = f"【测试】{cat}的震撼真相"
        body = f"这是{cat}赛道的模拟测试内容。请确认网页 Tab 切换和复制功能是否正常。"
        img_path = download_img("test", i)
    else:
        full_prompt = f"{p} 要求：1.生成一个震撼的标题。2.正文50字左右。3.最后给一个配图关键词如 Keyword:xxx (必须英文)。4.不要包含 ```markdown 标签。"
        try:
            response = model.generate_content(full_prompt)
            content = response.text.strip()
            
            # 解析标题、正文和关键词
            lines = [l for l in content.split('\n') if l.strip()]
            title = lines[0].replace('#', '').strip()
            
            keyword = "nature"
            if "Keyword:" in content:
                keyword = content.split("Keyword:")[-1].strip().split()[0]
            
            img_path = download_img(keyword, i)
            
            # 提取正文（去掉第一行和关键词行）
            body = content.replace(lines[0], '', 1)
            if "Keyword:" in body:
                body = body.split("Keyword:")[0]
            body = body.strip()
            
        except Exception as e:
            print(f"{cat} 生成错误: {e}")
            title, body, img_path = f"{cat} 更新中", "内容获取失败，请稍后再试。", ""

    # 按照 index.html 的 Tab 切分要求拼接 Markdown
    md_output += f"## {cat}\n\n"
    md_output += f"# {title}\n\n"
    if img_path:
        md_output += f"![img]({img_path})\n\n"
    md_output += f"{body}\n\n"
    md_output += "---\n\n"

# 保存最终的 Markdown 文件
md_file_path = os.path.join(BASE_DIR, "latest.md")
with open(md_file_path, 'w', encoding='utf-8') as f:
    f.write(md_output)

print(f">>> 成功！Markdown 已保存至 {md_file_path}")