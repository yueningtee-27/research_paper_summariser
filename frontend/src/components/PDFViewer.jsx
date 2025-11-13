import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function PDFViewer({ fileUrl, highlights = [] }) {
  const [numPages, setNumPages] = useState(null);

  // Function to render text with highlight markup
  const renderHighlightedText = (str, pageNumber) => {
    // Find any highlight object whose text occurs in this string
    const match = highlights.find(
      (h) =>
        h.page === pageNumber &&
        str.toLowerCase().includes(h.matched_chunk.toLowerCase())
    );

    if (!match) return str; // no highlight on this chunk

    // Split the string and wrap matched parts in <mark>
    const parts = str.split(
      new RegExp(`(${match.matched_chunk})`, "gi")
    );

    return parts.map((part, i) =>
      part.toLowerCase() === match.matched_chunk.toLowerCase() ? (
        <mark key={i} className="bg-yellow-300 rounded-sm">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="h-screen overflow-y-scroll bg-neutral-50 p-4">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">📄 Document Viewer</h2>

      {fileUrl ? (
        <div className="flex flex-col items-center space-y-6">
          <Document
            file={fileUrl}
            onLoadSuccess={({ numPages }) => setNumPages(numPages)}
            loading={<p className="text-gray-500 italic">Loading PDF...</p>}
            className="flex flex-col items-center"
          >
            {Array.from(new Array(numPages), (el, index) => (
              <div key={`page_${index + 1}`} className="shadow-md rounded-xl overflow-hidden bg-white">
                <Page
                  pageNumber={index + 1}
                  // enable text layer so we can wrap text
                  renderTextLayer={true}
                  renderAnnotationLayer={false}
                  className="w-full"
                  // custom renderer inserts <mark> tags for matches
                  customTextRenderer={({ str }) =>
                    renderHighlightedText(str, index + 1)
                  }
                />
                <div className="text-center text-sm text-gray-500 mt-2">
                  Page {index + 1}
                </div>
              </div>
            ))}
          </Document>
        </div>
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500 italic">
          Upload a PDF to preview it here.
        </div>
      )}
    </div>
  );
}
