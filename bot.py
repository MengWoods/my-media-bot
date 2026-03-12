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

# --- 蹭热点、强共鸣版类目 ---
categories = ["🚨 紧急提醒", "🔥 社交热议", "👩‍❤️‍👨 夫妻共鸣", "💔 寒心真相", "👑 活出自我"]

prompts = [
    # 🚨 紧急提醒：利用危机感，主打“转发救人”
    "搜集今日国内最新的突发民生新闻、医保政策变动或全国性反诈提醒。要求：标题必须以【紧急提醒】或【刚刚传出】开头，语气极其焦急且关怀。重点强调‘这件事关乎每个人的利益，一定要转发给家里人’。",
    
    # 🔥 社交热议：蹭热点事件，主打“观点输出”
    "选取当前全网热议的一个社会新闻或争议性话题（如养老门槛、社会保障、或典型民生事件）。要求：用深度、理性的笔触剖析事件背后的社会现实。标题要一针见血，引发读者在评论区或朋友圈展开讨论。",
    
    # 👩‍❤️‍👨 夫妻共鸣：利用情感纽带，主打“老伴真情”
    "写一篇关于‘老了以后，老伴才是唯一的依靠’的感人短文。要求：标题要极其抓心（如：等我们老了，最亲的不是孩子，而是...）。内容要写出少年夫妻老来伴的温馨与不易，语气温柔且深情，让读者想发给另一半看。",
    
    # 💔 寒心真相：利用家庭委屈，主打“清醒觉醒”
    "拆穿‘养儿防老’或‘亲戚社交’中的残酷现实。要求：标题要‘委屈但坚强’，如《看透了，也心碎了》。内容要戳中中老年人操劳一生却得不到理解的痛点，引导读者产生‘从此要为自己而活’的共鸣。",
    
    # 👑 活出自我：利用精神向往，主打“晚年富养”
    "写给50-70岁的人：为什么‘高质量的孤独，胜过低质量的凑合’。要求：标题要知性、高级，如《这才是晚年最体面的活法》。文风要禅意且洒脱，鼓励老年人放手子女，去旅游、变美、富养自己的灵魂。"
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
        full_prompt = (
                f"{p}\n\n"
                "要求：\n"
                "1. 生成一个震撼的标题（不带#号）。\n"
                "2. 正文300字左右，语言要有感染力。\n"
                "3. 核心金句和重点内容请使用 **加粗** 语法。\n"
                "4. 根据内容逻辑，适当使用 ### 加上小标题进行分段（每篇2-3个）。\n"
                "5. 最后给一个英文配图关键词，格式为 Keyword:xxx。\n"
                "6. 不要包含 ```markdown 这种外壳标签。"
            )
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

    # --- 修改后（图片挪到文末）---
    md_output += f"## {cat}\n\n"
    md_output += f"# {title}\n\n"
    md_output += f"{body}\n\n"  # 先放正文
    if img_path:
        md_output += f"![img]({img_path})\n\n" # 再放图片，图片就到文末了
    md_output += "---\n\n"

# 保存最终的 Markdown 文件
md_file_path = os.path.join(BASE_DIR, "latest.md")
with open(md_file_path, 'w', encoding='utf-8') as f:
    f.write(md_output)

print(f">>> 成功！Markdown 已保存至 {md_file_path}")