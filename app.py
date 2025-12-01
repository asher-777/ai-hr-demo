import streamlit as st
import os
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 页面配置
st.set_page_config(page_title="AI 招聘智能体", page_icon="🤖")

# --- 侧边栏：API 配置 ---
with st.sidebar:
    st.title("🤖 设置")
    # 优先从环境变量获取，如果没有则让用户输入
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ 系统密钥已自动加载")
    else:
        api_key = st.text_input("请输入 OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

# --- 主页面 ---
st.title("管理咨询 AI 招聘系统")
st.caption("支持端：电脑 Web / 手机 Mobile")

# 初始化 Session State (用于存储对话历史)
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "你好，我是AI面试官。请上传简历，或者我们可以直接开始对话。"}]
if "resume_content" not in st.session_state:
    st.session_state["resume_content"] = ""

# --- 模块 1: 简历上传 (折叠式，节省手机空间) ---
with st.expander("📄 第一步：上传简历 (PDF)", expanded=True):
    jd_text = st.text_area("职位描述 (JD)", height=100, value="岗位：高级咨询顾问\n要求：逻辑思维强，熟练使用Python，有MBB实习经验优先。")
    uploaded_file = st.file_uploader("点击上传 PDF", type="pdf")

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        st.session_state["resume_content"] = text
        st.success(f"简历解析成功！字数：{len(text)}")

        if api_key and st.button("开始 AI 评分"):
            with st.spinner("AI 正在分析..."):
                try:
                    chat = ChatOpenAI(model_name="gpt-4o", temperature=0)
                    prompt = f"""
                    你是一位咨询公司合伙人。请根据JD评估简历。
                    JD: {jd_text}
                    简历: {st.session_state["resume_content"]}
                    请输出：1.总分(0-100) 2.三个核心亮点 3.一个主要风险。用Markdown格式。
                    """
                    response = chat.invoke([HumanMessage(content=prompt)])
                    st.markdown(response.content)
                except Exception as e:
                    st.error(f"发生错误: {e}")

# --- 模块 2: 模拟面试 ---
st.divider()
st.subheader("🎙️ 第二步：AI 模拟面试")

# 显示历史消息
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 用户输入框
if user_input := st.chat_input("输入你的回答..."):
    if not api_key:
        st.warning("请先配置 API Key")
    else:
        # 1. 显示用户输入
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # 2. AI 生成回复
        with st.spinner("面试官正在思考..."):
            chat_interview = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
            
            # 构建上下文
            system_instruction = f"""
            你是一位严厉的咨询公司面试官。
            已知候选人简历信息: {st.session_state.get('resume_content', '未上传简历')}
            职位: {jd_text}
            
            要求：
            1. 简短有力，不要长篇大论（适合手机阅读）。
            2. 基于候选人的上一句回答进行深挖（追问细节）。
            3. 如果候选人逻辑不清，直接指出。
            """
            
            conversation = [SystemMessage(content=system_instruction)]
            # 仅保留最近 6 条对话以节省 Token 并保持上下文专注
            for msg in st.session_state.messages[-6:]: 
                if msg["role"] == "user":
                    conversation.append(HumanMessage(content=msg["content"]))
                else:
                    conversation.append(SystemMessage(content=msg["content"]))
            
            ai_reply = chat_interview.invoke(conversation).content
            
            # 3. 显示 AI 回复
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.chat_message("assistant").write(ai_reply)


