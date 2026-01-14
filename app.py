import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# 1. 設定頁面資訊
st.set_page_config(
    page_title="AI 影音轉摘要助手", 
    page_icon="🎙️",
    layout="centered"
)

# 自訂 CSS：讓按鈕變漂亮，並隱藏右上角選單
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-weight: bold;
    }
    /* 主要按鈕樣式 */
    .stButton>button[kind="primary"] {
        background-color: #4F46E5;
        color: white;
    }
    /* 連結按鈕樣式 */
    a[href="https://aistudio.google.com/app/apikey"] {
        text-decoration: none;
        color: #4F46E5;
        font-weight: bold;
        border: 1px solid #4F46E5;
        padding: 8px 16px;
        border-radius: 8px;
        display: block;
        text-align: center;
        background-color: #EEF2FF;
    }
    a[href="https://aistudio.google.com/app/apikey"]:hover {
        background-color: #E0E7FF;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎙️ AI 影音轉摘要助手")
st.caption("上傳錄音檔或影片，AI 自動幫你生成重點摘要與待辦事項。")

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.header("🔑 啟動設定")
    
    st.markdown("### 第一步：取得通行證")
    st.markdown("本工具使用 Google Gemini AI，需要 API Key 才能運作 (個人使用通常免費)。")
    
    # 直接提供跳轉連結
    st.link_button("👉 點此免費申請 API Key", "https://aistudio.google.com/app/apikey", help="開啟 Google AI Studio")
    
    st.divider()
    
    st.markdown("### 第二步：貼上金鑰")
    
    # 初始化 session state
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
        
    api_key_input = st.text_input(
        "請將 AIza 開頭的字串貼在這裡：",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIzaSy..."
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input
        st.success("✅ 已輸入金鑰")
    else:
        st.warning("⚠️ 請先輸入金鑰")

# --- 主畫面邏輯 ---

# 如果還沒輸入 API Key，顯示新手教學
if not st.session_state.api_key:
    st.info("👈 請先在左側邊欄輸入 **Google API Key** 才能開始使用喔！")
    
    st.markdown("### 🐣 新手上路指南")
    st.markdown("""
    1. **點擊左側按鈕**：前往 Google AI Studio。
    2. **登入 Google 帳號**：點選左上角的 **"Get API key"**。
    3. **建立金鑰**：點擊 **"Create API key"**。
    4. **複製貼上**：將那串 `AIza` 開頭的亂碼複製，貼到左邊的輸入框。
    """)
    
else:
    # 已經有 Key 了，顯示上傳介面
    try:
        genai.configure(api_key=st.session_state.api_key)
        
        st.divider()
        st.subheader("📂 上傳檔案")
        
        uploaded_file = st.file_uploader(
            "支援 MP3, WAV, M4A, MP4 (建議 200MB 以內)", 
            type=["mp3", "wav", "mp4", "mov", "m4a"]
        )
        
        if uploaded_file is not None:
            # 顯示播放器預覽
            st.write("檔案預覽：")
            if uploaded_file.type.startswith('audio'):
                st.audio(uploaded_file)
            else:
                st.video(uploaded_file)
            
            # 分析按鈕
            if st.button("🚀 開始 AI 分析", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text('正在準備檔案...')
                    progress_bar.progress(10)
                    
                    # 處理暫存檔
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name

                    status_text.text('正在傳送給 Google AI (這可能需要一點時間)...')
                    progress_bar.progress(30)
                    
                    # 上傳檔案
                    video_file = genai.upload_file(path=tmp_file_path)
                    
                    # 等待檔案處理
                    while video_file.state.name == "PROCESSING":
                        status_text.text('Google 正在消化檔案內容...')
                        time.sleep(2)
                        video_file = genai.get_file(video_file.name)

                    if video_file.state.name == "FAILED":
                        st.error("❌ 檔案處理失敗，可能是格式不支援或檔案損毀。")
                    else:
                        status_text.text('AI 正在聆聽並撰寫筆記...')
                        progress_bar.progress(70)
                        
                        # 使用 Gemini 1.5 Flash
                        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                        
                        prompt = """
                        請擔任專業的會議記錄員，聆聽這個檔案，並用繁體中文生成以下報告：
                        1. 【標題】：給這段內容一個精準的標題
                        2. 【重點摘要】：請用列點方式整理出核心重點 (至少 3-5 點)
                        3. 【詳細內容】：針對每個重點進行補充說明
                        4. 【待辦事項/結論】：如果有下一步行動請列出
                        """
                        
                        response = model.generate_content([video_file, prompt])
                        
                        progress_bar.progress(100)
                        status_text.text('完成！')
                        
                        st.success("🎉 分析完成！")
                        st.markdown("### 📝 分析結果")
                        st.markdown(response.text)
                        
                        # 清理暫存檔
                        os.unlink(tmp_file_path)
                        
                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
                    st.info("如果是 API Key 錯誤，請檢查左側是否複製完整。")
                    
    except Exception as e:
        st.error(f"API 設定錯誤：{str(e)}")
