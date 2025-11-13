import { useEffect, useState } from "react";
import PDFViewer from "./PDFViewer";
import PaperSummarizer from "./PaperSummarizer";
import "./SplitView.css"; // import your CSS

export default function SplitView() {
  const [fileUrl, setFileUrl] = useState(null);
  const [filename, setFilename] = useState("");
  // Store the backend JSONResponse here 
  const [summaryData, setSummaryData] = useState(null);

  useEffect(() => {
    if (summaryData) {
      console.log("✅ Backend data received in SplitView:", summaryData);
    }
  }, [summaryData]);

  return (
    <div className="split-container">
      <div className="split-left">
        <PDFViewer fileUrl={fileUrl} highlights={summaryData?.highlights || []} />
      </div>
      <div className="split-right">
        <PaperSummarizer setFileUrl={setFileUrl} setFilename={setFilename} setSummaryData={setSummaryData}/>
      </div>
    </div>
  );
}
