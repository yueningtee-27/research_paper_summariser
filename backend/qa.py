from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_community.document_loaders import PyMuPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from summarizer import extract_pdf_text
from langchain_core.callbacks import UsageMetadataCallbackHandler

import os

# -------------------------------
# 1. Initialize LLM and embeddings
# -------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
embeddings = OpenAIEmbeddings()
callback = UsageMetadataCallbackHandler()

# -------------------------------
# 2. Load PDF, chunk, create vectorstore
# -------------------------------
def create_vectorstore_from_pdf(pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> FAISS:
    # Reuse your existing PDF extraction
    text = extract_pdf_text(pdf_path)

    # Chunk the text for RAG
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)

    # Create vectorstore
    vectorstore = FAISS.from_texts(chunks, embeddings)
    return vectorstore
# -------------------------------
# 3. Define prompt template
# -------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful research assistant."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])
chain = prompt | llm

# -------------------------------
# 4. Setup session-based history
# -------------------------------
_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]

conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history"
)

# -------------------------------
# 5. RAG-enabled Q&A function
# -------------------------------
def answer_question_with_rag(session_id: str, vectorstore: FAISS, question: str, top_k=5):
    # 1. Retrieve most relevant chunks from vectorstore
    docs = vectorstore.similarity_search(question, k=top_k)
    context_text = "\n\n".join([doc.page_content if hasattr(doc, 'page_content') else doc for doc in docs])
    
    # 2. Combine retrieved context with user question
    user_input = (
        f"Here are the relevant parts of the research paper:\n\n"
        f"{context_text}\n\n"
        f"Question: {question}"
    )
    
    # 3. Invoke conversation with session memory
    result = conversation.invoke(
        {"question": user_input},
        config={"configurable": {"session_id": session_id},
            "callbacks": [callback]}
    )

    print("QnA token usage metadata: ", callback.usage_metadata)
    
    return result.content

# -------------------------------
# Example usage:
# -------------------------------
# 1. Load and chunk PDF
# chunks = load_and_chunk_pdf("my_paper.pdf")

# 2. Create vector store
# vectorstore = create_vectorstore(chunks)

# 3. Ask questions
# session = "user123"
# response1 = answer_question_with_rag(session, vectorstore, "What is the main contribution of the paper?")
# print(response1)

# response2 = answer_question_with_rag(session, vectorstore, "How was the model trained?")
# print(response2)
