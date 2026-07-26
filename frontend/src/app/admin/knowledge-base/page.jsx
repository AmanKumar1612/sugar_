"use client";

import { useEffect, useState } from "react";
import { Upload, Globe, Trash2, FileText, RefreshCw, Database, Search, Layers } from "lucide-react";
import { getDocuments, deleteDocument, uploadDocument, addWebsite } from "@/services/document";
import api from "@/services/api";

const SEARCH_MODES = [
  {
    id: "hybrid",
    label: "Hybrid",
    desc: "Knowledge base first, web search as fallback",
    icon: Layers,
    color: "text-blue-600 bg-blue-50 border-blue-200",
    activeColor: "bg-blue-600 text-white border-blue-600",
  },
  {
    id: "kb_only",
    label: "KB Only",
    desc: "Only use indexed documents (no web search)",
    icon: Database,
    color: "text-emerald-600 bg-emerald-50 border-emerald-200",
    activeColor: "bg-emerald-600 text-white border-emerald-600",
  },
  {
    id: "web_only",
    label: "Web Only",
    desc: "Always use Tavily web search (ignore KB)",
    icon: Search,
    color: "text-violet-600 bg-violet-50 border-violet-200",
    activeColor: "bg-violet-600 text-white border-violet-600",
  },
];

function Badge({ type }) {
  const styles = {
    pdf:     "bg-red-50 text-red-600 border-red-100",
    website: "bg-blue-50 text-blue-600 border-blue-100",
  };
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium ${styles[type] ?? "bg-gray-50 text-gray-600 border-gray-100"}`}>
      {type === "pdf" ? <FileText size={11} /> : <Globe size={11} />}
      {type}
    </span>
  );
}

function StatusBadge({ status }) {
  if (!status || status === "INDEXED") return null;
  const s = {
    INDEXING: "bg-yellow-50 text-yellow-700 border-yellow-200",
    FAILED:   "bg-red-50 text-red-600 border-red-200",
  };
  return (
    <span className={`ml-1.5 inline-flex items-center text-[10px] px-1.5 py-0.5 rounded border font-medium ${s[status] ?? ""}`}>
      {status === "INDEXING" ? "⏳ indexing" : "❌ failed"}
    </span>
  );
}

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  // PDF upload state
  const [file, setFile] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfStatus, setPdfStatus] = useState({ type: "", msg: "" });

  // Website state
  const [url, setUrl] = useState("");
  const [urlLoading, setUrlLoading] = useState(false);
  const [urlStatus, setUrlStatus] = useState({ type: "", msg: "" });
  const [urlError, setUrlError] = useState("");

  // Delete
  const [deletingId, setDeletingId] = useState(null);

  // Search mode
  const [searchMode, setSearchMode]     = useState("hybrid");
  const [modeLoading, setModeLoading]   = useState(false);
  const [modeStatus,  setModeStatus]    = useState({ type: "", msg: "" });

  useEffect(() => { loadDocuments(); loadSearchMode(); }, []);

  const loadSearchMode = async () => {
    try {
      const res = await api.get("/settings/search-mode");
      setSearchMode(res.data.search_mode);
    } catch { /* non-fatal */ }
  };

  const handleModeChange = async (mode) => {
    if (mode === searchMode) return;
    setModeLoading(true);
    setModeStatus({ type: "", msg: "" });
    try {
      const res = await api.post("/settings/search-mode", { mode });
      setSearchMode(res.data.search_mode);
      setModeStatus({ type: "success", msg: res.data.message });
      setTimeout(() => setModeStatus({ type: "", msg: "" }), 3000);
    } catch (err) {
      setModeStatus({ type: "error", msg: err?.response?.data?.detail || "Failed to update." });
    } finally {
      setModeLoading(false);
    }
  };

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      const data = await getDocuments();
      setDocuments(data ?? []);
    } catch {
      /* non-fatal */
    } finally {
      setLoadingDocs(false);
    }
  };

  // ── Upload PDF ──────────────────────────────────────────
  const handleUpload = async () => {
    if (!file) return;
    setPdfLoading(true);
    setPdfStatus({ type: "", msg: "" });
    try {
      const res = await uploadDocument(file);
      const msg = res.status === "INDEXING"
        ? `PDF received — indexing ${res.chunks ?? "?"} chunks in background. Refresh in a moment.`
        : `Indexed ${res.chunks ?? "?"} chunks.`;
      setPdfStatus({ type: "success", msg });
      setFile(null);
      setTimeout(() => loadDocuments(), 3000); // reload after 3s to show new doc
    } catch (err) {
      setPdfStatus({
        type: "error",
        msg: err?.response?.data?.detail || "Upload failed. Please try again.",
      });
    } finally {
      setPdfLoading(false);
    }
  };

  // ── Add website ─────────────────────────────────────────
  const validateUrl = (v) => {
    try { new URL(v); return true; } catch { return false; }
  };

  const handleWebsite = async () => {
    setUrlError("");
    if (!url.trim()) { setUrlError("Please enter a URL."); return; }
    if (!validateUrl(url.trim())) { setUrlError("Enter a valid URL starting with https://"); return; }

    setUrlLoading(true);
    setUrlStatus({ type: "", msg: "" });
    try {
      const res = await addWebsite(url.trim());
      const msg = res.status === "INDEXING"
        ? `Website received — indexing ${res.chunks ?? "?"} chunks in background. Refresh in a moment.`
        : `Indexed ${res.chunks ?? "?"} chunks.`;
      setUrlStatus({ type: "success", msg });
      setUrl("");
      setTimeout(() => loadDocuments(), 3000);
    } catch (err) {
      setUrlStatus({
        type: "error",
        msg: err?.response?.data?.detail || "Failed to index website. Please try again.",
      });
    } finally {
      setUrlLoading(false);
    }
  };

  // ── Delete ──────────────────────────────────────────────
  const handleDelete = async (id, title) => {
    if (!window.confirm(`Delete "${title}"?\n\nThis will remove it from the knowledge base.`)) return;
    setDeletingId(id);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      /* ignore */
    } finally {
      setDeletingId(null);
    }
  };

  const StatusMsg = ({ status }) => {
    if (!status.msg) return null;
    return (
      <p className={`mt-2 text-sm ${status.type === "error" ? "text-red-500" : "text-emerald-600"}`}>
        {status.msg}
      </p>
    );
  };

  return (
    <div className="max-w-4xl">
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-sm text-gray-500 mt-0.5">Manage documents and websites indexed for RAG retrieval</p>
      </div>

      {/* ── Search Mode Toggle ── */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-7">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-semibold text-gray-900 text-[15px]">Search Mode</h2>
            <p className="text-xs text-gray-400 mt-0.5">Controls how the assistant retrieves answers for all users</p>
          </div>
          {modeLoading && (
            <span className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {SEARCH_MODES.map(({ id, label, desc, icon: Icon, color, activeColor }) => {
            const active = searchMode === id;
            return (
              <button
                key={id}
                onClick={() => handleModeChange(id)}
                disabled={modeLoading}
                className={`flex flex-col items-start gap-2 p-4 rounded-xl border-2 transition text-left disabled:opacity-60 ${
                  active ? activeColor : "border-gray-200 hover:border-gray-300 bg-white"
                }`}
              >
                <div className={`flex items-center gap-2 ${active ? "text-white" : color.split(" ")[0]}`}>
                  <Icon size={16} />
                  <span className="font-semibold text-sm">{label}</span>
                  {active && (
                    <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-white/20 font-medium">Active</span>
                  )}
                </div>
                <p className={`text-xs leading-snug ${active ? "text-white/80" : "text-gray-500"}`}>{desc}</p>
              </button>
            );
          })}
        </div>

        {modeStatus.msg && (
          <p className={`mt-3 text-sm ${modeStatus.type === "error" ? "text-red-500" : "text-emerald-600"}`}>
            {modeStatus.msg}
          </p>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-5 mb-7">
        {/* ── Upload PDF ── */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center">
              <FileText size={15} className="text-red-500" />
            </div>
            <h2 className="font-semibold text-gray-900 text-[15px]">Upload PDF</h2>
          </div>

          <label
            className={`flex flex-col items-center justify-center w-full h-28 border-2 border-dashed rounded-lg cursor-pointer transition ${
              file
                ? "border-blue-300 bg-blue-50"
                : "border-gray-200 bg-gray-50 hover:border-gray-300 hover:bg-gray-100"
            }`}
          >
            <Upload size={20} className={file ? "text-blue-500" : "text-gray-400"} />
            <p className="text-sm mt-1.5 text-gray-500">
              {file ? file.name : "Click to choose a PDF"}
            </p>
            {file && (
              <p className="text-xs text-gray-400 mt-0.5">
                {(file.size / 1024).toFixed(0)} KB
              </p>
            )}
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                setFile(e.target.files[0] ?? null);
                setPdfStatus({ type: "", msg: "" });
              }}
            />
          </label>

          <button
            onClick={handleUpload}
            disabled={!file || pdfLoading}
            className="mt-3 w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
          >
            {pdfLoading && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
            {pdfLoading ? "Uploading & indexing…" : "Upload PDF"}
          </button>

          <StatusMsg status={pdfStatus} />
        </div>

        {/* ── Add Website ── */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
              <Globe size={15} className="text-blue-500" />
            </div>
            <h2 className="font-semibold text-gray-900 text-[15px]">Add Website</h2>
          </div>

          <div className="space-y-2">
            <input
              type="url"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setUrlError("");
                setUrlStatus({ type: "", msg: "" });
              }}
              onKeyDown={(e) => e.key === "Enter" && handleWebsite()}
              placeholder="https://example.com/page"
              aria-label="Website URL"
              className={`w-full px-3.5 py-2.5 rounded-lg border text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition ${
                urlError ? "border-red-400" : "border-gray-200 focus:border-blue-500"
              }`}
            />
            {urlError && <p className="text-xs text-red-500">{urlError}</p>}
          </div>

          <button
            onClick={handleWebsite}
            disabled={urlLoading}
            className="mt-3 w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
          >
            {urlLoading && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
            {urlLoading ? "Crawling & indexing…" : "Index Website"}
          </button>

          <StatusMsg status={urlStatus} />
        </div>
      </div>

      {/* ── Document table ── */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-gray-900 text-[15px]">
              Indexed Documents
              {!loadingDocs && (
                <span className="ml-2 text-xs font-normal text-gray-400">
                  ({documents.length})
                </span>
              )}
            </h2>
          </div>
          <button
            onClick={loadDocuments}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition"
            aria-label="Refresh documents"
          >
            <RefreshCw size={15} className={loadingDocs ? "animate-spin" : ""} />
          </button>
        </div>

        {loadingDocs ? (
          <div className="px-5 py-10 text-center text-sm text-gray-400">Loading…</div>
        ) : documents.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <p className="text-sm text-gray-400">No documents indexed yet.</p>
            <p className="text-xs text-gray-300 mt-1">Upload a PDF or add a website above to get started.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Title</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide w-24">Type</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wide w-20">Chunks</th>
                <th className="px-5 py-3 w-16" />
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition">
                  <td className="px-5 py-3.5 text-gray-800 max-w-xs">
                    <span className="truncate block" title={doc.title}>{doc.title}</span>
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-5 py-3.5">
                    <Badge type={doc.source_type} />
                  </td>
                  <td className="px-5 py-3.5 text-right text-gray-500 tabular-nums">
                    {doc.chunk_count ?? "—"}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={() => handleDelete(doc.id, doc.title)}
                      disabled={deletingId === doc.id}
                      aria-label={`Delete ${doc.title}`}
                      className="p-1.5 rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-500 transition disabled:opacity-40"
                    >
                      {deletingId === doc.id
                        ? <span className="w-3.5 h-3.5 border-2 border-red-300 border-t-transparent rounded-full animate-spin inline-block" />
                        : <Trash2 size={15} />
                      }
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
