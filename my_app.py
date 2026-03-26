import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
import io, requests, time

# --- 1. 深度 UI 美化 (完全模仿黑金高级感) ---
st.set_page_config(page_title="妮情 · MJ & 即梦工坊", layout="wide")

st.markdown("""
    <style>
    /* 全局背景与文字颜色 */
    .stApp { background-color: #0A0A0A; color: #EEDCBF !important; }
    
    /* 选项卡(Tabs) 样式定制：模仿截图的黄色高亮切换 */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #262626;
        border-radius: 25px;
        color: #EEDCBF;
        padding: 0px 30px;
        border: 1px solid #333;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFB300 !important;
        color: black !important;
        font-weight: 700;
        border: none;
    }

    /* 模块容器样式：深色卡片 */
    [data-testid="stVerticalBlock"] > div > div {
        background-color: #171717; border-radius: 20px; padding: 25px;
        border: 1px solid #333; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
    }

    /* 橙色大按钮：生成专用 */
    .stButton > button {
        background-color: #FFB300 !important;
        color: black !important;
        border-radius: 35px !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        width: 100%;
        border: none;
        padding: 12px;
        box-shadow: 0 4px 15px rgba(255, 179, 0, 0.2);
    }
    
    /* 宽高比矩阵按钮：深灰色方块 */
    .ratio-grid .stButton > button {
        background-color: #262626 !important;
        color: #EEDCBF !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
        padding: 8px !important;
    }

    /* 输入框样式 */
    textarea {
        background-color: #121212 !important;
        border: 1px solid #333 !important;
        border-radius: 15px !important;
        color: #EEDCBF !important;
    }
    
    /* 隐藏默认装饰线 */
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心后端函数 (翻译与逻辑预留) ---
def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

# --- 3. UI 界面布局 (双栏设计) ---
col_left, col_right = st.columns([1.2, 1], gap="large")

# 尝试获取 Secrets 中的 Key
try:
    mj_key = st.secrets.get("MJ_API_KEY", "").strip()
    volc_ak = st.secrets.get("VOLC_AK", "").strip()
except:
    mj_key, volc_ak = "", ""

# --- 👈 左侧：交互式控制中心 ---
with col_left:
    # 使用 Tabs 实现点击切换功能
    tab_mj, tab_jm = st.tabs(["Midjourney 创意", "即梦视频大师"])
    
    # --- Midjourney 选项卡内容 ---
    with tab_mj:
        st.write(" ")
        mj_type = st.radio("创作引擎", ["MJ 文生图", "MJ 图生图 (垫图)"], horizontal=True, label_visibility="collapsed")
        
        if mj_type == "MJ 图生图 (垫图)":
            st.markdown("##### 📸 参考底图 (Image Reference)")
            st.file_uploader("上传 1-5 张图片作为参考", type=["jpg", "png"], accept_multiple_files=True, key="up_mj")
        
        st.write(" ")
        st.markdown("##### 📐 宽高比 (Aspect Ratio)")
        # 模仿截图的按钮矩阵样式
        st.markdown('<div class="ratio-grid">', unsafe_allow_html=True)
        r_cols = st.columns(5)
        with r_cols[0]: st.button("1:1", key="ar1")
        with r_cols[1]: st.button("9:16", key="ar2")
        with r_cols[2]: st.button("16:9", key="ar3")
        with r_cols[3]: st.button("3:4", key="ar4")
        with r_cols[4]: st.button("4:3", key="ar5")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write(" ")
        st.markdown("##### ✍️ 创意描述 (Prompt)")
        mj_txt = st.text_area("输入你的艺术构思...", placeholder="例如：夏日海边，复古电影调，1990s...", height=120, key="txt_mj")
        
        st.write(" ")
        if st.button("🔮 开启艺术渲染 (MJ)", key="btn_mj"):
            if not mj_key:
                st.warning("🔑 请先在 Secrets 中配置 MJ_API_KEY")
            else:
                with st.status("🎨 Midjourney 正在排队并构思...", expanded=True):
                    st.write(f"🌐 翻译引擎已就绪: {translate_to_en(mj_txt)}")
                    time.sleep(3); st.success("地基已稳，等待 MJ 接口返回图像。")

    # --- 即梦视频 选项卡内容 ---
    with tab_jm:
        st.write(" ")
        st.markdown("##### 🎞️ 视频起始帧 (Initial Frame)")
        st.file_uploader("上传一张图片，即梦将赋予它生命", type=["jpg", "png"], key="up_jm")
        
        st.write(" ")
        st.markdown("##### 🚀 动态描述 (Motion Prompt)")
        jm_txt = st.text_area("描述你想要的运动轨迹...", placeholder="例如：海水缓缓流过脚踝，镜头平稳向后推进...", height=120, key="txt_jm")
        
        st.write(" ")
        if st.button("🎬 启动即梦引擎渲染", key="btn_jm"):
            if not volc_ak:
                st.error("🔑 还没检测到火山引擎 Key！请在 Secrets 中配置。")
            else:
                with st.status("🎬 即梦正在生成视频...", expanded=True):
                    p_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.04); p_bar.progress(i+1)
                    st.success("视频渲染中，请稍候...")

# --- 👉 右侧：实时输出预览 ---
with col_right:
    st.markdown("##### 🖼️ 实时输出结果 (Output)")
    st.write(" ")
    
    # 演示用的预览布局
    with st.container():
        c_in, _, c_out = st.columns([1, 0.1, 1])
        with c_in:
            st.image("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=500", caption="输入源 (Input)")
        with c_out:
            st.image("https://images.unsplash.com/photo-1618220179428-22790b461013?w=500", caption="重绘参考 (Ref)")
    
    st.divider()
    st.info("提示：MJ 生成的结果通常包含 4 张预览图。您可以点击下方的“即梦”按钮将其转化为动态视频。")
