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
    
# ---------------------------------------------------------
# 五大流量赛道：基于用户最新反馈（全领域热点 + 明星八卦）
# ---------------------------------------------------------

categories = ["🔥 热点", "🍺 责任", "🧘 禅修", "🌹 柔情", "🌟 爆料"]

prompts = [
    # 1. 🔥 热点：搜索当天中国最火的新闻热点，不限领域
    "搜索中国当天（2026年3月）全网搜索量最高、最火爆的社会热点新闻（不限领域，涵盖民生、突发、政策或奇闻）。\
    要求：标题必须极具视觉冲击力，如【刚刚发生，全网炸锅了】、【今天这件事，所有人都在看】。\
    内容：详细介绍新闻事件，随后进行辛辣或深度的点评，挖掘背后的社会共鸣。要能引发读者强烈的讨论欲望。",
    
    # 2. 🍺 责任：男人心声，赞美责任感
    "针对中年男性，撰写关于‘责任、隐忍与负重’的共鸣文。写男人默默承担家庭重担、为了妻小绝不喊累的硬汉柔情。\
    要求：标题要戳中泪点，如《男人这辈子，最难的不是没钱，而是推开门后那份无人倾诉的累》。\
    内容：赞美男人的坚韧，写出‘有泪心里流’的担当，给男性读者一份极致的心理慰藉和自我认可。",
    
    # 3. 🧘 禅修：禅宗修行，心灵修炼
    "写一篇关于‘放下纠结、修身养性’的治愈系禅意文。主打‘不勉强、不强求、心静则万事顺’的人生哲学。\
    要求：标题要清新且有深度，如《余生最好的修行：不纠结，不强求，万事随缘》。\
    内容：教读者如何摆脱内心的浮躁和执念，文字要温柔且充满智慧，让读者的心灵瞬间安静下来。",
    
    # 4. 🌹 柔情：女人心声，赞美女性无私
    "写一篇赞美女性为家庭无私付出、隐忍且坚韧的情感文。描写女性在琐碎生活中作为‘家庭压舱石’的伟大。\
    要求：标题要温暖人心，如《谁能读懂她的疲惫？那个为全家人撑起一片天的女人，最该被好好心疼》。\
    内容：深度共情女性的付出，看见她们的操劳。语气要细腻、充满感激，引导家属转发表达爱意。",
    
    # 5. 🌟 爆料：明星八卦，搜索当天热点
    "搜索中国当天（2026年3月）最热门的娱乐圈明星八卦、情感纠葛或演艺圈大事件。\
    要求：标题要带有典型的‘吃瓜’色彩，如【惊天反转！某一线顶流刚刚被曝，全网都在求真相】。\
    内容：客观陈述目前曝出的瓜，并以此探讨娱乐圈的众生相或人际关系。文字要轻快、带一点犀利点评，满足读者的好奇心。"
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
md_output += f"## 💡 指南\n\n"
md_output += f"# 每日素材库 - 他们的叔叔们®群专用\n\n"
md_output += f"**📅 更新日期：{update_date}**\n\n"
md_output += "> **📢 温馨提示：**\n"
md_output += "* **更新频率**：每日更新 5 大热门赛道，紧跟全网热点。\n"
md_output += "* **发布建议**：每篇文章建议仅在公众号**发布一次，避免雷同**，保护账号权重。\n"
md_output += "* **手机办公**：点击右下角按钮复制后，可直接粘贴到【公众号助手App】，手机即可轻松发文。\n"
md_output += "* **操作逻辑**：右滑或点击右上方切换赛道。\n"
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