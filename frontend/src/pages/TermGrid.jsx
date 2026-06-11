import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function TermGrid() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [terms, setTerms] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTerms();
  }, [id]);

  useEffect(() => {
    if (search.trim() === "") {
      setFiltered(terms);
    } else {
      setFiltered(terms.filter(t =>
        t.term.toLowerCase().includes(search.toLowerCase()) ||
        t.value.toLowerCase().includes(search.toLowerCase())
      ));
    }
  }, [search, terms]);

  const fetchTerms = async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents/${id}/terms`);
      const data = await response.json();
      setDocument(data.document);
      setTerms(data.terms);
      setFiltered(data.terms);
    } catch (err) {
      console.error("Failed to fetch terms:", err);
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    const header = "Term,Value\n";
    const rows = terms.map(t =>
      `"${t.term}","${t.value.replace(/"/g, '""')}"`
    ).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = `${document?.filename?.replace(/\.[^/.]+$/, "")}_terms.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportExcel = async () => {
  try {
    const response = await fetch(
      `${API_URL}/api/documents/${id}/export/excel`
    );
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = `${document?.filename?.replace(/\.[^/.]+$/, "")}_terms.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Export failed:", err);
  }
};

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-500 animate-pulse">Loading term grid...</p>
    </div>
  );

  const viewDocument = () => {
  window.open(`${API_URL}/api/documents/${id}/file`, "_blank");
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="max-w-4xl mx-auto">

        <button
          onClick={() => navigate("/documents")}
          className="text-sm text-gray-500 hover:text-gray-700 mb-6 flex items-center gap-1"
        >
          ← Back to Documents
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {document?.filename}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {terms.length} {terms.length === 1 ? "term" : "terms"} extracted
          </p>
        </div>

        <div className="flex items-center gap-2 mb-6">
            <button
              onClick={viewDocument}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >

              View Document
            </button>
            <button
                onClick={exportCSV}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
                Export CSV
            </button>
            <button
                onClick={exportExcel}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
            >
                Export Excel
            </button>
        </div>

        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search terms or values..."
          className="w-full px-4 py-2 mb-6 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/3">
                  Term
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Value
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((term, index) => (
                <tr
                  key={index}
                  className="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {term.term}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {term.value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filtered.length === 0 && (
            <p className="text-center text-gray-400 py-10">
              No terms match your search
            </p>
          )}
        </div>

      </div>
    </div>
  );
}

export default TermGrid;