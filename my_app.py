import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from PIL.ExifTags import TAGS
from rembg import remove
import io
import zipfile
import requests
import time

# --- 💡 新增：Hugging Face 免费绘画函数 ---
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

def query_ai_art(prompt, hf_token):
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    
    response = requests.post(API_URL, headers=headers, json=payload)
    
    # 如果模型正在加载，需要重试
    if response.status_code == 503:
        return "loading"
    return response.content

# --- 核心美化函数 (复用之前的逻辑) ---
def process_image(img_obj, mode, add_border=True, ai_remove_bg=False):
    # 这里的 img_obj 可以是上传的文件，也可以是 AI 生成的 PIL Image
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

# --- UI 界面 ---
st.set_page_config(page_title="妮情 AI 创意工坊", layout="wide")
st.title("🕯️ 妮情摄影工坊 | NIQING STUDIO")

st.sidebar.header("🎨 创作模式")
app_mode = st.sidebar.radio("选择工作区", ["影像后期", "AI 文生图"])

# --- 模式 A：影像后期 ---
if app_mode == "影像后期":
    mode = st.sidebar.selectbox("影调选择", ["原色风格", "自动增强", "徕卡黑白"])
    ai_remove_bg = st.sidebar.toggle("启用 AI 自动抠图", value=False)
    add_border = st.sidebar.toggle("启用妮情专属边框", value=True)
    
    uploaded_files = st.file_uploader("导入摄影素材", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
            cols = st.columns(3)
            for idx, file in enumerate(uploaded_files):
                processed_img = process_image(Image.open(file), mode, add_border, ai_remove_bg)
                with cols[idx % 3]:
                    st.image(processed_img, use_container_width=True)
                img_byte = io.BytesIO()
                processed_img.convert("RGB").save(img_byte, format='JPEG', quality=95)
                zip_file.writestr(f"NIQING_{idx}.jpg", img_byte.getvalue())
        st.download_button("📥 导出作品集", data=zip_buffer.getvalue(), file_name="NIQING_WORKS.zip")

# --- 模式 B：AI 文生图 ---
elif app_mode == "AI 文生图":
    hf_token = st.text_input("输入你的 Hugging Face Token (hf_...)", type="password")
    prompt = st.text_area("描述你想要的画面", placeholder="e.g. Cinematic noir photography...")
    
    if st.button("开始梦境生成"):
        if not hf_token:
            st.warning("请输入 Token。")
        else:
            with st.spinner("妮情 AI 正在构思..."):
                result = query_ai_art(prompt, hf_token)
                
                # 🛡️ 增加防御逻辑：检查返回的数据到底是不是图片
                try:
                    # 尝试把返回的数据当做图片打开
                    generated_img = Image.open(io.BytesIO(result))
                    
                    # 如果成功打开，则套用边框
                    final_art = process_image(generated_img, "原色风格", add_border=True)
                    st.image(final_art, caption="妮情 AI 创意生成", use_container_width=True)
                    
                    buf = io.BytesIO()
                    final_art.save(buf, format="JPEG")
                    st.download_button("💾 保存这张 AI 作品", data=buf.getvalue(), file_name="NIQING_AI.jpg")
                
                except Exception:
                    # 如果打开失败，说明 result 里面是错误文本
                    error_msg = result.decode("utf-8") if isinstance(result, bytes) else "未知错误"
                    
                    if "estimated_time" in error_msg:
                        st.info("🕒 模型正在苏醒中... 请等待 30 秒后再点一次。")
                    elif "Authorization" in error_msg:
                        st.error("🔑 Token 无效，请检查是否输入正确。")
                    else:
                        st.error(f"❌ 抱歉，生成出错了：{error_msg}")
