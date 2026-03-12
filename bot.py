import os
import json
import requests
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 开发调试开关
# ==========================================
# 本地测试时设为 True (不调用 API)
# 上传到 GitHub 前建议设为 False，或者使用下方的自动检测逻辑
DEBUG_MODE = os.environ.get("GEMINI_API_KEY") is None 

print(f"--- 当前运行模式: {'DEBUG (模拟)' if DEBUG_MODE else 'PRODUCTION (正式)'} ---")

# 配置 API (仅在非 DEBUG 模式下需要)
if not DEBUG_MODE:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    UNSPLASH_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
    model = genai.GenerativeModel('gemini-1.5-flash')

# 确保图片文件夹存在
if not os.path.exists('imgs'):
    os.makedirs('imgs')

categories = ["今日热点", "深度共鸣", "生活智慧", "扎心现实", "晚年智慧"]
prompts = [
    "搜集今日中国最火的民生或感人热点，以‘深度思考、传递正能量’为基调，写一篇标题党、情绪激昂的短文。",
    "针对50-60岁父母，写一篇关于‘为子女操碎心、却得不到理解’的心声感悟。语气要温柔且委屈。",
    "写一篇关于‘坚持几个好习惯，比吃药管用’的科学生活指南。文风要像专家叮嘱，专业且亲切。",
    "针对中老年人，拆穿一些社会交往或亲戚关系的现实（如人走茶凉）。语气要犀利、扎心。",
    "写一段送给退休人群的晚年哲学，关于‘舍弃无效社交、富养自己’。文风要知性、富有禅意。"
]

def download_img(word, index):
    """下载图片并保存到本地"""
    if DEBUG_MODE:
        return f"https://via.placeholder.com/600x400?text=Debug+Image+{index}"

    search_url = f"https://api.unsplash.com/photos/random?query={word}&client_id={UNSPLASH_KEY}"
    local_path = f"imgs/tab_{index}.jpg"
    try:
        res = requests.get(search_url, timeout=10).json()
        img_url = res['urls']['regular']
        img_data = requests.get(img_url, timeout=15).content
        with open(local_path, 'wb') as handler:
            handler.write(img_data)
        return local_path
    except Exception as e:
        print(f"图片下载失败 ({word}): {e}")
        return "https://images.unsplash.com/photo-1495020689067-958852a7765e?q=80&w=1000"

results = []

for i, (cat, p) in enumerate(zip(categories, prompts)):
    print(f"正在生成赛道: {cat}...")
    
    if DEBUG_MODE:
        # 模拟数据
        title = f"【测试】{cat}：这是你绝对不能错过的真相！"
        body = f"<p>这是针对<b>{cat}</b>赛道的模拟测试正文。</p><p>老祖宗说得好：测试千万条，代码第一条。<strong>关注这个绿色加粗文字</strong>，你的生活会更好。</p><p>点击下方按钮即可复制。测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
        local_img_path = download_img("test", i)
    else:
        # 正式调用 API
        full_prompt = f"{p} 要求：1.生成标题。2.正文300字。3.最后给一个英文配图关键词如 Keyword:xxx。4.HTML格式，段落用<p>，重要处用<strong>并内联绿色样式。"
        try:
            response = model.generate_content(full_prompt)
            text = response.text.replace('```html', '').replace('```', '').strip()
            
            lines = [l for l in text.split('\n') if l.strip()]
            title = lines[0].replace('#', '').strip()
            
            keyword = "nature"
            if "Keyword:" in text:
                keyword = text.split("Keyword:")[-1].strip().split()[0]
            
            local_img_path = download_img(keyword, i)
            
            body = text.replace(lines[0], '', 1)
            if "Keyword:" in body:
                body = body.split("Keyword:")[0]
            body = body.strip()
        except Exception as e:
            print(f"{cat} 生成失败: {e}")
            title, body, local_img_path = f"{cat}更新中", "<p>内容正在快马加鞭赶来...</p>", ""

    results.append({
        "category": cat,
        "title": title,
        "img_url": local_img_path,
        "body": body
    })

# 读取模板并替换
try:
    with open('index_template.html', 'r', encoding='utf-8') as f:
        template = f.read()

    final_html = template.replace('{{DATA_JSON}}', json.dumps(results, ensure_ascii=False))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(">>> 恭喜！index.html 已成功生成。")
except Exception as e:
    print(f"文件处理出错: {e}")