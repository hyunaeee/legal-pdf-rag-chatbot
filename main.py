import streamlit as st
import uuid
import tempfile
import os
import time
from config import MAX_MESSAGES_BEFORE_DELETION
from document_loader import load_pdf
from embedding import create_vectorstore
from chat_model import setup_chat_model, create_rag_chain
from ui_components import reset_chat, setup_sidebar, display_chat_messages, get_user_input
def main():
    st.title("QA Engine 1팀 챗봇")
    if "id" not in st.session_state:
        st.session_state.id = uuid.uuid4()
        st.session_state.file_cache = {}
    if "messages" not in st.session_state:
        st.session_state.messages = []
    uploaded_file = setup_sidebar()
    if uploaded_file:
        try:
            file_key = f"{st.session_state.id}-{uploaded_file.name}"
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.sidebar.write("Indexing your document...")
                if file_key not in st.session_state.get('file_cache', {}):
                    pages = load_pdf(file_path)
                    retriever = create_vectorstore(pages)
                    chat, contextualize_q_prompt, qa_prompt = setup_chat_model()
                    rag_chain = create_rag_chain(chat, retriever, contextualize_q_prompt, qa_prompt)
                    st.session_state.file_cache[file_key] = rag_chain
                st.sidebar.success("Ready to Chat!")
        except Exception as e:
            st.sidebar.error(f"An error occurred: {e}")
            st.stop()
    display_chat_messages()
    if prompt := get_user_input():
        if len(st.session_state.messages) >= MAX_MESSAGES_BEFORE_DELETION:
            del st.session_state.messages[:2]
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            if uploaded_file:
                rag_chain = st.session_state.file_cache[file_key]
                result = rag_chain.invoke({"input": prompt, "chat_history": st.session_state.messages})
                with st.expander("Evidence context"):
                    st.write(result["context"])
                for chunk in result["answer"].split(" "):
                    full_response += chunk + " "
                    time.sleep(0.2)
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            else:
                full_response = "Please upload a PDF file first."
                message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
if __name__ == "__main__":
    main()