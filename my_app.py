import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from rembg import remove
import io
import zipfile
import requests

# --- 1. 配置与视觉美化 (落日橙 + 奶油白) ---
st.set_page_config(page_title="妮情 · 青春创意工坊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF9F5; }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#FF9E7D, #FF6B6B);
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: white !important; font-weight: bold;
    }
    h1 { color: #FF5E3A; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
    .stButton>button {
        background-color: #FF8E53; color: white; border-radius: 20px;
        border: none; padding: 10px 25px; transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(255, 142, 83, 0.3);
    }
    .stButton>button:hover { background-color: #FF6B6B; transform: translateY(-2px); }
    .stFileUploader, .stImage {
        background: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心：AI 请求函数 (使用最新 Router 路径) ---
# 选用了更稳定的 OpenJourney 模型，非常有摄影质感
API_URL = "https://router.huggingface.co/prompthero/openjourney"

def query_ai_art(prompt, hf_token):
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            try: return response.json()
            except: return {"error": f"码: {response.status_code}"}
        if not response.content:
            return {"error": "返回为空，请重试"}
        if "image" in response.headers.get("Content-Type", ""):
            return response.content
        else:
            return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- 3. 核心：图片处理函数 (带妮情边框) ---
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

# --- 4. UI 逻辑主体 ---
st.title("🍓 妮情 · 青春创意工坊 | NIQING")
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
    prompt = st.text_area("描述你的梦境 (推荐英文)", placeholder="e.g. A portrait of a girl in sunset, cinematic lighting, 85mm lens")
    
    if st.button("开始梦境生成"):
        if not token: st.warning("🔑 请在侧边栏输入 Token")
        elif not prompt: st.warning("📝 请输入提示词")
        else:
            with st.spinner("🕯️ 妮情 AI 正在构思..."):
                result = query_ai_art(prompt, token)
                
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
                        st.info(f"🕒 模型正在苏醒... 预计还需 {int(result['estimated_time'])} 秒，请稍后再次点击。")
                    else:
                        st.error(f"❌ 提示: {result.get('error', '未知错误')}")
