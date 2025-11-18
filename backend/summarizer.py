from openai import OpenAI
# from langchain_openai import ChatOpenAI 
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage
# from langchain_core.callbacks import UsageMetadataCallbackHandler
# import PyPDF2
# import fitz # PyMuPDF
from langchain_community.document_loaders import PyMuPDFLoader
from dotenv import load_dotenv

load_dotenv()

# client = OpenAI()

# To get token usage 
# handler = UsageMetadataCallbackHandler()

# Initialize langchain chat model 
llm = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0.05
)

def extract_pdf_text(pdf_path):
    print("[backend] Extracting text from PDF using LangChain PyMuPDFLoader...")

    # Load the PDF as LangChain documents (each page = one Document)
    loader = PyMuPDFLoader(pdf_path, mode="page")
    docs = loader.load()

    print(f"[backend] PDF has {len(docs)} pages")

    # Concatenate all pages
    text = "\n".join([d.page_content for d in docs])

    print(f"[backend] Finished extraction ({len(text)} chars)")
    return text

def summarize_paper_text(paper_text, summary_type="detailed", output_format="json"):
    print(f"[backend] Starting summarization ({len(paper_text)} chars, type={summary_type}, format={output_format})")
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
            f"""
            You are an expert machine learning research assistant. 


            Here is the full text of a research paper:

            {paper_text}

            Your task:
            Produce an extremely detailed summary of the paper with a strong focus on
            machine learning methods, data engineering, feature engineering, training
            pipeline, evaluation details, and detailed results.

            You MUST:
            - Follow the JSON schema as given below with pretty print.
            - Do NOT add or remove fields.
            - Do NOT rename fields.
            - Do NOT change the structure.
            - All values must be strings, except where arrays or objects are explicitly required.
            - If the paper does NOT explicitly mention a detail (e.g., optimizer, loss, version, batch size, hidden dimensions), you MUST write: "not specified".
            - Do NOT infer or guess under any circumstances.
            - Ensure the output is valid JSON.
            - Include version information for the model if present in the paper (e.g., v1, v2, “2023 version”). If not mentioned, set: "version": "not specified".

            Here is the REQUIRED JSON schema you MUST follow:

            {{
                "name_of_research_paper": "YoloV5",
                "objective": "... let the machine see light ...",
                "paper_metadata": {{
                    "title": "...",
                    "authors": ["..."],
                    "publication_venue": "...",
                    "publication_year": "number",
                    "doi": "...",
                    "research_domain": "string (e.g., Computer Vision, NLP, Machine Learning, etc.)",
                    "paper_type": "string (e.g., Empirical Study, Theoretical Analysis, Survey, etc.)"
                    }},
                "models": [
                    {{
                        "YoloV5": {{
                            "name": "YoloV5",
                            "version": "vX.X or not specified",
                            "input": "image...",
                            "output": "metadata...",
                            "machine_learning_category": "object detection",
                            "data_engineering": "...",
                            "feature_engineering": "...",
                            "model_training": {{
                                "optimizer": "...",
                                "loss_function": "...",
                                "learning_rate": "...",
                                "epochs": "...",
                                "batch_size": "...",
                                "training_pipeline": "...",
                                "early_stopping": "...",
                                "other_hyperparameters": "..."
                            }},
                            "model_evaluation": {{
                                "evaluation_metrics": "...",
                                "baselines_compared": "...",
                                "experimental_setup": "..."
                            }},
                            "model_results": "...",
                            "limitations_and_implications": "..."
                        }}
                    }}
                ],
                "key_findings": "..."
            }}

            You MUST produce only JSON as the output. No explanations, no commentary, no markdown.
            """
        )

    # utilise LangChain's structured messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = llm.invoke(messages)

    return response.content
    # return response.choices[0].message.content
