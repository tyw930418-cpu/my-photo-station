import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from PIL.ExifTags import TAGS
import io
import zipfile

# --- 核心美化函数 ---
def process_image(file, mode, add_border=True):
    # 1. 打开原图并提取参数 (在处理前抓取 EXIF，防止丢失)
    raw_img = Image.open(file)
    exif_data = raw_img._getexif()
    info = {TAGS.get(tag, tag): value for tag, value in exif_data.items()} if exif_data else {}
    
    # 自动修正方向 (解决手机或单反竖拍照片横过来的问题)
    img = ImageOps.exif_transpose(raw_img)
    
    # 2. 模式选择 (滤镜算法)
    if mode == "徕卡黑白":
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.4) # 加强对比度，更有德系味
    elif mode == "自动增强":
        img = ImageEnhance.Color(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = ImageEnhance.Sharpness(img).enhance(1.1)

    # 3. 拍立得风格水印边框
    if add_border:
        w, h = img.size
        # 准备相机参数文字
        cam_model = info.get('Model', 'Camera')
        focal = info.get('FocalLength', '?')
        f_stop = info.get('FNumber', '?')
        iso = info.get('ISOSpeedRatings', '?')
        param_text = f"{cam_model}  {focal}mm  f/{f_stop}  ISO {iso}"
        
        # 创建白边底板 (底部留出 18% 的高度写字)
        border_h = int(h * 0.18)
        new_img = Image.new("RGB", (w, h + border_h), (255, 255, 255))
        new_img.paste(img, (0, 0))
        
        # 绘制文字
        draw = ImageDraw.Draw(new_img)
        # 文字位置：左对齐，留一点边距
        draw.text((int(w * 0.05), h + int(border_h * 0.3)), param_text, fill=(60, 60, 60))
        img = new_img

    return img

# --- UI 界面 ---
st.set_page_config(page_title="wutianlong 摄影助手", layout="wide")
st.title("🎨 wutianlong 全能摄影工作站")

# 侧边栏设置
st.sidebar.header("🎛️ 后期设置")
mode = st.sidebar.selectbox("选择滤镜风格", ["原图重命名", "自动增强", "徕卡黑白"])
add_border = st.sidebar.toggle("启用拍立得水印边框", value=True)

uploaded_files = st.sidebar.file_uploader("批量拖入摄影素材", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        cols = st.columns(3) # 网页预览分三列显示
        for idx, file in enumerate(uploaded_files):
            # 处理图片
            processed_img = process_image(file, mode, add_border)
            
            # 网页预览
            with cols[idx % 3]:
                st.image(processed_img, caption=f"已处理: {file.name}", use_container_width=True)
            
            # 保存到内存 ZIP
            img_byte_arr = io.BytesIO()
            processed_img.save(img_byte_arr, format='JPEG', quality=92)
            zip_file.writestr(f"PRO_{mode}_{file.name}", img_byte_arr.getvalue())

    st.divider()
    st.balloons() # 撒花！
    st.download_button(
        label="📥 一键打包下载成品",
        data=zip_buffer.getvalue(),
        file_name="wutianlong_works.zip",
        mime="application/zip"
    )
else:
    st.info("👋 你好 wutianlong！请在左侧侧边栏上传照片。建议开启‘拍立得边框’。")