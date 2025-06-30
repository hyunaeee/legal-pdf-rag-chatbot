import streamlit as st
import base64

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None

def display_pdf(file):
    st.markdown("### PDF Preview")
    base64_pdf = base64.b64encode(file.read()).decode("utf-8")
    pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="400" height="100%" type="application/pdf"
                        style="height:100vh; width:100%"
                    >
                    </iframe>"""
    st.markdown(pdf_display, unsafe_allow_html=True)

def setup_sidebar():
    with st.sidebar:
        st.header("서류를 업로드 하세요.")
        uploaded_file = st.file_uploader("`.pdf` 파일을 고르세요.", type="pdf")
    return uploaded_file

def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def get_user_input():
    return st.chat_input("Ask a question!")