import React, { useEffect, useState } from "react";

export default function ChatHistorySidebar({ sessions, onSelect, onDelete }) {

  const grouped = Object.entries(sessions).reduce((acc, [paperId, data]) => {
    const name = data.filename || "Untitled";
    if (!acc[name]) acc[name] = [];
    acc[name].push({ paperId, ...data });
    return acc;
  }, {});

  return (
    <div className="w-64 h-screen bg-gray-100 border-r overflow-y-auto p-4">
      <h2 className="text-lg font-semibold mb-4">Chat History</h2>

      {Object.keys(grouped).map((filename) => (
        <div key={filename} className="mb-4">
          <h3 className="font-small text-gray-700 mb-2">{filename}</h3>

          <div className="space-y-2">
            {grouped[filename].map((session) => (
              <div
                key={session.paperId}
                className="flex items-center justify-between bg-white p-2 rounded shadow hover:bg-gray-50"
              >
                {/* Click to load chat */}
                <button
                  className="flex-1 text-left"
                  onClick={() => onSelect(session.paperId)}
                >
                  Chat {session.paperId.slice(0, 6)}…
                </button>

                {/* Delete button */}
                <button
                  className="text-red-500 text-sm ml-3"
                  onClick={(e) => {
                    e.stopPropagation();            // prevents triggering onSelect
                    onDelete(session.paperId); // delete logic
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
