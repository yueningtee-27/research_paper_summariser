import fitz  # PyMuPDF
from langchain_ollama import ChatOllama

# --------------------------
# Configuration
# --------------------------
PDF_PATH = "../papers/hospital_bed_capacity_planning.pdf"
OLLAMA_MODEL = "llama3.1:latest"
OLLAMA_BASE_URL = "http://localhost:11434"
TEMPERATURE = 0.05

# --------------------------
# 1. Load PDF text
# --------------------------
def load_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    doc.close()
    return full_text

# --------------------------
# 2. Initialize LLaMA 3.1
# --------------------------
llm = ChatOllama(
    model=OLLAMA_MODEL,
    temperature=TEMPERATURE,
    base_url=OLLAMA_BASE_URL,
    device="cuda"  # uses GPU if available
)

# --------------------------
# 3. Simple Q&A function
# --------------------------
def ask_pdf_question(pdf_text, question):
    prompt = f"""
You are an expert AI research assistant. Answer the question based on the content of this research paper.
Do not make up information. If the answer is not stated, say "Not stated in the paper."

Paper Content:
{pdf_text}

Question:
{question}
"""
    response = llm.invoke(prompt)
    return response if isinstance(response, str) else getattr(response, "content", str(response))

# --------------------------
# 4. Interactive Q&A loop
# --------------------------
if __name__ == "__main__":
    pdf_text = load_pdf_text(PDF_PATH)
    print(f"PDF loaded. Total words: {len(pdf_text.split())}\n")

    print("Ask questions about the paper. Type 'exit' to quit.")
    while True:
        user_q = input("\nQuestion: ")
        if user_q.lower() in ["exit", "quit"]:
            break
        answer = ask_pdf_question(pdf_text, user_q)
        print(f"\nAnswer:\n{answer}")



# review of run 
# Asked for a snippet of the paper -- terrible performance, mashed up information from references
