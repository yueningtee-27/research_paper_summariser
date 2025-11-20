import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function PaperSummarizer({ 
  setFileUrl, 
  setFilename: setFilenameProp, 
  loadedConversation, 
  selectedPaperId, 
  onUpdateChatHistory 
}) {
  const [file, setFile] = useState(null);
  const [summaryType, setSummaryType] = useState("short");
  const [summary, setSummary] = useState("");
  const [paperId, setPaperId] = useState(null);
  const [filename, setFilename] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(""); // new progress log text

  const [conversation, setConversation] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState("");
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

  //Apply past conversation when user clicks sidebar
  useEffect(() => {
    if (loadedConversation && loadedConversation.length > 0) {
      setConversation(loadedConversation);
    }
  }, [loadedConversation]);

  // Load existing conversation for upload (none)
  useEffect(() => {
    if (!paperId) return;
    
    const all = JSON.parse(localStorage.getItem("chatHistory") || "{}");
  
    if (all[paperId]) {
      setConversation(all[paperId].conversation);
    } else {
      // new upload → start empty
      setConversation([]);
    }
  }, [paperId]);

  // Save conversation only if it contains messages
  useEffect(() => {
    if (!paperId) return;
  
    if (conversation.length === 0) return;  // prevent empty saves
    const all = JSON.parse(localStorage.getItem("chatHistory") || "{}");
  
    all[paperId] = {
      filename: filename,
      conversation
    };
  
    localStorage.setItem("chatHistory", JSON.stringify(all));

    // notify parent SplitView of update immediately
    if (onUpdateChatHistory) onUpdateChatHistory(all);
  }, [paperId, conversation, filename]); // any of these change, the hook will be triggered
  
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
      setPaperId(data.paper_id);
      console.log("Check paper ID (data.paper_id): ", data.paper_id);
      setFilename(data.filename);
      if (setFilenameProp && data.filename) {
        setFilenameProp(data.filename);
      }
      console.log("Setting file name: ", data.filename);
      setProgress("Summary generation complete ✅");
  
      // -----------------------------
      // RAG vectorstore creation
      // -----------------------------
      const paperId = data.filename;
      const formDataQA = new FormData();
      formDataQA.append("file", file);
      formDataQA.append("paper_id", paperId)
  
      fetch("http://localhost:5000/upload_pdf_for_qa", {
        method: "POST",
        body: formDataQA
      })
      .then(resQA => resQA.json())
      .then(dataQA => {
        console.log("[RAG] PDF ready for Q&A:", dataQA);
        setProgress("RAG vectorstore ready. You can now ask questions.");
      })
      .catch(err => {
        console.error("[RAG] Error preparing PDF for Q&A:", err);
        setProgress("⚠️ Failed to prepare Q&A vectorstore.");
      });
  
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
    if (!currentQuestion) return;
    if (!filename) return alert("Please upload PDF first");
  
    const questionToSend = currentQuestion; // store question in local variable
    setCurrentQuestion("");
  
    // Add user message to conversation
    setConversation(prev => [...prev, { role: "user", content: questionToSend }]);
  
    // Show a "thinking" message from assistant
    setConversation(prev => [...prev, { role: "assistant", content: "Thinking..." }]);
  
    const form = new FormData()
    form.append("session_id", "user123");
    form.append("paper_id", filename);
    form.append("question", questionToSend);
  
    try {
      const res = await fetch("http://localhost:5000/ask", {
        method: "POST",
        body: form
      });
  
      const data = await res.json();
  
      // Replace "Thinking..." with actual answer
      setConversation(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: data.answer || "Error generating answer" };
        return updated;
      });
  
    } catch (error) {
      console.error("❌ Failed to get answer:", error);
      setConversation(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: "❌ Failed to get answer" };
        return updated;
      });
    }
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

          // reset conversation for new paper 
          setConversation([]);
          setCurrentQuestion("");
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
            <h2 className="text-xl font-semibold mb-2">Chat with Paper</h2>
            <div className="max-h-64 overflow-y-auto space-y-2 mb-2">
              {conversation.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded ${
                    msg.role === "user" ? "bg-blue-100 text-blue-900 self-end" : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ))}
            </div>

            <textarea
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              placeholder="Type your question..."
              className="w-full border p-2 rounded mb-2"
            />
            <button
              onClick={handleAsk}
              disabled={!filename || !currentQuestion}
              className="bg-green-600 text-white px-4 py-2 rounded"
            >
              Send
            </button>
          </div>
        </>
      )}
    </div>
  );
}
