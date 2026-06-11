import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:8000";

function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState("");
  const navigate = useNavigate();
  const abortControllerRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      const ext = selected.name.split(".").pop().toLowerCase();
      if (!["pdf", "docx", "txt"].includes(ext)) {
        setError("Only PDF, DOCX and TXT files are supported");
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      const ext = dropped.name.split(".").pop().toLowerCase();
      if (!["pdf", "docx", "txt"].includes(ext)) {
        setError("Only PDF, DOCX and TXT files are supported");
        return;
      }
      setFile(dropped);
      setError(null);
    }
  };

const handleCancel = async () => {
  // tell backend to stop
  try {
    await fetch(`${API_URL}/api/documents/cancel`, {
      method: "POST"
    });
  } catch (err) {
    console.error("Cancel request failed:", err);
  }

  // abort frontend request
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
  }

  setLoading(false);
  setProgress("");
  setError(null);
};

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setProgress("Uploading document...");

    abortControllerRef.current = new AbortController();

    const formData = new FormData();
    formData.append("file", file);

    try {
      setProgress("Extracting text and processing with AI...");
      const response = await fetch(`${API_URL}/api/documents/upload`, {
        method: "POST",
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Upload failed");
      }

      const data = await response.json();
      navigate(`/documents/${data.document.id}`);

    } catch (err) {
      if (err.name === "AbortError") {
        setError(null);
        setProgress("");
      } else {
        setError(err.message);
        setProgress("");
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Upload Document
        </h1>
        <p className="text-gray-500 mb-8">
          Upload a credit agreement or term sheet to extract key terms
        </p>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-400 transition-colors cursor-pointer bg-white"
          onClick={() => !loading && document.getElementById("fileInput").click()}
        >
          <div className="text-4xl mb-4">📄</div>
          {file ? (
            <div>
              <p className="text-lg font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          ) : (
            <div>
              <p className="text-lg font-medium text-gray-700">
                Drop your document here
              </p>
              <p className="text-sm text-gray-400 mt-1">
                or click to browse — PDF, DOCX, TXT supported
              </p>
            </div>
          )}
          <input
            id="fileInput"
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        {error && (
          <p className="text-red-500 text-sm mt-4">{error}</p>
        )}

        {loading && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <p className="text-blue-600 text-sm animate-pulse">
                {progress}
              </p>
              <span className="text-blue-400 text-xs">
                {file?.name}
              </span>
            </div>
            <p className="text-blue-400 text-xs">
              Large documents may take several minutes to process...
            </p>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="flex-1 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Processing..." : "Extract Terms"}
          </button>

          {loading && (
            <button
              onClick={handleCancel}
              className="px-6 py-3 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

      </div>
    </div>
  );
}

export default Upload;