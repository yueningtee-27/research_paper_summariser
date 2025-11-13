import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import SplitView from "./components/SplitView";
import PDFViewer from "./components/PDFViewer";
import MultiAgentSummarizer from "./components/MultiAgentSummarizer";
import { useState } from "react";


function App() {
  const [fileUrl, setFileUrl] = useState(null);
  const [filename, setFilename] = useState("");
  return (
    <Router>
      <Routes>
        {/* Default page */}
        <Route path="/" element={<SplitView />} />

        {/* New multi-agent summarizer page */}
        <Route
          path="/multi-agent"
          element={
            <div className="split-container flex h-screen">
              <div className="split-left w-2/3 border-r">
                <PDFViewer fileUrl={fileUrl} />
              </div>
              <div className="split-right w-1/3 overflow-y-auto">
                <MultiAgentSummarizer
                  setFileUrl={setFileUrl}
                  setFilename={setFilename}
                />
              </div>
            </div>
          }
        />

        {/* Redirect unknown paths to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
