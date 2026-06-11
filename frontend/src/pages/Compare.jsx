import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:8000";

function Compare() {
  const [documents, setDocuments] = useState([]);
  const [doc1Id, setDoc1Id] = useState("");
  const [doc2Id, setDoc2Id] = useState("");
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
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
    }
  };

  const handleCompare = async () => {
    if (!doc1Id || !doc2Id) {
      setError("Please select two documents to compare");
      return;
    }
    if (doc1Id === doc2Id) {
      setError("Please select two different documents");
      return;
    }

    setLoading(true);
    setError(null);
    setComparison(null);

    try {
      const response = await fetch(
        `${API_URL}/api/documents/compare?doc1_id=${doc1Id}&doc2_id=${doc2Id}`
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Comparison failed");
      }

      const data = await response.json();
      setComparison(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredRows = comparison?.comparison.filter(row => {
    const matchesSearch =
      search.trim() === "" ||
      row.term.toLowerCase().includes(search.toLowerCase()) ||
      row.value1.toLowerCase().includes(search.toLowerCase()) ||
      row.value2.toLowerCase().includes(search.toLowerCase());

    const matchesFilter =
      filter === "all" ||
      (filter === "match" && row.match === "Match") ||
      (filter === "nomatch" && row.match === "No Match");

    return matchesSearch && matchesFilter;
  });

  const exportComparisonCSV = () => {
    if (!comparison) return;
    const header = `Term,"${comparison.doc1.filename}","${comparison.doc2.filename}",Match\n`;
    const rows = comparison.comparison.map(row =>
      `"${row.term}","${row.value1.replace(/"/g, '""')}","${row.value2.replace(/"/g, '""')}","${row.match}"`
    ).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = `comparison_${comparison.doc1.filename}_vs_${comparison.doc2.filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="max-w-6xl mx-auto">

        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Compare Documents
        </h1>
        <p className="text-gray-500 mb-8">
          Select two documents to compare their term grids side by side
        </p>

        {/* Document selector */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Document A
              </label>
              <select
                value={doc1Id}
                onChange={(e) => setDoc1Id(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a document...</option>
                {documents.map(doc => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Document B
              </label>
              <select
                value={doc2Id}
                onChange={(e) => setDoc2Id(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a document...</option>
                {documents.map(doc => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <p className="text-red-500 text-sm mb-4">{error}</p>
          )}

          <button
            onClick={handleCompare}
            disabled={!doc1Id || !doc2Id || loading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Comparing..." : "Compare Documents"}
          </button>
        </div>

        {/* Comparison results */}
        {comparison && (
          <div>
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">
                  {comparison.total}
                </p>
                <p className="text-sm text-gray-500 mt-1">Total Terms</p>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-bold text-green-600">
                  {comparison.matches}
                </p>
                <p className="text-sm text-gray-500 mt-1">Matches</p>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 text-center">
                <p className="text-2xl font-bold text-red-500">
                  {comparison.differences}
                </p>
                <p className="text-sm text-gray-500 mt-1">Differences</p>
              </div>
            </div>

            {/* Search and filter */}
            <div className="flex gap-3 mb-4">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search terms or values..."
                className="flex-1 px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Terms</option>
                <option value="match">Matches Only</option>
                <option value="nomatch">Differences Only</option>
              </select>
              <button
                onClick={exportComparisonCSV}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                Export CSV
              </button>
            </div>

            {/* Comparison table */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/5">
                      Term
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-2/5">
                      {comparison.doc1.filename}
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-2/5">
                      {comparison.doc2.filename}
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-1/5">
                      Match
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRows.map((row, index) => (
                    <tr
                      key={index}
                      className="border-b border-gray-100 last:border-0"
                    >
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {row.term}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {row.value1}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {row.value2}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${
                          row.match === "Match"
                            ? "bg-green-50 text-green-600"
                            : "bg-red-50 text-red-500"
                        }`}>
                          {row.match}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredRows.length === 0 && (
                <p className="text-center text-gray-400 py-10">
                  No terms match your search or filter
                </p>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default Compare;