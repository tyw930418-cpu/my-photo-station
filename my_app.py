import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from PIL.ExifTags import TAGS
from rembg import remove
import io
import zipfile
import requests
import json

# --- 💡 核心：使用 Hugging Face 最新的路由地址 ---
API_URL = "https://router.huggingface.co/runwayml/stable-diffusion-v1-5"

def query_ai_art(prompt, hf_token):
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    try:
        # 增加超时处理，防止服务器长时间不响应
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        # 1. 如果服务器返回错误状态码 (如 503 加载中或 401 Token 错误)
        if response.status_code != 200:
            try:
                return response.json()
            except:
                return {"error": f"服务器响应异常，状态码: {response.status_code}"}

        # 2. 检查返回内容是否为空 (解决 Expecting value 报错的核心)
        if not response.content:
            return {"error": "服务器返回内容为空，模型可能正在初始化，请稍后重试。"}

        # 3. 正常逻辑：判断是图片还是 JSON 报错
        if "image" in response.headers.get("Content-Type", ""):
            return response.content
        else:
            return response.json()
            
    except requests.exceptions.Timeout:
        return {"error": "请求超时，云端模型加载较慢，请再试一次。"}
    except Exception as e:
        return {"error": f"网络请求异常: {str(e)}"}

# --- 核心美化函数 ---
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

# --- UI 界面 ---
import streamlit as st
st.markdown("""
    <style>
    /* 1. 整体背景美化：浅奶油色背景 */
    .stApp {
        background-color: #FFF9F5;
    }
    
    /* 2. 侧边栏美化：落日橙渐变 */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#FF9E7D, #FF6B6B);
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: bold;
    }

    /* 3. 标题美化：青春活力的橙红字体 */
    h1 {
        color: #FF5E3A;
        font-family: 'Helvetica Neue', sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    /* 4. 按钮美化：圆角多巴胺色 */
    .stButton>button {
        background-color: #FF8E53;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 25px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 142, 83, 0.3);
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
        transform: translateY(-2px);
    }

    /* 5. 卡片效果：让上传区和图片预览更有质感 */
    .stFileUploader, .stImage {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_stdio=True)

# --- 页面标题更新 ---
st.set_page_config(page_title="妮情 · 青春创意工坊", layout="wide")
st.title("🍓 妮情 · 青春创意工坊 | NIQING CREATIVE")
st.markdown("##### *用 AI 捕捉那一抹活跃的色彩*")

# --- 模式 A：影像后期 (确保这一行在最左边) ---
if app_mode == "影像后期":
    mode = st.sidebar.selectbox("影调选择", ["原色风格", "自动增强", "徕卡黑白"])
    ai_remove_bg = st.sidebar.toggle("启用 AI 自动抠图", value=False)
    add_border = st.sidebar.toggle("启用妮情专属边框", value=True)
    
    uploaded_files = st.file_uploader("导入摄影素材", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files:
        # 这里是处理上传图片的逻辑...
        # (确保这里的代码比上面的 if 往右缩进 4 个空格)
        st.write("正在处理中...") 

# --- 模式 B：AI 文生图 (这一行必须和上面的 if app_mode 对齐) ---
elif app_mode == "AI 文生图":
    hf_token = st.text_input("输入你的 Hugging Face Token", type="password")
    prompt = st.text_area("描述你想要的画面")
    
    if st.button("开始梦境生成"):
        # 这里是 AI 生成逻辑...
        st.write("梦境构思中...")
                        
                        buf = io.BytesIO()
                        final_art.save(buf, format="JPEG")
                        st.download_button("💾 保存这张 AI 作品", data=buf.getvalue(), file_name="NIQING_AI_ART.jpg")
                    except Exception as e:
                        st.error(f"❌ 图片解析失败: {e}")
                
                elif isinstance(result, dict):
                    if "estimated_time" in result:
                        st.info(f"🕒 模型正在苏醒中... 预计还需 {int(result['estimated_time'])} 秒。请稍后重试。")
                    else:
                        st.error(f"❌ 提示: {result.get('error', '未知错误')}")
