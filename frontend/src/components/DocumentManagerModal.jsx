import React, { useState, useEffect } from 'react';
import { X, Upload, Trash2, FileText, Database, Check, AlertCircle, RefreshCw, Layers, ShieldCheck, Loader2 } from 'lucide-react';
import { apiService } from '../services/apiService';

export default function DocumentManagerModal({ isOpen, onClose }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusInfo, setStatusInfo] = useState({ source: 'local', connected: false });
  const [feedback, setFeedback] = useState(null);

  // Form State
  const [selectedFile, setSelectedFile] = useState(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('handbook');
  const [activeTab, setActiveTab] = useState('list'); // 'list' | 'upload'

  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await apiService.listDocuments();
      setDocuments(data.documents || []);
      setStatusInfo({ source: data.source, connected: data.connected });
    } catch (e) {
      console.warn('Failed to load documents:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!title) {
        setTitle(file.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()));
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || !title.trim()) return;

    setUploading(true);
    setFeedback(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', title.trim());
    formData.append('category', category);

    try {
      const data = await apiService.uploadDocument(formData);

      setFeedback({
        type: 'success',
        msg: `"${title}" successfully uploaded and indexed into ${data.chunks_count} knowledge chunks!`,
      });
      setSelectedFile(null);
      setTitle('');
      setActiveTab('list');
      loadDocuments();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId, docTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${docTitle}"?`)) return;

    try {
      await apiService.deleteDocument(docId);
      setFeedback({ type: 'success', msg: `Deleted "${docTitle}".` });
      loadDocuments();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message });
    }
  };

  const handleSyncLocal = async () => {
    setLoading(true);
    try {
      const data = await apiService.syncDocuments();
      setFeedback({
        type: 'success',
        msg: `Sync complete: ${data.synced_count || 0} local documents uploaded to Supabase.`,
      });
      loadDocuments();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.message });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-3xl bg-[#0c0e18] border border-cyan-500/30 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Campus Document & Knowledge Vault</h3>
                {statusInfo.connected ? (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    Supabase Connected
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    Local Storage Fallback
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                Manage PDF & Text documents ingested into the RAG knowledge system
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab & Action Navigation */}
        <div className="flex items-center justify-between px-6 pt-3 border-b border-slate-800 bg-slate-950/40">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('list')}
              className={`px-4 py-2 text-xs font-semibold rounded-t-xl transition-all border-b-2 cursor-pointer ${
                activeTab === 'list'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-950/20'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              Indexed Documents ({documents.length})
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-t-xl transition-all border-b-2 cursor-pointer ${
                activeTab === 'upload'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-950/20'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              <Upload className="w-3.5 h-3.5" />
              Upload New Document
            </button>
          </div>

          {statusInfo.connected && (
            <button
              onClick={handleSyncLocal}
              disabled={loading}
              className="flex items-center gap-1 px-3 py-1 mb-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium transition-all cursor-pointer disabled:opacity-50"
              title="Sync local data/documents to Supabase"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              <span>Sync Local Files</span>
            </button>
          )}
        </div>

        {/* Feedback Alert Toast */}
        {feedback && (
          <div className="mx-6 mt-3">
            <div
              className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
                feedback.type === 'success'
                  ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-200'
                  : 'bg-rose-500/15 border-rose-500/30 text-rose-200'
              }`}
            >
              <div className="flex items-center gap-2">
                {feedback.type === 'success' ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                )}
                <span>{feedback.msg}</span>
              </div>
              <button onClick={() => setFeedback(null)} className="ml-2 font-bold hover:text-white">✕</button>
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'upload' ? (
            /* Upload Form */
            <form onSubmit={handleUpload} className="space-y-4 max-w-lg mx-auto">
              <div className="p-6 border-2 border-dashed border-slate-700 hover:border-cyan-500/50 rounded-2xl bg-slate-900/30 flex flex-col items-center justify-center text-center transition-all cursor-pointer relative">
                <input
                  type="file"
                  accept=".pdf,.txt,.md"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <FileText className="w-10 h-10 text-cyan-400 mb-2 animate-pulse" />
                <span className="text-sm font-semibold text-white">
                  {selectedFile ? selectedFile.name : 'Choose a PDF, TXT, or MD document'}
                </span>
                <span className="text-xs text-slate-400 mt-1">
                  Click or drag file here (Max 10MB)
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Document Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Campus Placement Guidelines 2026"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-none focus:border-cyan-400"
                >
                  <option value="handbook">Student Handbook & Rules</option>
                  <option value="syllabus">Course Syllabus</option>
                  <option value="protocols">Examination Protocols</option>
                  <option value="notices">Campus Notices & Bulletins</option>
                  <option value="general">General Campus Information</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={!selectedFile || !title.trim() || uploading}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-cyan-500/20"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Extracting Text & Ingesting Chunks...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Ingest into Knowledge System</span>
                  </>
                )}
              </button>
            </form>
          ) : (
            /* Document List Table */
            <div>
              {loading ? (
                <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                  <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mb-2" />
                  <span>Loading documents...</span>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <p>No documents uploaded yet.</p>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="mt-3 px-4 py-1.5 rounded-lg bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-xs font-semibold cursor-pointer"
                  >
                    Upload First Document
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-3.5 rounded-xl glass-panel border border-slate-800 flex items-center justify-between gap-4 hover:border-cyan-500/40 transition-all"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-300 shrink-0 mt-0.5">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-sm font-bold text-white">{doc.title}</h4>
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 border border-slate-700 text-slate-300">
                              {doc.file_type || doc.filename.split('.').pop()}
                            </span>
                            <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950/40 border border-cyan-500/30 text-cyan-300">
                              {doc.category}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-400">
                            <span>📄 {doc.filename}</span>
                            <span>•</span>
                            <span className="flex items-center gap-1 text-indigo-300">
                              <Layers className="w-3 h-3" />
                              {doc.chunks_count || 1} Chunks
                            </span>
                            <span>•</span>
                            <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDelete(doc.id || doc.filename, doc.title)}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-rose-500/20 border border-slate-700 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 transition-all cursor-pointer"
                        title="Delete document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
