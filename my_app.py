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
    .stApp { background-color: #0A192F; }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1B4D4B, #00A3AF);
        color: #E0F2F1;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #E0F2F1 !important; font-weight: 600;
    }
    h1 {
        color: #64FFDA; font-family: 'Segoe UI', sans-serif;
        letter-spacing: 3px; text-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
    }
    .stButton>button {
        background-color: #00A3AF; color: white; border-radius: 25px;
        border: none; padding: 10px 30px; transition: all 0.4s ease;
    }
    .stButton>button:hover { background-color: #64FFDA; color: #0A192F; transform: scale(1.05); }
    .stFileUploader, .stImage, .stTextArea, .stAlert {
        background-color: #3E2723; color: #EEDCBF; padding: 20px;
        border-radius: 20px; border: 1px solid #5D4037; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    textarea { color: #EEDCBF !important; background-color: #2D1B18 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心：功能函数定义 ---

API_URL = "https://router.huggingface.co/prompthero/openjourney"

# ✨ 翻译官函数
def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except:
        return text

# 🚀 刚才丢失的 AI 请求引擎 (补回来了！)
def query_ai_art(prompt, hf_token):
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            try: return response.json()
            except: return {"error": f"码: {response.status_code}"}
        if not response.content: return {"error": "返回为空"}
        if "image" in response.headers.get("Content-Type", ""): return response.content
        else: return response.json()
    except Exception as e: return {"error": str(e)}

# 🖼️ 图片处理函数
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
        else:
            img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.4)
    
    if add_border:
        w, h = img.size
        brand_tag = "N I Q I N G   S T U D I O"
        border_h = int(h * 0.20)
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        if img.mode == 'RGBA':
            new_img.paste(img, (0, 0), mask=img.split()[3])
        else:
            new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)
        draw.text((int(w*0.05), h + int(border_h*0.3)), brand_tag, fill=(0, 0, 0))
        img = new_img
    return img

# --- 3. UI 逻辑主体 ---
st.title("🏖️ 妮情 · 仲夏海边工坊 | NIQING")
st.sidebar.markdown("### 🎨 创作模式")
app_mode = st.sidebar.radio("请选择操作", ["影像后期", "AI 文生图"])

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

elif app_mode == "AI 文生图":
    token = st.sidebar.text_input("Hugging Face Token", type="password")
    prompt = st.text_area("描述你的梦境 (支持中文)", placeholder="例如：深海中的发光少女...")
    
    if st.button("开始梦境生成"):
        if not token: st.warning("🔑 请在侧边栏输入 Token")
        elif not prompt: st.warning("📝 请输入提示词")
        else:
            with st.spinner("🌊 妮情 AI 正在构思并自动转译..."):
                en_prompt = translate_to_en(prompt)
                if en_prompt != prompt:
                    st.caption(f"🌐 翻译结果: {en_prompt}")
                
                result = query_ai_art(en_prompt, token)
                
                if isinstance(result, bytes):
                    try:
                        gen_img = Image.open(io.BytesIO(result))
                        final = process_image(gen_img, "原色风格", add_border=True)
                        st.image(final, caption="妮情 AI 创意生成", use_container_width=True)
                        buf = io.BytesIO()
                        final.save(buf, format="JPEG")
                        st.download_button("💾 保存这张 AI 作品", data=buf.getvalue(), file_name="NIQING_AI.jpg")
                    except Exception as e: st.error(f"解析失败: {e}")
                elif isinstance(result, dict):
                    if "estimated_time" in result:
                        st.info(f"🕒 模型正在苏醒... 预计还需 {int(result['estimated_time'])} 秒")
                    else:
                        st.error(f"❌ 提示: {result.get('error', '未知错误')}")
