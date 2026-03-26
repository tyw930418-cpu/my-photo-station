import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
import io, requests, time

# --- 1. 深度 UI 美化 (黑金视觉 + 品牌标题) ---
st.set_page_config(page_title="NQ生成工作坊", layout="wide")

st.markdown("""
    <style>
    /* 全局背景与文字 */
    .stApp { background-color: #0A0A0A; color: #EEDCBF !important; }
    
    /* 🌟 顶部品牌标题 (NQ生成工作坊) */
    .nq-header {
        background-color: #171717;
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #FFB300;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 0 20px rgba(255, 179, 0, 0.2);
    }
    .nq-title {
        color: #FFB300 !important;
        letter-spacing: 8px;
        text-shadow: 0 0 15px rgba(255, 179, 0, 0.5);
        margin: 0;
        font-size: 2.5em !important;
        font-weight: 900 !important;
    }
    .nq-subtitle {
        color: #888;
        letter-spacing: 3px;
        font-size: 1em;
        margin-top: 8px;
        text-transform: uppercase;
    }

    /* 选项卡(Tabs) 定制 */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #262626;
        border-radius: 25px;
        color: #EEDCBF;
        padding: 0px 35px;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFB300 !important;
        color: black !important;
        font-weight: 700;
    }

    /* 模块容器卡片 */
    [data-testid="stVerticalBlock"] > div > div {
        background-color: #171717; border-radius: 20px; padding: 25px;
        border: 1px solid #333; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
    }

    /* 按钮样式 */
    .stButton > button {
        background-color: #FFB300 !important;
        color: black !important;
        border-radius: 35px !important;
        font-weight: 700 !important;
        width: 100%;
        border: none;
        padding: 12px;
    }
    
    /* 宽高比矩阵按钮 */
    .ratio-grid .stButton > button {
        background-color: #262626 !important;
        color: #EEDCBF !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
    }

    textarea {
        background-color: #121212 !important;
        border: 1px solid #333 !important;
        border-radius: 15px !important;
        color: #EEDCBF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 翻译与逻辑预留 ---
def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

# --- 🌟 3. 顶部品牌区 ---
st.markdown("""
<div class="nq-header">
    <h1 class="nq-title">NQ生成工作坊</h1>
    <p class="nq-subtitle">NIQING GENERATION WORKSHOP</p>
</div>
""", unsafe_allow_html=True)

# --- 4. UI 布局 ---
col_left, col_right = st.columns([1.2, 1], gap="large")

# 获取密钥 (用于未来激活)
try:
    mj_key = st.secrets.get("MJ_API_KEY", "").strip()
    volc_ak = st.secrets.get("VOLC_AK", "").strip()
except:
    mj_key, volc_ak = "", ""

# --- 👈 左侧：控制中心 ---
with col_left:
    tab_mj, tab_jm = st.tabs(["Midjourney 创意", "即梦视频大师"])
    
    with tab_mj:
        st.write(" ")
        mj_mode = st.radio("模式", ["MJ 文生图", "MJ 图生图 (垫图)"], horizontal=True, label_visibility="collapsed")
        
        if mj_mode == "MJ 图生图 (垫图)":
            st.markdown("##### 📸 参考底图")
            st.file_uploader("上传参考图", type=["jpg", "png"], accept_multiple_files=True, key="up_mj")
        
        st.write(" ")
        st.markdown("##### 📐 宽高比选择")
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
        mj_txt = st.text_area("输入构思...", placeholder="电影感，85mm镜头...", height=120, key="txt_mj")
        
        if st.button("🔮 开启艺术渲染 (MJ)", key="go_mj"):
            if not mj_key: st.warning("🔑 请在 Secrets 配置 MJ_API_KEY")
            else:
                with st.status("🎨 MJ 构思中...", expanded=True):
                    st.write(f"翻译结果: {translate_to_en(mj_txt)}")
                    time.sleep(3); st.success("地基就绪！")

    with tab_jm:
        st.write(" ")
        st.markdown("##### 🎞️ 视频起始帧")
        st.file_uploader("上传图片，赋予生命", type=["jpg", "png"], key="up_jm")
        
        st.write(" ")
        st.markdown("##### 🚀 动态描述")
        jm_txt = st.text_area("描述动作...", placeholder="镜头推近，水面波动...", height=120, key="txt_jm")
        
        if st.button("🎬 启动即梦引擎", key="go_jm"):
            if not volc_ak: st.error("🔑 请配置火山引擎 Key")
            else:
                with st.spinner("视频渲染中..."):
                    time.sleep(3); st.success("连接成功！")

# --- 👉 右侧：输出预览 ---
with col_right:
    st.markdown("##### 🖼️ 实时输出结果")
    st.write(" ")
    c_in, _, c_out = st.columns([1, 0.1, 1])
    with c_in: st.image("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400", caption="输入源")
    with c_out: st.image("https://images.unsplash.com/photo-1618220179428-22790b461013?w=400", caption="效果参考")
    
    st.divider()
    st.info("💡 提示：NQ生成工作坊已准备就绪。")
