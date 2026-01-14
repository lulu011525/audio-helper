import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

st.set_page_config(page_title="AI 影音摘要", page_icon="🎙️")

st.title("🎙️ AI 影音轉摘要助手")

with st.sidebar:
    st.header("🔑 設定")
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    api_key = st.text_input("Google API Key", value=st.session_state.api_key, type="password")
    if api_key:
        st.session_state.api_key = api_key
    st.info("請輸入 Google API Key 才能使用。")

if not st.session_state.api_key:
    st.warning("👈 請先在左側輸入 API Key")
else:
    genai.configure(api_key=st.session_state.api_key)
    uploaded_file = st.file_uploader("上傳檔案", type=["mp3", "wav", "mp4", "m4a"])
    
    if uploaded_file and st.button("🚀 開始分析"):
        with st.spinner("AI 正在處理中... (請耐心等待)"):
            try:
                # 存暫存檔
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                # 上傳與分析
                video_file = genai.upload_file(path=tmp_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)

                if video_file.state.name == "FAILED":
                    st.error("檔案處理失敗")
                else:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res = model.generate_content([video_file, "請用繁體中文生成：1.標題 2.摘要 3.待辦"])
                    st.markdown(res.text)
                
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"錯誤：{e}")
