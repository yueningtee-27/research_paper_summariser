import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function PaperSummarizer({ setFileUrl, setFilename: setFilenameProp }) {
  const [file, setFile] = useState(null);
  const [summaryType, setSummaryType] = useState("short");
  const [summary, setSummary] = useState("");
  const [filename, setFilename] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(""); // new progress log text

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  // Create blob URL when file is selected
  useEffect(() => {
    if (file && setFileUrl) {
      const url = URL.createObjectURL(file);
      setFileUrl(url);
      console.log("📄 Created blob URL for PDF viewer:", url);
      
      // Cleanup function to revoke URL when component unmounts or file changes
      return () => {
        URL.revokeObjectURL(url);
      };
    } else if (!file && setFileUrl) {
      setFileUrl(null);
    }
  }, [file, setFileUrl]);

  const handleSubmit = async () => {
    if (!file) return alert("Please upload a PDF");

    const formData = new FormData();
    formData.append("pdf", file);
    formData.append("summary_type", summaryType);

    console.log("[1] Uploading PDF:", file.name);
    setProgress("Uploading PDF...");
    setLoading(true);
    setSummary(""); // clear old summary

    try {
      console.log("[2] Sending request to backend...");
      setProgress("Sending request to summarizer backend...");

      const res = await fetch("http://localhost:5000/summarize", {
        method: "POST",
        body: formData,
      });

      console.log("[3] Response received, parsing JSON...");
      setProgress("Processing response...");

      const data = await res.json();
      console.log("[4] Summary received from backend:", data);

      setSummary(data.summary || "⚠️ Error: No summary returned.");
      setFilename(data.filename);
      if (setFilenameProp && data.filename) {
        setFilenameProp(data.filename);
      }
      console.log("Setting file name: ", data.filename);
      setProgress("Summary generation complete ✅");
    } catch (error) {
      console.error("❌ Error during summarization:", error);
      setSummary("⚠️ Failed to generate summary. Check backend logs.");
      setProgress("Error occurred while generating summary ❌");
    } finally {
      setLoading(false);
      console.log("[5] Done.");
    }
  };

  const handleAsk = async () => {
    if (!question) return;
    setAnswer("Thinking...");
    const formData = new FormData();
    formData.append("filename", filename);
    console.log("Filename is:", filename);
    formData.append("question", question);

    const res = await fetch("http://localhost:5000/ask", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    setAnswer(data.answer || "Error generating answer");
  };


  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Research Paper Summarizer</h1>

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => {
          setFile(e.target.files[0]);
          console.log("📄 File selected:", e.target.files[0]);
        }}
        className="mb-4"
      />

      <div className="mb-4">
        <label className="mr-2 font-medium">Summary Type:</label>
        <select
          value={summaryType}
          onChange={(e) => {
            setSummaryType(e.target.value);
            console.log("📝 Summary type changed:", e.target.value);
          }}
          className="border p-2 rounded"
        >
          <option value="short">Short Summary</option>
          <option value="detailed">Detailed Summary</option>
        </select>
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading}
        className={`px-4 py-2 rounded text-white ${
          loading ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {loading ? "Summarizing..." : "Generate Summary"}
      </button>

      {progress && (
        <p className="mt-4 text-sm text-gray-600 italic">{progress}</p>
      )}

{summary && (
        <>
          <div className="mt-6 prose max-w-none">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </div>

          {/* Chat UI */}
          <div className="mt-8 border-t pt-4">
            <h2 className="text-xl font-semibold mb-2">Ask about the Paper</h2>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your question about this paper..."
              className="w-full border p-2 rounded mb-2"
            />
            <button
              onClick={handleAsk}
              disabled={!filename}
              className="bg-green-600 text-white px-4 py-2 rounded"
            >
              Ask
            </button>

            {answer && (
              <div className="mt-4 bg-gray-50 p-4 rounded border">
                <ReactMarkdown>{answer}</ReactMarkdown>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
