import { useEffect, useState } from "react";
import PDFViewer from "./PDFViewer";
import PaperSummarizer from "./PaperSummarizer";
import ChatHistorySidebar from "./ChatHistorySidebar";
import "./SplitView.css"; // import your CSS

export default function SplitView() {
  const [fileUrl, setFileUrl] = useState(null);
  const [filename, setFilename] = useState("");
  // Store the backend JSONResponse here 
  const [summaryData, setSummaryData] = useState(null);
  const [selectedPaperId, setSelectedPaperId] = useState(null); 
  const [loadedConversation, setLoadedConversation] = useState([]);
  const [chatHistory, setChatHistory] = useState(
    JSON.parse(localStorage.getItem("chatHistory") || "{}")
  )


  useEffect(() => {
    if (summaryData) {
      console.log("✅ Backend data received in SplitView:", summaryData);
    }
  }, [summaryData]);

  // Load conversation when user clicks a past session in the navbar
  useEffect(() => {
    if (!selectedPaperId) return;

    const all = JSON.parse(localStorage.getItem("chatHistory") || "{}");
    console.log("👉 All sessions in storage:", all);

    const session = all[selectedPaperId];

    if (session) {
      console.log("👉 Loaded selected session:", session);

      setLoadedConversation(session.conversation || []);
    }
  }, [selectedPaperId]);

  return (
    <div className="split-container">
      <div className="split-left">
        <ChatHistorySidebar 
          sessions={chatHistory}
          onSelect={setSelectedPaperId}
          onDelete={(paperId) => {
            const updated = { ...chatHistory };
            delete updated[paperId];
            localStorage.setItem("chatHistory", JSON.stringify(updated));
            setChatHistory(updated);
          }}
        />
      </div>
      <div className="split-center">
        <PDFViewer fileUrl={fileUrl} highlights={summaryData?.highlights || []} />
      </div>
      <div className="split-right">
        <PaperSummarizer
           setFileUrl={setFileUrl} 
           setFilename={setFilename} 
          //  setSummaryData={setSummaryData}
           loadedConversation={loadedConversation}
           selectedPaperId={selectedPaperId}
           onUpdateChatHistory={(updatedHistory) => setChatHistory(updatedHistory)}
        />
      </div>
    </div>
  );
}
