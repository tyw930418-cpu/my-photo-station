import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
import io, requests, time

# --- 1. 深度 CSS 美化 (模仿黑金 UI) ---
st.set_page_config(page_title="妮情 · MJ 创意工坊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: #EEDCBF !important; }
    [data-testid="stVerticalBlock"] > div > div {
        background-color: #171717; border-radius: 20px; padding: 20px;
        border: 1px solid #333; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    label, p { color: #EEDCBF !important; }
    .mj-tag { background-color: #FFB300; color: black !important; padding: 5px 15px; border-radius: 20px; font-weight: 700; display: inline-block; margin-right: 10px; }
    .text-tag { background-color: #262626; color: #EEDCBF !important; padding: 5px 15px; border-radius: 20px; display: inline-block; }
    .stButton > button { background-color: #262626; color: #EEDCBF !important; border-radius: 10px !important; width: 100% !important; border: 1px solid #333 !important; }
    .generate-btn > div > button { background-color: #FFB300 !important; color: black !important; border-radius: 30px !important; font-weight: 700 !important; }
    textarea { background-color: #121212 !important; border: 1px solid #333 !important; color: #EEDCBF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心后端函数 ---
def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

# --- 3. UI 界面布局 ---
col_control, col_output = st.columns([1.1, 1], gap="large")

# 密钥安全获取 (预留)
try:
    mj_key = st.secrets.get("MJ_API_KEY", "").strip()
    volc_ak = st.secrets.get("VOLC_AK", "").strip()
except:
    mj_key, volc_ak = "", ""

# --- 👈 左侧：控制面板 ---
with col_control:
    st.markdown('<span class="mj-tag">Midjourney 创意</span> <span class="text-tag">即梦视频大师</span>', unsafe_allow_html=True)
    st.write(" ")
    mj_mode = st.radio("模式选择", ["MJ 文生图", "MJ 图生图 (垫图)"], label_visibility="collapsed")
    
    if mj_mode == "MJ 图生图 (垫图)":
        st.markdown("##### 参考图 (MJ 垫图)")
        st.file_uploader("点击或拖拽上传 (0/5)", type=["jpg", "png"], accept_multiple_files=True)
    
    st.write(" ")
    st.markdown("##### 宽高比")
    ar_cols = st.columns(5)
    with ar_cols[0]: st.button("1:1")
    with ar_cols[1]: st.button("9:16")
    with ar_cols[2]: st.button("16:9")
    with ar_cols[3]: st.button("3:4")
    with ar_cols[4]: st.button("4:3")
    
    st.write(" ")
    st.markdown("##### 创意描述")
    mj_prompt = st.text_area("输入重绘指令...", placeholder="例如：夏日海滩边的复古少女...", height=150)
    
    st.write(" ")
    st.markdown("<div class='generate-btn'>", unsafe_allow_html=True)
    if st.button("🔮 激活艺术瞬间"):
        if not mj_key:
            st.warning("🔑 请先在 Secrets 中配置 MJ_API_KEY")
        else:
            with st.status("🌊 Midjourney 正在构思...", expanded=True) as status:
                en_p = translate_to_en(mj_prompt)
                status.write(f"🌐 翻译结果: {en_p}")
                for i in range(1, 6):
                    time.sleep(1)
                    status.write(f"渲染进度: {i*20}%...")
                st.success("✅ 框架运行正常！等待正式接口接入。")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 👉 右侧：输出区 ---
with col_output:
    st.markdown("##### 输出结果")
    
    # 视频大师预留
    with st.expander("🎞️ 即梦·视频灵动瞬间", expanded=False):
        st.file_uploader("上传起始帧", type=["jpg", "png"])
        st.button("🎬 开始视频渲染")

    st.write(" ")
    # 演示预览图
    c1, _, c2 = st.columns([1, 0.2, 1])
    with c1: st.image("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=640", caption="原图预览")
    with c2: st.image("https://images.unsplash.com/photo-1618220179428-22790b461013?q=80&w=640", caption="MJ 效果参考")
    
    st.info("提示：MJ 生成的是 2x2 网格图。")
