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
# 五大爆款赛道：基于用户最新分类逻辑的精准 Prompt
# ---------------------------------------------------------

categories = ["🔥 热点", "🍺 责任", "🧘 禅修", "🌹 柔情", "🚀 科技"]

prompts = [
    # 1. 🔥 热点：搜集最热点、易引发讨论的新闻，标题抓人眼球
    "搜集2026年3月最新、最火的社会新闻或民生政策（如：延迟退休正式实施、医保补助上调、或引发全网争论的民生事件）。\
    要求：标题必须极具冲击力，利用悬念或反差，如【刚刚传出，全网吵翻了】、【谁也没想到，真相竟然是这样】。\
    内容：先快速介绍新闻点，随后进行深度探讨，挖掘背后的人性或社会规律。语气要清醒、犀利，能瞬间引爆评论区讨论。",
    
    # 2. 🍺 责任：男人心声，赞美责任感，引发共鸣
    "针对中年男性，写一篇关于‘责任与负重’的深度共鸣文。重点描述男人‘有苦自扛、默默承受、为了家和孩子绝不喊累’的真实写照。\
    要求：标题要扎心，如《那个在车里坐很久才下楼的男人，心里藏着多少没说出口的累》。\
    内容：赞美男人的脊梁，写出他们‘有泪心里流’的坚韧。语气要深沉且带有温度，让男人看了想流泪，让家属看了想心疼。",
    
    # 3. 🧘 禅修：禅宗修行，不纠结、不勉强，心灵修炼
    "写一篇关于‘禅意人生、心灵修行’的治愈系散文。主打‘不为外物所动、不纠结、不勉强、凡事随缘’的生活哲学。\
    要求：标题要清新且有哲理，如《余生最好的活法：不纠结，不勉强，凡事发生皆利于我》。\
    内容：提供精神上的松弛感，教人如何在喧嚣的世界中修得一颗安静的心。文字要极简、优雅，适合深夜静读或清晨感悟。",
    
    # 4. 🌹 柔情：女人心声，赞美女性无私与承担
    "写一篇赞美女性在家庭中‘无私奉献、为孩子和家操心、有怨言也忍着’的情感文。\
    要求：标题要充满爱与理解，如《这一生，她活成了家里的光，却唯独忘了好好爱自己》。\
    内容：精准捕捉女性在琐碎家务与母职中的辛劳，看见她们的坚韧与不易。语气要细腻、温柔，给读者极致的情感代入和心理补偿。",
    
    # 5. 🚀 科技：最新科技前沿，介绍并展望未来
    "搜集2026年3月最前沿的科技进展（如：人工智能‘智能体’爆发、量子计算突破、或脑机接口的新应用）。\
    要求：标题要带有科幻感和震撼力，如《颠覆认知！这项刚刚诞生的黑科技，正在改写人类的未来》。\
    内容：用通俗易懂但充满激情的语言介绍这项技术，并幻想它将如何改变我们的未来生活。文风要硬核且充满想象力。"
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