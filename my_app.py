import streamlit as st
import threading
import time
from datetime import datetime

# ==========================================
# 核心逻辑层：处理任务与 API
# ==========================================
class NiqingEngine:
    def __init__(self):
        # 模拟用户信息，未来可对接数据库
        if 'user_data' not in st.session_state:
            st.session_state.user_data = {"balance": 100, "is_pro": False}
        
        # 任务队列状态
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []

    def check_balance(self, cost=1):
        """付费逻辑钩子"""
        return st.session_state.user_data["balance"] >= cost

    def process_video_task(self, prompt, config):
        """模拟异步视频生成过程"""
        # 扣费逻辑预留
        st.session_state.user_data["balance"] -= 5 
        
        # 模拟生成耗时
        time.sleep(10) # 假设生成需要10秒
        st.session_state.tasks.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "prompt": prompt,
            "status": "Completed ✅",
            "config": config
        })

# ==========================================
# UI 界面层：NIQING STUDIO
# ==========================================
def main():
    st.set_page_config(page_title="NIQING STUDIO · 妮情工坊", layout="wide")
    engine = NiqingEngine()

    # --- 侧边栏：品牌与参数控制 ---
    with st.sidebar:
        st.title("NIQING STUDIO")
        st.caption("深海创意工坊 · v2.0")
        st.divider()
        
        st.subheader("🎬 电影级参数预设")
        lens = st.selectbox("镜头焦段", ["85mm (人像特写)", "35mm (人文叙事)", "24mm (广角冲击)"])
        lighting = st.multiselect("光影氛围", ["Backlight (逆光轮廓)", "Teal & Orange (青橙调)", "Soft Diffusion (柔光)", "Japanese Film (日系胶片)"], default=["Backlight (逆光轮廓)"])
        
        st.divider()
        st.metric("剩余额度 (Tokens)", st.session_state.user_data["balance"])
        
        if st.button("升级 Pro 会员", use_container_width=True):
            st.balloons()
            st.success("即将开启商业闭环...")

    # --- 主界面：生成区域 ---
    st.header("NQ 生成工作坊")
    
    col1, col2 = st.columns([2, 1])

    with col1:
        prompt = st.text_area("输入创意描述 (Prompt)", placeholder="例如：一个在深海中发光的少女，85mm，逆光轮廓...")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 开始生成视频 (消耗 5 Tokens)", use_container_width=True):
                if engine.check_balance(5):
                    config = {"lens": lens, "lighting": lighting}
                    # 开启线程异步处理，防止 UI 假死
                    thread = threading.Thread(target=engine.process_video_task, args=(prompt, config))
                    thread.start()
                    st.toast("任务已提交，正在后台生成中...", icon="🎬")
                else:
                    st.error("余额不足，请充值！")
        
        with c2:
            st.button("📸 纯净图像生成", use_container_width=True, type="secondary")

    with col2:
        st.subheader("⏳ 任务状态列表")
        if not st.session_state.tasks:
            st.info("暂无正在进行或已完成的任务")
        else:
            for task in reversed(st.session_state.tasks):
                with st.expander(f"任务 {task['time']} - {task['status']}"):
                    st.write(f"**提示词:** {task['prompt']}")
                    st.json(task['config'])

    # --- 底部：实时渲染监控 ---
    st.divider()
    if any(t['status'] == "Processing..." for t in st.session_state.tasks):
        with st.status("正在渲染视频...", expanded=True):
            st.write("正在连接即梦 API...")
            st.write("注入电影感参数...")
            st.write("视频帧插值中...")

if __name__ == "__main__":
    main()
    
    st.divider()
    st.info("💡 提示：NQ生成工作坊已准备就绪。")
