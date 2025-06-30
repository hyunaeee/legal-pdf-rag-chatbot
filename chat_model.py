from langchain_upstage import ChatUpstage
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import UPSTAGE_API_KEY

def setup_chat_model():
    chat = ChatUpstage(upstage_api_key=UPSTAGE_API_KEY)
    
    contextualize_q_system_prompt = """이전 대화 내용과 최신 사용자 질문이 있을 때, 이 질문이 이전 대화 내용과 관련이 있을 수 있습니다. 
    이런 경우, 대화 내용을 알 필요 없이 독립적으로 이해할 수 있는 질문으로 바꾸세요. 
    질문에 답할 필요는 없고, 필요하다면 그저 다시 구성하거나 그대로 두세요."""

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    qa_system_prompt = """질문-답변 업무를 돕는 보조원입니다. 
    질문에 답하기 위해 검색된 내용을 사용하세요. 
    답을 모르면 모른다고 말하세요. 
    친절한 말투를 사용해서 말하세오.
    10줄 정도로 정리해서 말하세요.

    ## 답변 예시
    📍답변 내용: 
    📍증거(참고 부분): 

    {context}"""

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    return chat, contextualize_q_prompt, qa_prompt

def create_rag_chain(chat, retriever, contextualize_q_prompt, qa_prompt):
    history_aware_retriever = create_history_aware_retriever(chat, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(chat, qa_prompt)
    return create_retrieval_chain(history_aware_retriever, question_answer_chain)