import os
import json
import time
import requests
import google.generativeai as genai
from datetime import datetime
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 定义安全设置：全部设为 BLOCK_NONE
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

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
    model = genai.GenerativeModel(
        'models/gemini-flash-latest',
        safety_settings=safety_settings)

# --- 蹭热点、强共鸣版类目 ---
categories = ["🚨 紧急提醒", "🔥 社交热议", "👩‍❤️‍👨 夫妻共鸣", "💔 寒心真相", "🌙 深夜私语"]

prompts = [
    # 🚨 紧急提醒：利用“避险心理”，主打信息差
    "搜集今日国内最新的突发民生新闻、医保养老政策变动或全国性高发反诈预警。\
    要求：标题必须极具冲击力，如【万分紧急】、【刚刚传出，谁都别睡】。\
        开头第一句话要直接点出利益受损的风险。语气要像焦急的家人在耳边叮嘱，充满关怀感。\
            文末强调：‘这种事耽误不得，多一人知道就少一人受害，赶紧发到相亲相爱一家人群里！’",
    
    # 🔥 社交热议：利用“正义感/焦虑感”，主打观点站队
    "选取当前全网热议的一个涉及养老、医疗、或社会民生的争议性事件。\
    要求：用犀利且清醒的笔触，拆穿事件背后残酷或真实的社会规律。\
        标题要一针见血，直指人心（如：某些‘遮羞布’该撕下来了）。文章要有金句，\
            能替读者说出他们想说却说不出来的话，强烈激发读者转发到朋友圈进行‘观点站队’或讨论。",
    
    # 👩‍❤️‍👨 夫妻共鸣：利用“双向暗示”，主打中老年战友感
    "针对45-70岁夫妻，写一篇关于‘余生漫漫，唯有老伴是底牌’的感人深度文。\
    要求：标题要对比扎心，如《儿女是别人的，老伴才是自己的》。\
        内容要描写‘年轻时的吵闹不休’与‘老后的相依为命’。\
            语气要像老友谈心，既有烟火气的真实，又有岁月的温情。引导女性读者转发给丈夫，暗示对方要好好珍惜这份‘陪跑’一辈子的情谊。",
    
    # 💔 寒心真相：利用“清醒觉醒”，主打情感补偿
    "深度剖析‘养儿防老’的幻觉或亲戚间‘人走茶凉’的残酷真相。\
    要求：标题要带有一种‘看透红尘’的豁达与委屈，如《掏心掏肺一辈子，我终于活明白了》。\
        正文要戳中读者操劳一生却被边缘化的痛点，文风要从‘寒心’转为‘觉醒’。\
            结尾必须鼓励读者‘从此往后，富养自己’，引发同龄人强烈的情感反弹和收藏欲望。",
    
    # 🌙 深夜私语：利用“深夜脆弱”，主打灵魂抚慰
    "写一篇适合深夜独处的唯美情感散文，聊聊‘那些年为了全家人，那个弄丢了的自己’。\
    要求：标题要极其动人且具有画面感，如《今夜，突然很想和年轻时的自己碰个杯》。\
        文风要像在台灯下翻开旧相册，细腻、柔软、带一点点优美的忧伤。\
            多用比喻，把读者的遗憾写成诗。结尾要给出一个温暖的出口，让读者含泪转发时，感觉自己被这个世界温柔地抱了一下。"
]

def download_img(word, index):
    """下载图片并保存到 news-reports/images/"""
    local_filename = f"tab_{index}.jpg"
    local_path = os.path.join(IMG_DIR, local_filename)
    
    if DEBUG_MODE:
        return f"images/{local_filename}" # 调试模式仅返回路径

    search_url = f"https://api.unsplash.com/photos/random?query={word}&orientation=landscape&&client_id={UNSPLASH_KEY}"
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

# 获取当前更新日期
update_date = datetime.now().strftime('%Y-%m-%d')

# 初始化 Markdown 内容
md_output = f"\n" # 保留隐藏标记供 Title 使用
md_output += f"## 💡 使用指南\n\n"
md_output += f"# 每日素材库\n\n"
md_output += f"**📅 更新日期：{update_date}**\n\n"
md_output += "> **📢 温馨提示：**\n"
md_output += "* **更新频率**：每日准时更新 5 大热门赛道，紧跟全网热点。\n"
md_output += "* **发布建议**：每篇文章建议仅在公众号发布一次，避免雷同，保护账号权重。\n"
md_output += "* **手机办公**：点击右下角按钮复制后，可直接粘贴到【公众号助手App】，手机即可轻松发文。\n"
md_output += "* **操作逻辑**：点击上方 Tab 切换赛道。若内容未更新，请尝试刷新页面。\n"
md_output += "* **意见反馈**：使用中有任何建议或遇到问题，请随时联系开发者反馈。\n\n"
md_output += "---\n\n"

for i, (cat, p) in enumerate(zip(categories, prompts)):
    print(f"正在处理赛道: {cat}...")
    
    if DEBUG_MODE:
        title = f"【测试】{cat}的震撼真相"
        body = f"这是{cat}赛道的模拟测试内容。请确认网页 Tab 切换和复制功能是否正常。"
        img_path = download_img("test", i)
    else:
        full_prompt = (
            f"{p}\n\n"
            "【创作与排版指令】：\n"
            "1. **震撼标题**：生成一个极其抓人、能引发点击欲望的标题（不带#号）。\n"
            "2. **内容篇幅**：正文必须在 500 字左右，确保情感铺垫到位，内容扎实。避免空话，多用具体的生活场景描写。\n"
            "3. **结构布局**：必须使用 ### 加上小标题进行分段（每篇2-3个）。小标题要像正文一样有感染力，不要死板。\n"
            "4. **情绪节奏**：\n"
            "   - 开头：用一句扎心或引起好奇的话瞬间抓住读者。\n"
            "   - 中间：结合现实痛点，通过小标题分层次展开，要有‘剥洋葱’式的代入感。\n"
            "   - 结尾：升华主题，给读者一个情感出口或深刻的反思金句。\n"
            "5. **视觉重点**：将文中核心金句、能够引起共鸣的短句使用 **加粗** 语法，总数不少于 4 处。\n"
            "6. **图片说明**：在末尾提供一个精准的英文配图关键词，格式为 Keyword:xxx。\n"
            "7. **禁令**：严禁包含 ```markdown 这种代码块标签，直接输出纯 Markdown 内容。"
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

        time.sleep(5)  # 避免请求过快被封禁

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