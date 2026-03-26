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

# 模型地址
TEXT_MODEL = "https://router.huggingface.co/prompthero/openjourney"
# 未来接入火山引擎的地址预留
DREAMINA_VIDEO_URL = "https://visual.volcengineapi.com/api/v1/video_generation" 

def translate_to_en(text):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q={requests.utils.quote(text)}"
    try:
        r = requests.get(url, timeout=5)
        return r.json()[0][0][0]
    except: return text

def query_huggingface(prompt, hf_token):
    headers = {"Authorization": f"Bearer {hf_token}"}
    response = requests.post(TEXT_MODEL, headers=headers, json={"inputs": prompt}, timeout=60)
    if response.status_code != 200: return {"error": "生成失败"}
    return response.content

# 🚀 即梦视频生成逻辑 (预留框架)
def query_dreamina_video(image_obj, prompt, ak, sk):
    # 这里是未来接入火山引擎 SDK 的位置
    # 逻辑：1. 上传图片 -> 2. 提交任务 -> 3. 循环查询状态 -> 4. 返回视频 URL
    return None # 目前返回空，等待 Key 到位

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
app_mode = st.sidebar.radio("请选择操作", ["影像后期", "AI 文生图", "AI 视频大师"])

# Token 安全获取
try: 
    hf_token = st.secrets["HF_TOKEN"].strip()
    volc_ak = st.secrets.get("VOLC_AK", "").strip()
    volc_sk = st.secrets.get("VOLC_SK", "").strip()
except: 
    hf_token = ""
    volc_ak, volc_sk = "", ""

# --- 模式：影像后期 & 文生图 (保持你之前的成熟逻辑) ---
if app_mode == "影像后期":
    files = st.file_uploader("导入素材", type=["jpg", "png"], accept_multiple_files=True)
    if files:
        for f in files: st.image(process_image(Image.open(f), "原色风格"), use_container_width=True)

elif app_mode == "AI 文生图":
    prompt = st.text_area("描述梦境")
    if st.button("造梦"):
        with st.spinner("🌊 正在生成..."):
            res = query_huggingface(translate_to_en(prompt), hf_token)
            if isinstance(res, bytes): st.image(process_image(Image.open(io.BytesIO(res)), "原色风格"))

# --- 🌟 新增模式：AI 视频大师 ---
elif app_mode == "AI 视频大师":
    st.subheader("🎥 即梦引擎 · 灵动时刻")
    video_ref = st.file_uploader("上传一张底图 (视频的起始帧)", type=["jpg", "png"])
    motion = st.text_area("描述动态效果", placeholder="例如：海浪缓慢拍打，阳光在水面闪烁")
    
    if st.button("开始渲染视频"):
        if not volc_ak or not volc_sk:
            st.error("🔑 还没检测到火山引擎密钥！请在 Secrets 中配置 VOLC_AK 和 VOLC_SK")
        elif not video_ref:
            st.warning("📸 请先上传一张参考图")
        else:
            # 这是一个模拟过程，等 Key 填好后我们会写正式的 Request
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for percent_complete in range(100):
                time.sleep(0.1) # 模拟视频生成的漫长等待
                progress_bar.progress(percent_complete + 1)
                status_text.text(f"🎬 视频渲染中... {percent_complete+1}%")
            
            st.success("✅ 渲染完成！(当前为演示模式，请填入 Key 激活真实引擎)")
            # 这里的 st.video 会在未来播放真实生成的 .mp4
