import streamlit as st
import os
import pdfplumber
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# ==========================================
# 1. 页面基础配置
# ==========================================
st.set_page_config(
    page_title="Gemini AI 招聘助手", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. 侧边栏：API Key 配置
# ==========================================
with st.sidebar:
    st.header("⚡ 设置 / Settings")
    st.markdown("本系统使用 **Google Gemini 1.5 Flash** 模型，速度快且免费额度高。")
    
    # 优先读取环境变量，否则让用户输入
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ 系统密钥已加载")
    else:
        api_key = st.text_input("请输入 Google API Key", type="password", placeholder="AIza开头...")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            st.success("✅ 密钥已保存")
        else:
            st.warning("请先输入 API Key 才能使用。")
            st.markdown("[👉 点击这里免费申请 Google Key](https://aistudio.google.com/app/apikey)")

# ==========================================
# 3. 初始化 Session State (状态管理)
# ==========================================
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "你好！我是基于 Gemini 的 AI 面试官。请上传简历，我们可以开始模拟面试。"}]
if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""

# ==========================================
# 4. 主界面标题
# ==========================================
st.title("⚡ Gemini 智能招聘系统")
st.caption("Powered by Google Gemini 1.5 Flash | 支持中英双语简历解析")

# ==========================================
# 模块 A: 简历解析与智能评分
# ==========================================
with st.expander("📄 第一步：简历上传与评估 (Resume Analysis)", expanded=True):
    col1, col2 = st.columns([1, 1])
    
    with col1:
        jd_text = st.text_area("请输入职位描述 (JD)", height=200, value="岗位：高级项目经理\n要求：\n1. 5年以上软件行业经验。\n2. 精通敏捷开发 (Agile)。\n3. 英语流利，能作为工作语言。\n4. PMP 证书优先。")
    
    with col2:
        uploaded_file = st.file_uploader("上传简历 (支持 PDF)", type="pdf")
        
        if uploaded_file:
            try:
                # 使用 pdfplumber 解析 (对双栏排版更友好)
                with pdfplumber.open(uploaded_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                
                st.session_state["resume_text"] = text
                st.success(f"✅ 简历解析成功 (约 {len(text)} 字符)")
                
                # 分析按钮
                if st.button("🚀 开始 AI 评估"):
                    if not api_key:
                        st.error("请先在左侧输入 Google API Key")
                    else:
                        with st.spinner("Gemini 正在极速分析中..."):
                            # 初始化 Gemini 模型
                            llm = ChatGoogleGenerativeAI(
                                model="gemini-1.5-flash",
                                temperature=0.2, # 低温度，保证评分严谨
                                convert_system_message_to_human=True # 兼容性设置
                            )
                            
                            prompt = f"""
                            你是一位资深的人力资源专家。请基于以下 JD 对简历进行详细评估。
                            
                            【职位描述 JD】:
                            {jd_text}
                            
                            【候选人简历】:
                            {st.session_state["resume_text"]}
                            
                            【任务要求】:
                            1. 无论简历是中文还是英文，请**必须使用中文**输出报告。
                            2. 请使用 Markdown 格式。
                            3. 输出包含以下模块：
                               - 📊 **匹配度得分** (0-100分)
                               - ✅ **核心优势** (列出3点)
                               - ⚠️ **潜在风险/红旗** (Red Flags)
                               - 🗣️ **语言能力评估** (针对 JD 要求的语言)
                               - 💡 **面试建议** (2个建议追问的问题)
                            """
                            
                            response = llm.invoke([HumanMessage(content=prompt)])
                            st.markdown("### 📊 评估报告")
                            st.markdown(response.content)
                            
            except Exception as e:
                st.error(f"解析失败: {e}")

# ==========================================
# 模块 B: AI 模拟面试 (Chat)
# ==========================================
st.divider()
st.subheader("🎙️ 第二步：AI 模拟面试 (Interactive Interview)")

# 1. 展示聊天记录
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 2. 用户输入
if user_input := st.chat_input("请输入你的回答 (支持中英文)..."):
    if not api_key:
        st.warning("请先配置 API Key")
    else:
        # 用户消息上屏
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        
        # AI 思考与回复
        with st.spinner("面试官正在记录..."):
            try:
                # 初始化聊天模型 (稍微提高温度，增加对话灵活性)
                chat_llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.6,
                    convert_system_message_to_human=True
                )
                
                # 构建 Prompt
                system_prompt = f"""
                You are a professional Interviewer.
                Current Job: {jd_text}
                Candidate Resume Content: {st.session_state.get('resume_text', 'No resume uploaded yet')}
                
                **Rules**:
                1. If user speaks Chinese, reply in Chinese.
                2. If user speaks English, reply in English.
                3. Ask **ONE** question at a time.
                4. Use the STAR method to dig into details based on the resume.
                5. Be professional but slightly challenging.
                """
                
                # 构建消息历史 (Gemini 对 SystemMessage 的处理方式不同，我们将其作为第一条 HumanMessage 的上下文前缀，或者使用 LangChain 的自动转换)
                messages = [SystemMessage(content=system_prompt)]
                
                # 仅保留最近 10 条对话，防止 Token 溢出
                for msg in st.session_state.messages[-10:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        # LangChain 中 AI 的回复对应 AIMessage，这里为了简单直接用 System 模拟或直接由库处理
                        # 在 ChatGoogleGenerativeAI 中，最好不要手动插入 AIMessage 类，而是依靠 LangChain 的 invoke 结构
                        # 简单起见，我们只把用户的历史发给它，或者使用 memory chain。
                        # 为了最简单的实现：
                        pass 
                
                # ⚠️ 修正：为了让 Gemini 记住上下文，我们需要把历史对话转换成它能理解的格式
                # 最简单的方法是将历史记录拼接成一个长 Prompt 发送（无状态模式），或者使用 LangChain 的 Memory
                # 这里采用“拼接法”确保稳定性：
                
                full_conversation = system_prompt + "\n\nConversation History:\n"
                for msg in st.session_state.messages:
                    role_label = "Candidate" if msg["role"] == "user" else "Interviewer"
                    full_conversation += f"{role_label}: {msg['content']}\n"
                
                full_conversation += "Interviewer (You):"
                
                ai_response = chat_llm.invoke([HumanMessage(content=full_conversation)])
                
                # AI 回复上屏
                st.session_state.messages.append({"role": "assistant", "content": ai_response.content})
                st.chat_message("assistant").write(ai_respons
