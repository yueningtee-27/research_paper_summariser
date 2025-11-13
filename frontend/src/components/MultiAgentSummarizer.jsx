import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function MultiAgentSummarizer({ setFileUrl, setFilename: setFilenameProp }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [filename, setFilename] = useState("");
  const [summary, setSummary] = useState("");
  const [sections, setSections] = useState([]); // per-section summaries
  const [highlights, setHighlights] = useState([]);
 
  // Handle PDF blob URL for the PDF viewer (if you have one)
  useEffect(() => {
    if (file && setFileUrl) {
      const url = URL.createObjectURL(file);
      setFileUrl(url);
      return () => URL.revokeObjectURL(url);
    } else if (!file && setFileUrl) {
      setFileUrl(null);
    }
  }, [file, setFileUrl]);

  const handleSubmit = async () => {
    if (!file) return alert("Please upload a PDF file first.");

    const formData = new FormData();
    formData.append("pdf", file);

    setLoading(true);
    setProgress("Uploading and analyzing PDF with multi-agent system...");
    setSummary("");
    setSections([]);

    try {
      const res = await fetch("http://localhost:5000/multi-agent-summarize", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();

      console.log("✅ Multi-agent summary response:", data);

      setSummary(data.summary || "⚠️ No summary returned.");
      setSections(data.sections || []);
      setProgress("Summary successfully generated ✅");
      setHighlights(data.highlights || "⚠️ No highlights returned.")
      console.log("Highlights array:", highlights);

      // Optional filename tracking for future /ask calls
      const generatedFilename = file.name;
      setFilename(generatedFilename);
      if (setFilenameProp) setFilenameProp(generatedFilename);
    } catch (err) {
      console.error("❌ Multi-agent summarization failed:", err);
      setSummary("⚠️ Failed to generate summary. Check backend logs.");
      setProgress("Error occurred while generating summary ❌");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">🧠 Multi-Agent Research Paper Summarizer</h1>

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files[0])}
        className="mb-4"
      />

      <button
        onClick={handleSubmit}
        disabled={loading}
        className={`px-4 py-2 rounded text-white ${
          loading ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {loading ? "Processing..." : "Generate Multi-Agent Summary"}
      </button>

      {progress && <p className="mt-4 text-sm text-gray-600 italic">{progress}</p>}

      {/* Final Summary */}
      {summary && (
        <div className="mt-6 border rounded bg-gray-50 p-4">
          <h2 className="text-xl font-semibold mb-2">📄 Final Paper Summary</h2>
          <div className="prose max-w-none">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Section Summaries */}
      {/* {sections.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-2">📚 Section Summaries</h2>
          {sections.map((s, idx) => (
            <div key={idx} className="border rounded p-3 mb-3 bg-white shadow-sm">
              <h3 className="font-bold text-gray-800">{s.section}</h3>
              <div className="prose max-w-none text-sm text-gray-700 mt-2">
                <ReactMarkdown>{s.summary}</ReactMarkdown>
              </div>
            </div>
          ))}
        </div>
      )} */}
    </div>
  );
}
