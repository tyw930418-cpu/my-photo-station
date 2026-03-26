import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from rembg import remove
import io, zipfile, requests, base64, time

# --- 1. 视觉美化 ---
st.set_page_config(page_title="妮情 · 深海创意工坊", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0A192F; }
    [data-testid="stSidebar"] { background-image: linear-gradient(#1B4D4B, #00A3AF); color: #E0F2F1; }
    h1 { color: #64FFDA; letter-spacing: 3px; text-shadow: 0 0 10px rgba(100, 255, 218, 0.3); }
    .stFileUploader, .stImage, .stTextArea, .stAlert, .stVideo {
        background-color: #3E2723; color: #EEDCBF; padding: 20px; border-radius: 20px; 
        border: 1px solid #5D4037; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    textarea { color: #EEDCBF !important; background-color: #2D1B18 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心函数 ---
TEXT_MODEL = "https://router.huggingface.co/prompthero/openjourney"
# 图生图使用 SD 1.5 兼容接口
IMG2IMG_MODEL = "https://router.huggingface.co/runwayml/stable-diffusion-v1-5"

def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

def query_ai(prompt, hf_token, is_img2img=False, init_image=None):
    headers = {"Authorization": f"Bearer {hf_token}"}
    url = IMG2IMG_MODEL if is_img2img else TEXT_MODEL
    
    if is_img2img and init_image:
        buf = io.BytesIO()
        init_image.save(buf, format="PNG")
        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        payload = {"inputs": prompt, "image": img_str, "parameters": {"strength": 0.5}}
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    else:
        response = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=60)

    if response.status_code != 200:
        try: return response.json()
        except: return {"error": f"码: {response.status_code}"}
    return response.content

def process_image(img_obj, mode, add_border=True):
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
        draw.text((int(w*0.05), h + int(border_h*0.3)), "N I Q I N G   S T U D I O", fill=(0, 0, 0))
        img = new_img
    return img

# --- 3. UI 主体 ---
st.title("🏖️ 妮情 · 仲夏海边工坊 | NIQING")
app_mode = st.sidebar.radio("请选择操作", ["影像后期", "AI 文生图", "AI 图生图", "AI 视频大师"])

try: 
    token = st.secrets["HF_TOKEN"].strip()
    volc_ak = st.secrets.get("VOLC_AK", "").strip()
    volc_sk = st.secrets.get("VOLC_SK", "").strip()
except: 
    token = ""
    volc_ak, volc_sk = "", ""

# --- 影像后期 ---
if app_mode == "影像后期":
    files = st.file_uploader("导入摄影素材", type=["jpg", "png"], accept_multiple_files=True)
    if files:
        for f in files: st.image(process_image(Image.open(f), "原色风格"), use_container_width=True)

# --- AI 文生图 ---
elif app_mode == "AI 文生图":
    prompt = st.text_area("描述你的梦境")
    if st.button("开始造梦"):
        with st.spinner("🌊 正在生成..."):
            res = query_ai(translate_to_en(prompt), token)
            if isinstance(res, bytes):
                st.image(process_image(Image.open(io.BytesIO(res)), "原色风格"))
            else: st.error(f"提示: {res}")

# --- AI 图生图 (重磅回归！) ---
elif app_mode == "AI 图生图":
    ref_file = st.file_uploader("上传参考底图", type=["jpg", "png"])
    prompt = st.text_area("输入重绘指令")
    if st.button("魔法重绘"):
        if ref_file and token:
            with st.spinner("🎨 正在参考原图重绘..."):
                init_img = Image.open(ref_file).convert("RGB").resize((512, 512))
                res = query_ai(translate_to_en(prompt), token, is_img2img=True, init_image=init_img)
                if isinstance(res, bytes):
                    st.image(process_image(Image.open(io.BytesIO(res)), "原色风格"))
                else: st.error(f"提示: {res}")

# --- AI 视频大师 ---
elif app_mode == "AI 视频大师":
    st.subheader("🎥 即梦引擎 · 灵动时刻")
    video_ref = st.file_uploader("上传起始帧图片", type=["jpg", "png"])
    motion = st.text_area("描述动作方向")
    if st.button("生成演示动画"):
        progress_bar = st.progress(0)
        for p in range(100):
            time.sleep(0.05)
            progress_bar.progress(p + 1)
        st.info("地基已就绪！拿到火山引擎 Key 后即可激活真实视频渲染。")
            # 这里的 st.video 会在未来播放真实生成的 .mp4
