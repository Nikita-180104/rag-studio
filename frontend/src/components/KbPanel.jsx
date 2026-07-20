import React, { useState, useEffect, useRef } from 'react';
import { 
  Database, RefreshCw, UploadCloud, FileText, FileCode, File, 
  Trash2, RotateCw, Loader2, HelpCircle 
} from 'lucide-react';
import { 
  listDocuments, uploadDocument, deleteDocument, reindexDocument 
} from '../api/ragApi';

/**
 * Knowledge Base sidebar panel component.
 * Allows file uploads via browse or drag-and-drop, displays
 * progress metrics, and lists indexed documents with controls.
 */
export default function KbPanel({ isOpen, onClose, isOnline, showToast }) {
  const [documents, setDocuments] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingFilename, setUploadingFilename] = useState('');
  const [processingDoc, setProcessingDoc] = useState(null); // { type: 'reindex'|'delete', filename: string }
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isOpen && isOnline) {
      fetchDocs();
    }
  }, [isOpen, isOnline]);

  const fetchDocs = async () => {
    setLoadingList(true);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err) {
      showToast('Failed to fetch document list.', 'error');
    } finally {
      setLoadingList(false);
    }
  };

  const handleUpload = async (file) => {
    if (!isOnline) return;
    
    // Check file extension
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.pdf', '.docx', '.txt', '.md'].includes(ext)) {
      showToast('Unsupported file type. Use PDF, DOCX, TXT, or MD.', 'error');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadingFilename(file.name);

    try {
      const response = await uploadDocument(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });

      if (response.success) {
        showToast(response.message || 'Document indexed successfully.', 'success');
        fetchDocs();
      } else {
        showToast(response.message || 'Upload failed.', 'warning');
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Failed to upload and index document.';
      showToast(errMsg, 'error');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      setUploadingFilename('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (filename) => {
    if (!isOnline || !window.confirm(`Are you sure you want to delete "${filename}"?`)) return;
    
    setProcessingDoc({ type: 'delete', filename });
    try {
      const res = await deleteDocument(filename);
      showToast(res.message || `Deleted "${filename}" successfully.`, 'success');
      fetchDocs();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete document.', 'error');
    } finally {
      setProcessingDoc(null);
    }
  };

  const handleReindex = async (filename) => {
    if (!isOnline) return;
    
    setProcessingDoc({ type: 'reindex', filename });
    try {
      const res = await reindexDocument(filename);
      showToast(res.message || `Re-indexed "${filename}" successfully.`, 'success');
      fetchDocs();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to re-index document.', 'error');
    } finally {
      setProcessingDoc(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (isOnline) setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (!isOnline) return;
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  };

  const getFileIcon = (filename) => {
    const ext = filename.substring(filename.lastIndexOf('.')).toLowerCase();
    if (ext === '.md') return <FileCode className="h-4.5 w-4.5 text-purple-400 text-glow-purple" />;
    if (ext === '.txt') return <FileText className="h-4.5 w-4.5 text-blue-400 text-glow-blue" />;
    return <File className="h-4.5 w-4.5 text-gray-400" />;
  };

  if (!isOpen) return null;

  return (
    <aside className="w-80 border-r border-darkBorder/50 glass-panel flex flex-col h-full overflow-y-auto shrink-0 shadow-[0_0_35px_rgba(0,0,0,0.3)] animate-slideRight backdrop-blur-xl">
      {/* KB Sidebar Header */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-darkBorder/50 bg-darkBg/30">
        <div className="flex items-center space-x-2.5 text-white">
          <Database className="h-4.5 w-4.5 text-blue-400 text-glow-blue animate-glow" />
          <h2 className="font-bold tracking-widest text-xs uppercase">Knowledge Base</h2>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDocs}
            disabled={!isOnline || loadingList}
            className="text-gray-400 hover:text-white cursor-pointer transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none"
            title="Refresh documents"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loadingList ? 'animate-spin text-blue-400' : ''}`} />
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-[10px] font-bold uppercase tracking-widest cursor-pointer transition-all duration-150 focus:outline-none"
          >
            Close
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div className="flex-1 p-6 space-y-6 flex flex-col min-h-0">
        {/* Upload Panel */}
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => isOnline && !isUploading && fileInputRef.current.click()}
          className={`border border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center space-y-2.5 ${
            isDragOver 
              ? 'border-blue-500 bg-blue-600/10 shadow-[0_0_15px_rgba(31,111,235,0.2)]' 
              : 'border-darkBorder hover:border-blue-500/50 hover:bg-darkBg/30'
          } ${(!isOnline || isUploading) ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={(e) => e.target.files.length > 0 && handleUpload(e.target.files[0])}
            className="hidden"
            accept=".pdf,.docx,.txt,.md"
            disabled={!isOnline || isUploading}
          />
          <UploadCloud className={`h-8 w-8 ${isDragOver ? 'text-blue-400 animate-bounce' : 'text-gray-500'}`} />
          <div className="text-xs font-semibold text-white">
            {isDragOver ? 'Drop file here' : 'Drag & drop file or browse'}
          </div>
          <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
            PDF, DOCX, TXT, MD
          </div>
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="bg-darkBg/50 p-4 rounded-xl border border-darkBorder/40 space-y-2.5 animate-fadeIn">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-gray-400 truncate max-w-[180px]">
                {uploadingFilename}
              </span>
              <span className="font-mono text-blue-400 font-bold">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-[#181C24] rounded-full h-1.5 overflow-hidden border border-darkBorder/20">
              <div 
                className="bg-blue-500 h-full transition-all duration-150 rounded-full" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <div className="flex items-center space-x-2 text-[10px] text-gray-500 font-bold uppercase tracking-wider">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-400" />
              <span>Indexing document...</span>
            </div>
          </div>
        )}

        {/* Document List */}
        <div className="flex-1 flex flex-col min-h-0 space-y-3">
          <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">
            Indexed Documents ({documents.length})
          </div>

          <div className="flex-1 overflow-y-auto pr-1 space-y-3 min-h-0">
            {documents.length === 0 ? (
              <div className="h-32 flex flex-col items-center justify-center text-center text-gray-500">
                <HelpCircle className="h-8 w-8 text-gray-600 mb-2" />
                <p className="text-xs leading-relaxed max-w-[200px]">
                  No documents indexed yet. Upload a file to populate the Knowledge Base.
                </p>
              </div>
            ) : (
              documents.map((doc) => {
                const isProcessing = processingDoc?.filename === doc.filename;
                return (
                  <div 
                    key={doc.filename}
                    className="p-3.5 rounded-xl border border-darkBorder/40 bg-darkBg/20 flex flex-col space-y-2 relative transition-all duration-200 hover:border-darkBorder hover:bg-darkBg/40 group overflow-hidden"
                  >
                    {/* Background loader during processing */}
                    {isProcessing && (
                      <div className="absolute inset-0 bg-darkBg/80 backdrop-blur-xs flex items-center justify-center space-x-2 z-10">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                          {processingDoc.type === 'delete' ? 'Deleting...' : 'Re-indexing...'}
                        </span>
                      </div>
                    )}

                    {/* Card Header Info */}
                    <div className="flex items-start space-x-2.5">
                      <div className="mt-0.5 shrink-0">
                        {getFileIcon(doc.filename)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div 
                          className="text-xs font-bold text-white truncate cursor-help"
                          title={doc.filename}
                        >
                          {doc.filename}
                        </div>
                        <div className="text-[9px] text-gray-500 font-semibold mt-0.5">
                          {doc.upload_date}
                        </div>
                      </div>
                    </div>

                    {/* Card Footer Meta / Badge */}
                    <div className="flex items-center justify-between pt-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-mono text-gray-400 bg-[#181C24] px-1.5 py-0.5 rounded border border-darkBorder/20">
                          {doc.chunks} chunks
                        </span>
                        <span className="inline-flex rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-emerald-950/20 text-emerald-400 border border-emerald-500/10 text-glow-emerald">
                          {doc.status}
                        </span>
                      </div>

                      {/* Action buttons shown on hover */}
                      <div className="flex items-center space-x-2.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button
                          onClick={() => handleReindex(doc.filename)}
                          disabled={!isOnline || isProcessing}
                          className="text-gray-400 hover:text-blue-400 cursor-pointer disabled:opacity-30 transition-colors duration-150 focus:outline-none"
                          title="Re-index document"
                        >
                          <RotateCw className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.filename)}
                          disabled={!isOnline || isProcessing}
                          className="text-gray-400 hover:text-rose-400 cursor-pointer disabled:opacity-30 transition-colors duration-150 focus:outline-none"
                          title="Delete document"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
