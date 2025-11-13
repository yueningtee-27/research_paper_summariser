# agents/highlight_agent.py

import faiss
import numpy as np
import fitz  # PyMuPDF
from openai import OpenAI

class HighlightAgent:
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self.embedding_model = embedding_model
        self.client = OpenAI()
        self.index = None
        self.chunk_metadata = []

    def build_index(self, flat_sections):
        """
        Build FAISS index from all chunks in all sections.
        Stores chunk metadata for highlighting.
        """
        chunks = [chunk for sec in flat_sections for chunk in sec.get("chunks", [])]
        self.chunk_metadata = chunks

        # Create embeddings for each chunk
        embeddings = []
        for chunk in chunks:
            emb = self.client.embeddings.create(
                input=chunk["content"],
                model=self.embedding_model
            )["data"][0]["embedding"]
            embeddings.append(emb)

        embeddings = np.array(embeddings).astype("float32")
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

    def search_chunks(self, query, top_k=3):
        """
        Return top-k chunks most relevant to the query.
        """
        query_emb = np.array(
            self.client.embeddings.create(
                input=query,
                model=self.embedding_model
            )["data"][0]["embedding"]
        ).astype("float32")

        distances, indices = self.index.search(np.array([query_emb]), k=top_k)
        results = [self.chunk_metadata[i] for i in indices[0]]
        return results

    def highlight_summary(self, summary_text, pdf_path, output_path, top_k=3):
        """
        Highlight supporting chunks for each sentence in the summary.
        """
        # Split summary into sentences (naive split)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', summary_text)

        pdf = fitz.open(pdf_path)

        for sentence in sentences:
            top_chunks = self.search_chunks(sentence, top_k=top_k)
            for chunk in top_chunks:
                if chunk["coords"] and chunk["page"] is not None:
                    page = pdf[chunk["page"] - 1]  # PyMuPDF pages are 0-indexed
                    try:
                        x0, y0, x1, y1 = map(float, chunk["coords"].split(","))
                        rect = fitz.Rect(x0, y0, x1, y1)
                        page.addHighlightAnnot(rect)
                    except Exception as e:
                        print(f"Failed to highlight chunk: {e}")

        pdf.save(output_path)
        print(f"Saved highlighted PDF to {output_path}")
