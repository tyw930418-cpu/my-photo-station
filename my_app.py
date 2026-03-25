import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from PIL.ExifTags import TAGS
from rembg import remove # AI 抠图核心引擎
import io
import zipfile

# --- 核心处理函数 (AI + 滤镜 + 品牌边框) ---
def process_image(file, mode, add_border=True, ai_remove_bg=False):
    # 1. 读取原图并备份 EXIF 信息
    raw_img = Image.open(file)
    exif_data = raw_img._getexif()
    info = {TAGS.get(tag, tag): value for tag, value in exif_data.items()} if exif_data else {}
    
    # 自动校正照片方向
    img = ImageOps.exif_transpose(raw_img)
    
    # 2. AI 自动抠图 (核心：将背景剥离，转换为透明图层)
    if ai_remove_bg:
        # 转换字节流供 rembg 处理
        img_byte = io.BytesIO()
        img.save(img_byte, format='PNG')
        out_data = remove(img_byte.getvalue())
        img = Image.open(io.BytesIO(out_data)).convert("RGBA")

    # 3. 风格滤镜 (适配透明度图层)
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

    # 4. 妮情 (NIQING) 专属拍立得边框
    if add_border:
        w, h = img.size
        # 准备品牌与拍摄参数
        brand_tag = "N I Q I N G   S T U D I O"
        cam = info.get('Model', 'Digital Camera')
        focal = info.get('FocalLength', '?')
        f_stop = info.get('FNumber', '?')
        iso = info.get('ISOSpeedRatings', '?')
        param_text = f"{cam}  |  {focal}mm  f/{f_stop}  ISO {iso}"
        
        # 创建 20% 留白的白色底板
        border_h = int(h * 0.20)
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        
        # 将主体贴入底板 (如果是抠图后的透明图，使用 mask 保持透明)
        if img.mode == 'RGBA':
            new_img.paste(img, (0, 0), mask=img.split()[3])
        else:
            new_img.paste(img, (0, 0))
            
        # 绘制品牌文字与参数
        draw = ImageDraw.Draw(new_img)
        draw.text((int(w*0.05), h + int(border_h*0.25)), brand_tag, fill=(0, 0, 0))
        draw.text((int(w*0.05), h + int(border_h*0.55)), param_text, fill=(130, 130, 130))
        img = new_img
        
    return img

# --- UI 界面布局 ---
st.set_page_config(page_title="妮情摄影工坊 Pro", layout="wide")
st.title("🕯️ 妮情摄影工坊 | NIQING STUDIO")

# 侧边栏：功能开关
st.sidebar.header("🎛️ 艺术创作面板")
mode = st.sidebar.selectbox("影调选择", ["原色风格", "自动增强", "徕卡黑白"])
ai_remove_bg = st.sidebar.toggle("启用 AI 自动抠图", value=False)
add_border = st.sidebar.toggle("启用妮情专属边框", value=True)

# 文件上传
uploaded_files = st.file_uploader("导入摄影素材", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# --- 这里的缩进必须完全对齐 ---
if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            # 执行 AI 处理
            with st.spinner(f'AI 正在处理: {file.name}...'):
                processed_img = process_image(file, mode, add_border, ai_remove_bg)
            
            # 实时预览
            with cols[idx % 3]:
                st.image(processed_img, use_container_width=True)
            
            # 存入下载压缩包
            img_byte_arr = io.BytesIO()
            # 统一转为 RGB 保存为高质量 JPEG
            save_img = processed_img.convert("RGB")
            save_img.save(img_byte_arr, format='JPEG', quality=95)
            zip_file.writestr(f"NIQING_{file.name}.jpg", img_byte_arr.getvalue())

    st.divider()
    st.balloons()
    st.download_button(
        label="📥 导出妮情 AI 作品集", 
        data=zip_buffer.getvalue(), 
        file_name="NIQING_STUDIO_WORKS.zip"
    )

# 👈 注意这个 else 必须和上面的 if uploaded_files 对齐
else:
    st.info("👋 你好，妮情。请在此导入你的影像，开启基于 AI 的艺术化后期流程。")
