from openai import OpenAI
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def extract_pdf_text(pdf_path):
    print("[backend] Extracting text from PDF...")
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        print(f"[backend] PDF has {len(reader.pages)} pages")
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        print(f"[backend] Finished extraction ({len(text)} chars)")
    return text

def summarize_paper_text(paper_text, summary_type="detailed"):
    print(f"[backend] Starting summarization ({len(paper_text)} chars, type={summary_type})")
    system_prompt = (
        "You are an expert scientific summarizer. "
        "You will read the entire research paper and produce a thorough, factual, structured summary. "
        "Be precise and avoid hallucinations."
    )

    if summary_type == "short":
        user_prompt = (
            "Provide a concise summary (3–5 bullet points or one paragraph) "
            "highlighting the paper’s objectives, methods, and findings.\n\n"
            f"Paper text:\n{paper_text}"
        )
    else:
        user_prompt = (
            "Here is the full text of a research paper:\n\n"
            f"{paper_text}\n\n"
            "Please produce a detailed summary that captures all key ideas, results, and implications."
            "formatted in Markdown.\n\n"
        )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
    )

    # 🔍 Extract usage info
    usage = getattr(response, "usage", None)
    if usage:
        print(f"[🧮] Token usage — Prompt: {usage.prompt_tokens}, "
              f"Completion: {usage.completion_tokens}, "
              f"Total: {usage.total_tokens}")
    else:
        print("[⚠️] Token usage info not available.")

    return response.choices[0].message.content
