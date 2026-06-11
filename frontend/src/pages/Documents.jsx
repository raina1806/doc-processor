import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:8000";

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents`);
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (e, id) => {
    e.stopPropagation();
    try {
      await fetch(`${API_URL}/api/documents/${id}`, { method: "DELETE" });
      setDocuments(documents.filter(doc => doc.id !== id));
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-500 animate-pulse">Loading documents...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">
              Documents
            </h1>
            <p className="text-gray-500">
              {documents.length} {documents.length === 1 ? "document" : "documents"} processed
            </p>
          </div>
          <button
            onClick={() => navigate("/")}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            + Upload New
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-4xl mb-4">📂</p>
            <p className="text-gray-500">No documents yet — upload one to get started</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {documents.map(doc => (
              <div
                key={doc.id}
                onClick={() => navigate(`/documents/${doc.id}`)}
                className="flex items-center justify-between px-6 py-4 bg-white rounded-xl border border-gray-200 shadow-sm hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl">
                    {doc.file_type === "pdf" ? "📕" : doc.file_type === "docx" ? "📘" : "📄"}
                  </span>
                  <div>
                    <p className="font-medium text-gray-900">{doc.filename}</p>
                    <p className="text-sm text-gray-400">
                      {new Date(doc.uploaded_at).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit"
                      })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded-full font-medium uppercase">
                    {doc.file_type}
                  </span>
                  <button
                    onClick={(e) => deleteDocument(e, doc.id)}
                    className="text-gray-300 hover:text-red-500 transition-colors text-lg"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Documents;