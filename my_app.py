import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from rembg import remove
import io
import zipfile
import requests

# --- 1. 配置与视觉美化 (深海背景 + 椰沙棕卡片 + 薄荷绿侧边栏) ---
st.set_page_config(page_title="妮情 · 深海创意工坊", layout="wide")

st.markdown("""
    <style>
    /* 1. 整体背景：深邃的午夜海蓝色 */
    .stApp {
        background-color: #0A192F; 
    }
    
    /* 2. 侧边栏：依然保持薄荷绿，但在深色背景下会更亮眼 */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1B4D4B, #00A3AF);
        color: #E0F2F1;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #E0F2F1 !important;
        font-weight: 600;
    }

    /* 3. 标题：极光青色，带一点发光效果 */
    h1 {
        color: #64FFDA;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 300;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
    }

    /* 4. 按钮：深海青色 */
    .stButton>button {
        background-color: #00A3AF;
        color: white;
        border-radius: 25px;
        border: none;
        padding: 10px 30px;
        transition: all 0.4s ease;
    }
    .stButton>button:hover {
        background-color: #64FFDA;
        color: #0A192F;
        transform: scale(1.05);
    }

    /* 5. 🛠️ 核心：棕色卡片在深色背景下的表现 */
    .stFileUploader, .stImage, .stTextArea, .stAlert {
        background-color: #3E2723; /* 深椰壳棕 */
        color: #EEDCBF; /* 浅沙色文字，形成对比 */
        padding: 20px;
        border-radius: 20px;
        border: 1px solid #5D4037; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }

    /* 输入框内部文字颜色调整 */
    textarea {
        color: #EEDCBF !important;
        background-color: #2D1B18 !important; /* 内部更深一点的棕色 */
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心：AI 请求函数 ---
API_URL = "https://router.huggingface.co/prompthero/openjourney"

# ✨ [在此处插入] 翻译官函数：把你的中文梦境翻译成 MJ 听得懂的英文
def translate_to_en(text):
    import requests
    # 这是一个简单有效的谷歌翻译爬虫接口
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except:
        return text # 如果网络波动，就返回原词
# --- 3. 核心：图片处理函数 (保持不变) ---
def process_image(img_obj, mode, add_border=True, ai_remove_bg=False):
    img = ImageOps.exif_transpose(img_obj)
    if ai_remove_bg:
        img_byte = io.BytesIO()
        img.save(img_byte, format='PNG')
        out_data = remove(img_byte.getvalue())
        img = Image.open(io.BytesIO(out_data)).convert("RGBA")
    if mode == "徕卡黑白":
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
            img = Image.merge("RGBA", (gray, gray, gray, a))
        else: img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.4)
    if add_border:
        w, h = img.size
        brand_tag = "N I Q I N G   S T U D I O"
        border_h = int(h * 0.20)
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        if img.mode == 'RGBA': new_img.paste(img, (0, 0), mask=img.split()[3])
        else: new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)
        draw.text((int(w*0.05), h + int(border_h*0.3)), brand_tag, fill=(0, 0, 0))
        img = new_img
    return img

# --- 4. UI 逻辑主体 (保持不变) ---
st.title("🏖️ 妮情 · 仲夏海边工坊 | NIQING")
st.sidebar.markdown("### 🎨 创作模式")
app_mode = st.sidebar.radio("请选择操作", ["影像后期", "AI 文生图"])

# --- 模式 A：影像后期 ---
if app_mode == "影像后期":
    mode = st.sidebar.selectbox("影调选择", ["原色风格", "徕卡黑白"])
    ai_remove_bg = st.sidebar.toggle("自动抠图", value=False)
    add_border = st.sidebar.toggle("妮情专属边框", value=True)
    
    files = st.file_uploader("导入摄影素材", type=["jpg", "png"], accept_multiple_files=True)
    if files:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zip_f:
            cols = st.columns(3)
            for idx, f in enumerate(files):
                p_img = process_image(Image.open(f), mode, add_border, ai_remove_bg)
                with cols[idx % 3]: st.image(p_img, use_container_width=True)
                img_b = io.BytesIO()
                p_img.convert("RGB").save(img_b, format='JPEG', quality=95)
                zip_f.writestr(f"NIQING_{idx}.jpg", img_b.getvalue())
        st.download_button("📥 批量导出作品", data=zip_buf.getvalue(), file_name="NIQING_WORKS.zip")

# --- 模式 B：AI 文生图 ---
elif app_mode == "AI 文生图":
    token = st.sidebar.text_input("Hugging Face Token", type="password")
    prompt = st.text_area("输入你的梦境 (支持中文)", placeholder="例如：深海中的发光少女，电影感光影...")
    
    if st.button("开始梦境生成"):
        if not token: 
            st.warning("🔑 请在侧边栏输入 Token")
        elif not prompt: 
            st.warning("📝 请输入提示词")
        else:
            with st.spinner("🌊 妮情 AI 正在跨越语言阻碍并构思..."):
                # 🛠️ 关键一步：调用你定义的翻译官
                en_prompt = translate_to_en(prompt)
                
                # 如果是中文翻译过来的，显示一下翻译结果，方便你学习关键词
                if en_prompt != prompt:
                    st.caption(f"🌐 自动翻译结果: {en_prompt}")
                
                # 注意：这里传给 query_ai_art 的必须是 en_prompt
                result = query_ai_art(en_prompt, token)
                
                if isinstance(result, bytes):
                    try:
                        gen_img = Image.open(io.BytesIO(result))
                        # 自动套用妮情专属边框
                        final = process_image(gen_img, "原色风格", add_border=True)
                        st.image(final, caption="妮情 AI 创意生成", use_container_width=True)
                        
                        buf = io.BytesIO()
                        final.save(buf, format="JPEG")
                        st.download_button("💾 保存这张 AI 作品", data=buf.getvalue(), file_name="NIQING_AI.jpg")
                    except Exception as e: 
                        st.error(f"解析失败: {e}")
                
                elif isinstance(result, dict):
                    if "estimated_time" in result:
                        st.info(f"🕒 模型正在苏醒... 预计还需 {int(result['estimated_time'])} 秒，请稍后再次点击。")
                    else:
                        st.error(f"❌ 提示: {result.get('error', '未知错误')}")
