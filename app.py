import streamlit as st
import os
import pdfplumber  # 替换了 PyPDF2
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# --- 页面基础配置 ---
st.set_page_config(page_title="Global AI HR", page_icon="🌍", layout="wide")

# --- API 设置 ---
with st.sidebar:
    st.title("🌍 设置 / Settings")
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ Key Loaded")
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

# --- 主标题 ---
st.title("双语 AI 招聘系统 (Bilingual HR System)")
st.caption("支持中文简历 & English Resume | 智能识别语言")

# 初始化状态
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! I am your AI Interviewer. Please upload a resume to start. \n你好，我是AI面试官，请上传简历开始。"}]
if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""

# ==========================================
# 模块 1: 简历解析 (核心升级部分)
# ==========================================
with st.expander("📄 Step 1: Upload Resume (PDF)", expanded=True):
    jd_text = st.text_area("Job Description (职位描述)", height=100, value="岗位：高级咨询顾问 / Senior Consultant\n要求：\n1. Fluent in English and Chinese.\n2. Strong logic and data analysis skills.\n3. Experience in top-tier consulting firms.")
    
    uploaded_file = st.file_uploader("Upload PDF (CN/EN)", type="pdf")

    if uploaded_file:
        try:
            # 使用 pdfplumber 进行更精准的解析
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    # extract_text 对双栏排版支持更好
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            st.session_state["resume_text"] = text
            st.success(f"解析成功 / Parsed Successfully! (Length: {len(text)} chars)")

            # AI 评分按钮
            if api_key and st.button("开始双语评估 / Start Assessment"):
                with st.spinner("AI is analyzing (Bilingual Mode)..."):
                    chat = ChatOpenAI(model_name="gpt-4o", temperature=0)
                    
                    # --- 关键修改：双语提示词 ---
                    prompt = f"""
                    Role: You are an expert Global HR Partner.
                    Task: Analyze the candidate's resume based on the Job Description (JD).
                    
                    Input Data:
                    1. JD: {jd_text}
                    2. Resume Content: {st.session_state["resume_text"]}
                    
                    Instructions:
                    1. The resume can be in Chinese or English. You must understand both perfectly.
                    2. **Output Language**: Please output the report in **Chinese (中文)** so the local HR team can read it easily. (Even if the resume is English).
                    3. Analysis Dimensions:
                       - Match Score (0-100)
                       - Education & Background Check
                       - Key Strengths (3 points)
                       - Potential Risks
                       - Language Ability Assessment (Check if they match the JD language requirements)
                    
                    Please format the output using Markdown.
                    """
                    
                    response = chat.invoke([HumanMessage(content=prompt)])
                    st.markdown("### 📊 智能评估报告")
                    st.markdown(response.content)

        except Exception as e:
            st.error(f"Error reading PDF: {e}")

# ==========================================
# 模块 2: 双语模拟面试 (Chat)
# ==========================================
st.divider()
st.subheader("🎙️ Step 2: AI Interview (Auto-Switch Language)")

# 显示历史
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 输入框
if user_input := st.chat_input("Type your answer (CN or EN)..."):
    if not api_key:
        st.warning("Please enter API Key first.")
    else:
        # 1. 用户消息上屏
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # 2. AI 生成回复
        with st.spinner("Thinking..."):
            chat_interview = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
            
            # --- 关键修改：动态语言适配 ---
            system_instruction = f"""
            You are a professional Interviewer.
            
            Context:
            - Job: {jd_text}
            - Candidate Resume: {st.session_state.get('resume_text', 'Not uploaded')}
            
            **Crucial Language Rule**: 
            - If the user speaks **Chinese**, reply in **Chinese**.
            - If the user speaks **English**, reply in **English**.
            - If the user mixes languages, reply in the language that maintains the most professional tone for the context.
            
            Goal:
            - Ask follow-up questions based on the resume (STAR method).
            - Keep the conversation professional but engaging.
            - Ask one question at a time.
            """
            
            # 构建对话历史
            conversation = [SystemMessage(content=system_instruction)]
            for msg in st.session_state.messages[-8:]: # 只保留最近8条
                if msg["role"] == "user":
                    conversation.append(HumanMessage(content=msg["content"]))
                else:
                    conversation.append(SystemMessage(content=msg["content"]))
            
            ai_reply = chat_interview.invoke(conversation).content
            
            # 3. AI 回复上屏
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.chat_message("assistant").write(ai_reply)
