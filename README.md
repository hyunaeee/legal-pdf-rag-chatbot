# Legal PDF RAG Chatbot 📚⚖️

법률 관련 PDF 문서를 분석하고 질문에 답변해주는 RAG(Retrieval-Augmented Generation) 기반 챗봇입니다.

## 🌟 주요 기능

- **PDF 문서 업로드**: 법률 관련 PDF 파일을 업로드하여 분석
- ![image](https://github.com/user-attachments/assets/fdcb1085-cf0b-4e1f-95e3-9b414d0e3626)
- **지능형 검색**: 업로드된 문서에서 관련 내용을 정확하게 검색
- **문맥 인식**: 이전 대화 내용을 고려한 답변 생성
- **증거 제시**: 답변과 함께 참고한 문서 부분을 제공
- ![image](https://github.com/user-attachments/assets/6b900f73-1277-4c3f-b62c-58ab8affb574)
- **대화형 인터페이스**: Streamlit 기반의 사용자 친화적인 웹 인터페이스
- ![image](https://github.com/user-attachments/assets/8a587818-e118-454c-86eb-ea1b4d503cec)



## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **LLM**: Upstage Solar API
- **Vector Database**: Chroma
- **Embeddings**: Upstage Solar Embedding
- **Framework**: LangChain
- **Document Processing**: PyPDF

## 📋 필요 조건

- Python 3.8+
- Upstage API Key

## ⚙️ 설치 및 설정

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/legal-pdf-rag-chatbot.git
cd legal-pdf-rag-chatbot
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```
UPSTAGE_API_KEY=your_upstage_api_key_here
```

## 🚀 실행 방법

```bash
streamlit run main.py
```

브라우저에서 `http://localhost:8501`로 접속하여 애플리케이션을 사용할 수 있습니다.

## 📖 사용법

1. **PDF 업로드**: 사이드바에서 법률 관련 PDF 파일을 업로드합니다.
2. **문서 처리 대기**: 업로드된 문서가 인덱싱될 때까지 잠시 기다립니다.
3. **질문하기**: 채팅창에 문서와 관련된 질문을 입력합니다.
4. **답변 확인**: AI가 문서를 바탕으로 답변하며, 참고한 증거도 함께 제공됩니다.

## 📂 프로젝트 구조

```
legal-pdf-rag-chatbot/
├── main.py                 # 메인 애플리케이션
├── chat_model.py          # 채팅 모델 및 RAG 체인 설정
├── document_loader.py     # PDF 문서 로딩
├── embedding.py           # 벡터 저장소 생성
├── ui_components.py       # UI 컴포넌트
├── config.py             # 설정 파일
├── requirements.txt      # 패키지 의존성
├── .env                  # 환경 변수 (생성 필요)
└── README.md            # 프로젝트 설명서
```

## ⚡ 주요 특징

### 지능형 문맥 인식
- 이전 대화 내용을 고려하여 더 정확한 답변 제공
- 대화 히스토리 기반 질문 재구성

### 효율적인 메모리 관리
- 일정 개수 이상의 메시지 자동 삭제로 메모리 최적화
- 파일별 캐싱으로 재처리 시간 단축

### 사용자 친화적 인터페이스
- 직관적인 Streamlit 기반 웹 인터페이스
- 실시간 타이핑 효과로 자연스러운 대화 경험
- 증거 문서 확장 가능한 뷰

## 🔧 설정 옵션

`config.py`에서 다음 설정을 조정할 수 있습니다:

- `MAX_MESSAGES_BEFORE_DELETION`: 메모리 관리를 위한 최대 메시지 수 (기본값: 4)

## 📝 요구사항 파일 (requirements.txt)

```
streamlit
langchain
langchain-community
langchain-chroma
langchain-upstage
pypdf
python-dotenv
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**⚠️ 주의사항**: 이 도구는 법률 자문을 대체하지 않습니다. 중요한 법적 결정을 내리기 전에 반드시 전문 변호사와 상담하시기 바랍니다.
