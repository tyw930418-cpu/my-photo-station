import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from PIL.ExifTags import TAGS
from rembg import remove
import io
import zipfile

# --- 核心美化函数 ---
def process_image(file, mode, add_border=True, ai_remove_bg=False):
    raw_img = Image.open(file)
    exif_data = raw_img._getexif()
    info = {TAGS.get(tag, tag): value for tag, value in exif_data.items()} if exif_data else {}
    img = ImageOps.exif_transpose(raw_img)
    
    # AI 抠图 (如果开启)
    if ai_remove_bg:
        img = remove(img)
        img = img.convert("RGBA")

    # 滤镜逻辑
    if mode == "徕卡黑白":
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
            img = Image.merge("RGBA", (gray, gray, gray, a))
        else:
            img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.4)
    elif mode == "自动增强":
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.1)

    # 妮情专属拍立得边框
    if add_border:
        w, h = img.size
        # 提取参数
        cam = info.get('Model', 'Digital Camera')
        focal = info.get('FocalLength', '?')
        f_stop = info.get('FNumber', '?')
        iso = info.get('ISOSpeedRatings', '?')
        
        # 构造底部文字：品牌名 + 参数
        brand_tag = "N I Q I N G   S T U D I O" # 妮情工坊
        param_text = f"{cam}  |  {focal}mm  f/{f_stop}  ISO {iso}"
        
        border_h = int(h * 0.20) # 留白稍微加大，更有呼吸感
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        
        if img.mode == 'RGBA':
            new_img.paste(img, (0, 0), mask=img.split()[3])
        else:
            new_img.paste(img, (0, 0))
            
        draw = ImageDraw.Draw(new_img)
        # 品牌名字居中大写
        draw.text((int(w*0.05), h + int(border_h*0.25)), brand_tag, fill=(0, 0, 0))
        # 参数信息在下方浅灰色小字
        draw.text((int(w*0.05), h + int(border_h*0.55)), param_text, fill=(120, 120, 120))
        img = new_img
    return img

# --- UI 界面 ---
st.set_page_config(page_title="妮情摄影工坊 Pro", layout="wide")
st.title("🕯️ 妮情摄影工坊 | NIQING STUDIO")

st.sidebar.header("🎛️ 创作设置")
mode = st.sidebar.selectbox("胶片风格", ["原稿导出", "自动增强", "徕卡黑白"])
ai_remove_bg = st.sidebar.toggle("启用 AI 自动抠图", value=False)
add_border = st.sidebar.toggle("启用妮情专属边框", value=True)

uploaded_files = st.file_uploader("批量导入素材", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            processed_img = process_image(file, mode, add_border, ai_remove_bg)
            with cols[idx % 3]:
                st.image(processed_img, use_container_width=True)
            
            img_byte_arr = io.BytesIO()
            save_img = processed_img.convert("RGB")
            save_img.save(img_byte_arr, format='JPEG', quality=95)
            # 导出的文件名也加上品牌前缀
            zip_file.writestr(f"NIQING_{file.name}.jpg", img_byte_arr.getvalue())

    st.divider()
    st.balloons()
    st.download_button("📥 一键导出妮情作品集", data=zip_buffer.getvalue(), file_name="NIQING_WORKS.zip")
else:
    st.info("👋 欢迎来到妮情空间。在左侧导入你的影像，开启艺术化处理。")
else:
    st.info("👋 你好 wutianlong！请在左侧侧边栏上传照片。建议开启‘拍立得边框’。")
