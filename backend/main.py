from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile, shutil, os, time
from summarizer import extract_pdf_text, summarize_paper_text
from qa import answer_question
from ma_summarizer.agents import GrobidSectionAgent, SectionSummaryAgent, SummaryAggregatorAgent, summarize_sections_parallel, SummaryHighlighterAgent
from ma_summarizer.highlight_agent import HighlightAgent
app = FastAPI(title="PDF Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# test solution: store uplaoded paper text in memory 
DOCUMENT_STORE = {}

@app.post("/summarize")
async def summarize_api(pdf: UploadFile = File(...), summary_type: str = Form("detailed")):
    start_time = time.time()
    print("\n[🟢] Received request")
    print(f"Filename to store in DOCUMENT_STORE as: {pdf.filename}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(pdf.file, tmp)
        pdf_path = tmp.name
    print(f"[📄] Saved PDF temporarily: {pdf_path}")

    try:
        # 1️⃣ Extract text
        t1 = time.time()
        print("[🔍] Extracting text from PDF...")
        paper_text = extract_pdf_text(pdf_path)
        print(f"[✅] Text extracted ({len(paper_text)} chars) in {time.time() - t1:.2f}s")

        # save text to store (keyed by filename)
        DOCUMENT_STORE[pdf.filename] = paper_text
        print(f"Filename stored in DOCUMENT_STORE as: {pdf.filename}")

        # 2️⃣ Truncate long text
        paper_text = paper_text[:400000]
        print(f"[✂️] Text truncated to {len(paper_text)} chars")

        # 3️⃣ Generate summary
        t2 = time.time()
        print("[🤖] Sending text to OpenAI model...")
        summary = summarize_paper_text(paper_text, summary_type)
        print(f"[✅] OpenAI summarization done in {time.time() - t2:.2f}s")

        print(f"[🏁] Total time: {time.time() - start_time:.2f}s\n")
        return JSONResponse({
            "summary": summary,
            "filename": pdf.filename})

    except Exception as e:
        print(f"[❌] Error: {e}")
        return JSONResponse({"summary": f"Error: {str(e)}"}, status_code=500)

    finally:
        os.remove(pdf_path)
        print(f"[🧹] Temporary file deleted: {pdf_path}")


@app.post("/ask")
async def ask_question(filename: str = Form(...), question: str = Form(...)):
    """Answer a question about a previously uploaded paper."""
    if filename not in DOCUMENT_STORE: 
        return JSONResponse({"error": "File not found. Upload and summarize first"}, status_code = 400)

    context_text = DOCUMENT_STORE[filename]
    answer = answer_question(context_text, question)
    return JSONResponse({"answer": answer})


grobid_agent = GrobidSectionAgent()
section_agent = SectionSummaryAgent()
aggregator_agent = SummaryAggregatorAgent()
highlight_agent = HighlightAgent()

@app.post("/multi-agent-summarize")
async def multi_agent_summarize(pdf: UploadFile = File(...)):
    start_time = time.time()
    print("\n[🟢] Received request")
    # Save uploaded PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(pdf.file, tmp)
        pdf_path = tmp.name
        print(f"[📄] Saved PDF temporarily: {pdf_path}")

    # 1. extract sections 
    t1 = time.time()
    sections = grobid_agent.extract_sections(pdf_path)
    print(f"[✅] Sections extracted ({len(sections)} sections) in {time.time() - t1:.2f}s")

    # 2. Summarize each section 
    t2 = time.time()
    section_summaries = await summarize_sections_parallel(sections, section_agent)
    # for s in sections:
    #     print(f"[🤖] Summarizing section: {s['heading']}...")
    #     summary = section_agent.summarize(s['heading'], s['content'])
    #     section_summaries.append({"section": s['heading'], "summary": summary})
    print(f"[✅] Section summarization done in {time.time() - t2:.2f}s")



    # 3. Aggregate summaries
    t3 = time.time()
    final_summary = aggregator_agent.combine(section_summaries)
    print(f"[✅] Final summarization done in {time.time() - t3:.2f}s")

    # # 4. Compute sentence-level highlights 
    # t4 = time.time()
    # highlighter = SummaryHighlighterAgent()
    # highlights = highlighter.link_summary_to_sources(
    #     final_summary = final_summary, 
    #     all_chunks = [chunk for sec in sections for chunk in sec["chunks"]]
    # )
    # print(f"[✅] Highlight mapping done in {time.time() - t4:.2f}s")


    return JSONResponse({
        "summary": final_summary, 
        "sections": section_summaries,
        # "highlights": highlights,
        "ma_filename": pdf.filename})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
    