import requests
from lxml import etree
import re
import nltk
import asyncio
import numpy as np
from langchain_openai import OpenAIEmbeddings
from nltk.tokenize import sent_tokenize
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
# from spire.pdf import PdfDocument, PdfTextFinder, PdfTextFindOptions, TextFindParameter



# Ensure sentence tokenizer is available
nltk.download("punkt", quiet=True)


class GrobidSectionAgent:
    """
    Extracts high-level sections and text from a PDF using GROBID.
    GROBID provides normalized, structured text suitable for summarization.

    ✅ Now only returns section-level text — coordinates and per-sentence
       chunks are removed (PyMuPDF handles those separately).
    """

    def __init__(self, grobid_url: str = "http://localhost:8070/api/processFulltextDocument"):
        self.grobid_url = grobid_url

    def extract_sections(self, pdf_path: str):
        """
        Sends PDF to GROBID and returns flattened section list:
        [
            { "heading": "Introduction", "content": "Full section text..." },
            ...
        ]
        """
        with open(pdf_path, "rb") as f:
            response = requests.post(
                self.grobid_url,
                files={"input": f},
                data={"generateIDs": "true", "teiCoordinates": "true"}
            )
        response.raise_for_status()
        xml_text = response.text

        # Parse TEI XML into structured sections
        sections = self._parse_tei_xml(xml_text)

        # Flatten nested subsections
        flat_sections = self._flatten_sections(sections)

        # Return only those with actual content
        return [s for s in flat_sections if s["content"].strip()]

    def _parse_tei_xml(self, xml_text: str):
        root = etree.fromstring(xml_text.encode("utf-8"))
        body = root.find(".//{*}body")
        sections = []
        if body is not None:
            for div in body.findall("{*}div"):
                sections.append(self._parse_div(div))
        return sections

    def _parse_div(self, div):
        heading = div.findtext("{*}head")
        content = " ".join(list(div.itertext())).strip()
        subsections = [self._parse_div(d) for d in div.findall("{*}div")]

        return {
            "heading": heading.strip() if heading else "Untitled",
            "content": content,
            "subsections": subsections,
        }

    def _flatten_sections(self, sections):
        flat = []

        def walk(sec):
            if sec.get("content", "").strip():
                flat.append({
                    "heading": sec.get("heading"),
                    "content": sec.get("content"),
                })
            for s in sec.get("subsections", []):
                walk(s)

        for s in sections:
            walk(s)
        return flat


class SectionSummaryAgent:
    def __init__(self, llm_model: str = "gpt-4o-mini", temperature: float = 0.05):
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are an expert AI research assistant. Summarize the section "{section_name}" 
from the following content. Produce a concise, structured, and academic-style summary.

Section Text:
{section_text}

Instructions:
- Include key points and methodology if present
- Mention any datasets, results, or experiments
- Keep summary factual and concise
""")
        self.parser = StrOutputParser()
        self.chain = self.prompt_template | self.llm | self.parser

    async def asummarize(self, section_name: str, section_text: str) -> str:
        return await self.chain.ainvoke({"section_name": section_name, "section_text": section_text})

async def summarize_sections_parallel(sections, section_agent):
    async def summarize_one(sec):
        return {
            "section": sec["heading"],
            "summary": await section_agent.asummarize(sec["heading"], sec["content"])
        }

    tasks = [summarize_one(sec) for sec in sections]
    return await asyncio.gather(*tasks)

class SummaryAggregatorAgent:
    def __init__(self, llm_model: str = "gpt-4o-mini", temperature: float = 0.05):
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)
        self.prompt_template = PromptTemplate.from_template("""
You are an expert AI research assistant. Your task is to combine the following individual section summaries into one cohesive and well-structured academic summary of the research paper.

Guidelines:
- Reorganize and merge overlapping or overly detailed sections as needed.
- Choose the most logical and meaningful section headings yourself (e.g., Introduction, Methods, Results, Discussion, Conclusion), based on content.
- Ensure smooth transitions and consistent academic tone throughout.
- Preserve key technical details, results, and findings from the input summaries.
- Do not add information that is not supported by the summaries.

Input Section Summaries:
{sections_text}

Output:
A coherent and complete academic-style summary written in paragraphs with appropriate section headings.
""")
        self.parser = StrOutputParser()

    def combine(self, section_summaries: list[dict]) -> str:
        sections_text = "\n\n".join([f"## {s['section']}\n{s['summary']}" for s in section_summaries])
        chain = self.prompt_template | self.llm | self.parser
        return chain.invoke({"sections_text": sections_text})


class SummaryHighlighterAgent:
    """
    Maps sentences in the final summary back to the most similar
    sentence-level chunks (source text) for highlighting.

    Output mapping: 
    [
        {
            "summary_sentence": "...",
            "matched_chunk": "...",
            "page": 2,
            "coords": "some PDF region id",
            "similarity": 0.89
        },
        ...
    ]


    """
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self.embedder = OpenAIEmbeddings(model=embedding_model)

    def link_summary_to_sources(self, final_summary: str, all_chunks: list[dict], top_k: int = 1):
        """
        Compute semantic similarity between summary sentences and source chunks.
        Returns a mapping of summary sentences to source text with metadata.
        """
        # 1. Split the final summary into sentences
        summary_sentences = sent_tokenize(final_summary)
        print("Highlight agent Summary sentences:", summary_sentences[:5])


        # 2. Prepare embeddings
        chunk_texts = [c["content"] for c in all_chunks]
        print("Highlight agent Chunk texts:", chunk_texts[:5])
        chunk_embeddings = self.embedder.embed_documents(chunk_texts)
        summary_embeddings = self.embedder.embed_documents(summary_sentences)

        # 3. Compute cosine similarity
        chunk_matrix = np.array(chunk_embeddings)
        summary_matrix = np.array(summary_embeddings)

        similarity_matrix = np.dot(summary_matrix, chunk_matrix.T) / (
            np.linalg.norm(summary_matrix, axis=1, keepdims=True)
            * np.linalg.norm(chunk_matrix, axis=1)
        )

        # 4. Build mapping results
        results = []
        for i, sent in enumerate(summary_sentences):
            # Find top-k most similar chunks
            top_indices = np.argsort(similarity_matrix[i])[::-1][:top_k]
            matches = [
                {
                    "summary_sentence": sent,
                    "matched_chunk": all_chunks[j]["content"],
                    "page": all_chunks[j].get("page"),
                    "coords": all_chunks[j].get("coords"),
                    "similarity": float(similarity_matrix[i][j])
                }
                for j in top_indices
            ]
            results.extend(matches)

        print("results of highlight agent:", results[:5])

        return results
