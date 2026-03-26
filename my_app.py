import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from rembg import remove
import io, zipfile, requests, base64, time

# --- 1. 深度 CSS 美化 (完全模仿截图配色与布局) ---
st.set_page_config(page_title="妮情 · MJ 创意工坊", layout="wide")

st.markdown("""
    <style>
    /* 全局背景色：深黑 */
    .stApp { background-color: #0A0A0A; color: #EEDCBF !important; }
    
    /* 模仿截图的深色卡片样式 (控制面板) */
    [data-testid="stVerticalBlock"] > div > div {
        background-color: #171717;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #333;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* 文字标签颜色：模仿截图的米棕色 */
    label, p { color: #EEDCBF !important; font-weight: 500; }
    
    /* 模仿截图顶部的黄色高亮标签按钮 */
    .mj-tag {
        background-color: #FFB300;
        color: black !important;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        margin-right: 10px;
    }
    .text-tag {
        background-color: #262626;
        color: #EEDCBF !important;
        padding: 5px 15px;
        border-radius: 20px;
        display: inline-block;
    }
    
    /* 模仿截图的宽高比按钮样式 */
    .stButton > button {
        background-color: #262626;
        color: #EEDCBF !important;
        border-radius: 10px !important;
        width: 100% !important;
        border: 1px solid #333 !important;
        padding: 10px !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover { background-color: #444 !important; }
    
    /* 模仿截图最下方的大橙色生成按钮 */
    .generate-btn > div > button {
        background-color: #FFB300 !important;
        color: black !important;
        border-radius: 30px !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        padding: 15px 30px !important;
    }
    .generate-btn > div > button:hover { transform: scale(1.02); opacity: 0.9; }
    
    /* 上传组件美化 */
    .stFileUploader > div {
        background-color: #1A1A1A !important;
        border: 2px dashed #444 !important;
        border-radius: 15px !important;
    }
    
    /* 输入框样式 */
    textarea {
        background-color: #121212 !important;
        border: 1px solid #333 !important;
        border-radius: 15px !important;
        color: #EEDCBF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 后端核心逻辑 ---

# 翻译官
def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

# 图片后期 (影调+边框)
def process_image(img_obj, mode="原色风格", add_border=True):
    img = ImageOps.exif_transpose(img_obj)
    if mode == "徕卡黑白":
        img = ImageOps.grayscale(img.convert("RGB"))
        img = ImageEnhance.Contrast(img).enhance(1.4)
    if add_border:
        w, h = img.size
        border_h = int(h * 0.20)
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)
        draw.text((int(w*0.05), h + int(border_h*0.3)), "N I Q I N G   S T U D I O", fill=(0, 0, 0))
        img = new_img
    return img

# Midjourney 预埋调用 (文/图)
def mj_query(prompt, api_key, image_url=None):
    # 此处预留给未来正式的 MJ 中转接口
    # 如果是图生图，需要先把图片传图床拿链接，这里预埋一个模拟过程
    return {"task_id": "mock_mj_123", "status": "SUCCESS"}

# 即梦视频预埋调用
def seaweed_video_query(image_file, prompt, ak, sk):
    # 此处预留给火山引擎 SDK 的同步上传接口
    return {"task_id": "mock_seaweed_123", "status": "PENDING"}

# --- 3. UI 界面布局 (模仿截图双栏布局) ---

col_control, col_output = st.columns([1.1, 1], gap="large")

# 密钥管理
try: 
    mj_key = st.secrets.get("MJ_API_KEY", "").strip()
    volc_ak = st.secrets.get("VOLC_AK", "").strip()
    volc_sk = st.secrets.get("VOLC_SK", "").strip()
except: mj_key, volc_ak, volc_sk = "", "", ""

# --- 👈 左侧：控制面板 (模仿截图) ---
with col_control:
    # 顶部功能标签
    st.markdown('<span class="mj-tag">Midjourney 创意</span> <span class="text-tag">即梦视频大师</span>', unsafe_allow_html=True)
    
    st.write(" ")
    mj_mode = st.radio("MJ 引擎模式", ["MJ 文生图", "MJ 图生图 (垫图)"], label_visibility="collapsed")
    
    # 上传部分
    if mj_mode == "MJ 图生图 (垫图)":
        st.markdown("##### 参考图 (MJ 垫图)", help="上传图片将作为 Midjourney 的构思参考")
        mj_ref = st.file_uploader("点击或拖拽上传 (0/5)", type=["jpg", "png"], accept_multiple_files=True)
    
    # 宽高比部分 (模仿截图的按钮矩阵)
    st.write(" ")
    st.markdown("##### 宽高比")
    ar_cols = st.columns(5)
    with ar_cols[0]: st.button("◼️ 1:1")
    with ar_cols[1]: st.button("▮ 9:16")
    with ar_cols[2]: st.button("▬ 16:9")
    with ar_cols[3]: st.button("▮ 3:4")
    with ar_cols[4]: st.button("◼️ 4:3")
    
    # 提示词输入框
    st.write(" ")
    st.markdown("##### 创意描述")
    mj_prompt = st.text_area("输入重绘指令...", placeholder="例如：夏日海滩边的复古少女，胶片感...", height=150)
    
    # 生成按钮
    st.write(" ")
    st.markdown("<div class='generate-btn'>", unsafe_allow_html=True)
    if st.button("🔮 激活艺术瞬间 (MJ 耗时约60s)"):
        if not mj_key: st.error("请先配置 MJ_API_KEY")
        else:
            with st.status("🌊 Midjourney 正在构思...", expanded=True) as status:
                en_prompt = translate_to_en(mj_prompt)
                status.write(f"🌐 转译指令: {en_prompt}")
                # 模拟 MJ 渲染进度
                for p in range(1, 11):
                    time.sleep(1)
                    status.write(f"当前进度: {p*10}%...")
                st.info("地基已就绪！拿到正式 Key 后即可激活真实 MJ 艺术创作。")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 👉 右侧：输出区 (模仿截图) ---
with col_output:
    st.markdown("##### 输出结果")
    
    # 预埋即梦视频入口 (在输出区顶部占个位)
    with st.expander("🎞️ 即梦·视频灵动瞬间 (可选)", expanded=False):
        video_ref = st.file_uploader("上传起始帧 (让这张图动起来)", type=["jpg", "png"])
        motion = st.text_area("描述动作轨迹")
        if st.button("🎬 生成视频演示"):
            progress_bar = st.progress(0)
            for p in range(100):
                time.sleep(0.08)
                progress_bar.progress(p + 1)
            st.info("地基已通！填入火山引擎 Key 后即可激活真实视频渲染。")

    # 模仿截图的“试穿”预览对比效果 (这里放一张演示图)
    st.write(" ")
    col_demo_1, col_demo_arrow, col_demo_2 = st.columns([1, 0.2, 1])
    with col_demo_1:
        st.image("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=640", use_container_width=True, caption="妮情工作室原图")
    with col_demo_arrow:
        st.write(" ")
        st.markdown("<h2 style='text-align:center;'>➡️</h2>", unsafe_allow_html=True)
    with col_demo_2:
        st.image("https://images.unsplash.com/photo-1618220179428-22790b461013?q=80&w=640", use_container_width=True, caption="MJ 重绘参考图")
    
    st.info("提示：MJ 生成的是 2x2 网格图。')
