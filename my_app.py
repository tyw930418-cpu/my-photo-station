import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from rembg import remove
import io
import zipfile
import requests
import base64

# --- 1. 配置与视觉美化 ---
st.set_page_config(page_title="妮情 · 深海创意工坊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A192F; }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1B4D4B, #00A3AF);
        color: #E0F2F1;
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

# --- 2. 核心函数定义 ---

# 模型地址
TEXT_MODEL = "https://router.huggingface.co/prompthero/openjourney"
IMAGE_MODEL = "https://router.huggingface.co/runwayml/stable-diffusion-v1-5"

def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

def query_ai(prompt, hf_token, is_img2img=False, init_image=None):
    headers = {"Authorization": f"Bearer {hf_token}"}
    url = IMAGE_MODEL if is_img2img else TEXT_MODEL
    
    if is_img2img and init_image:
        # 图生图需要将图片转为字节发送
        buf = io.BytesIO()
        init_image.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        payload = {
            "inputs": prompt,
            "image": base64.b64encode(img_bytes).decode("utf-8"),
            "parameters": {"strength": 0.5} 
        }
        # 注意：部分 API 接收方式不同，这里采用通用的 json 封装
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    else:
        payload = {"inputs": prompt}
        response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        try: return response.json()
        except: return {"error": f"码: {response.status_code}"}
    return response.content

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
        border_h = int(h * 0.20)
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        if img.mode == 'RGBA': new_img.paste(img, (0, 0), mask=img.split()[3])
        else: new_img.paste(img, (0, 0))
        draw = ImageDraw.Draw(new_img)
        draw.text((int(w*0.05), h + int(border_h*0.3)), "N I Q I N G   S T U D I O", fill=(0, 0, 0))
        img = new_img
    return img

# --- 3. UI 逻辑 ---
st.title("🏖️ 妮情 · 仲夏海边工坊 | NIQING")
app_mode = st.sidebar.radio("请选择操作", ["影像后期", "AI 文生图", "AI 图生图"])

# 安全获取 Token
try:
    token = st.secrets["HF_TOKEN"].strip()
except:
    token = st.sidebar.text_input("🔑 Token 备用输入", type="password")

# --- 影像后期 ---
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

# --- AI 文生图 ---
elif app_mode == "AI 文生图":
    prompt = st.text_area("输入你的梦境 (支持中文)", placeholder="例如：深海中的发光少女...")
    if st.button("开始梦境生成"):
        if not token: st.warning("🔑 请在后台配置 Token")
        else:
            with st.spinner("🌊 妮情 AI 正在构思..."):
                en_p = translate_to_en(prompt)
                st.caption(f"🌐 自动翻译: {en_p}")
                result = query_ai(en_p, token)
                if isinstance(result, bytes):
                    gen_img = Image.open(io.BytesIO(result))
                    final = process_image(gen_img, "原色风格", add_border=True)
                    st.image(final, use_container_width=True)
                else: st.error(f"提示: {result}")

# --- AI 图生图 (垫图) ---
elif app_mode == "AI 图生图":
    ref_file = st.file_uploader("上传一张参考底图", type=["jpg", "png"])
    prompt = st.text_area("描述你想要的改造效果", placeholder="例如：把这个风景变成梵高风格")
    if st.button("开始重绘"):
        if ref_file and token:
            with st.spinner("🎨 正在参考原图重绘..."):
                en_p = translate_to_en(prompt)
                init_img = Image.open(ref_file).convert("RGB").resize((512, 512))
                result = query_ai(en_p, token, is_img2img=True, init_image=init_img)
                if isinstance(result, bytes):
                    gen_img = Image.open(io.BytesIO(result))
                    final = process_image(gen_img, "原色风格", add_border=True)
                    st.image(final, use_container_width=True)
                else: st.error(f"提示: {result}")
        else: st.warning("请上传图片并确保 Token 已设置")
