import React, { useState, useEffect } from 'react';
import HealthBar from './components/HealthBar';
import ChatWindow from './components/ChatWindow';
import TelemetryPanel from './components/TelemetryPanel';
import { checkHealth, queryRAG, clearCache, listDocuments } from './api/ragApi';
import { X, Info, CheckCircle, AlertTriangle, Database } from 'lucide-react';
import KbPanel from './components/KbPanel';
import './App.css';

/**
 * Master Application Coordinator.
 * Controls thread logs, query telemetry states, connection heartbeats,
 * and renders custom, dependency-free toast notifications.
 */
export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState(null);
  const [isOnline, setIsOnline] = useState(false);
  const [activeTelemetry, setActiveTelemetry] = useState(null);
  const [isKbOpen, setIsKbOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [documents, setDocuments] = useState([]);


  // Emits a custom, premium toast alert
  const showToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // Performs a heartbeat health check on the backend
  const runHeartbeat = async (isInitial = false) => {
    try {
      const data = await checkHealth();
      setHealth(data);
      if (!isOnline) {
        setIsOnline(true);
        if (!isInitial) {
          showToast(`Connected to backend. Provider: ${data.vector_db_provider.toUpperCase()}`, 'success');
        }
      }
    } catch (err) {
      if (isOnline || isInitial) {
        setIsOnline(false);
        setHealth(null);
        showToast('Backend offline. Re-connecting to localhost:8000...', 'error');
      }
    }
  };

  // Initialize and schedule periodic heartbeats
  useEffect(() => {
    runHeartbeat(true);
    const interval = setInterval(() => {
      runHeartbeat(false);
    }, 10000); // 10s interval
    return () => clearInterval(interval);
  }, [isOnline]);

  // Fetches document list from backend
  const fetchDocs = async () => {
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to fetch document list.', err);
    }
  };

  useEffect(() => {
    if (isOnline) {
      fetchDocs();
    }
  }, [isOnline]);

  // Clears the persistent SQLite query cache
  const handleClearCache = async () => {
    try {
      const res = await clearCache();
      showToast(res.message || 'SQLite cache cleared successfully.', 'success');
      setActiveTelemetry(null);
    } catch (err) {
      showToast('Failed to clear persistent query cache.', 'error');
    }
  };

  // Dispatches a user query to the RAG pipeline
  const handleSendMessage = async (text) => {
    if (loading || !isOnline) return;

    // Map current message thread history to role/content pairs for backend condensation
    const history = messages.map((msg) => ({
      role: msg.role,
      content: msg.text,
    }));

    // Append User query message to log
    const userMessage = { role: 'user', text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await queryRAG(text, history);
      
      // Append AI response containing citations
      const aiMessage = {
        role: 'assistant',
        text: res.answer,
        citations: res.citations || [],
        contexts: res.contexts || [],
        telemetry: res.telemetry || null,
      };

      setMessages((prev) => [...prev, aiMessage]);
      
      // Update selected query telemetry panel
      if (res.telemetry) {
        setActiveTelemetry(res.telemetry);
      }
    } catch (err) {
      // Check if it is a SlowAPI 429 Rate Limit error
      if (err.response && err.response.status === 429) {
        showToast('Rate Limit Exceeded: Max 5 queries per minute.', 'warning');
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: 'Rate limit exceeded. System limits client IPs to 5 queries per minute to protect API bounds. Please wait a moment and try again.',
            citations: [],
            contexts: [],
          }
        ]);
      } else {
        showToast('Internal error occurred during RAG pipeline query.', 'error');
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: 'Failed to process query. An unexpected connection error occurred.',
            citations: [],
            contexts: [],
          }
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-darkBg text-gray-200 overflow-hidden font-sans">
      {/* Dynamic Healthbar top deck */}
      <HealthBar health={health} isOnline={isOnline} onClearCache={handleClearCache} documentsCount={documents.length} />

      {/* Main content split panel */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Backdrop Overlay when KB Drawer is open */}
        {isKbOpen && (
          <div 
            onClick={() => setIsKbOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-xs z-40 transition-all duration-300 cursor-pointer"
          />
        )}

        {/* Knowledge Base Panel (slides in as overlay) */}
        <KbPanel
          isOpen={isKbOpen}
          onClose={() => setIsKbOpen(false)}
          isOnline={isOnline}
          showToast={showToast}
          documents={documents}
          onRefreshDocs={fetchDocs}
        />

        {/* Chat Window viewport (full width focus) */}
        <ChatWindow
          messages={messages}
          loading={loading}
          onSendMessage={handleSendMessage}
          isOnline={isOnline}
          documents={documents}
          onOpenKb={() => setIsKbOpen(true)}
          onClearChat={() => setMessages([])}
        />

        {/* Floating KB Drawer Trigger Button (bottom-left) */}
        {!isKbOpen && (
          <button
            onClick={() => setIsKbOpen(true)}
            className="fixed bottom-6 left-6 z-45 text-violet-400 hover:text-white border border-darkBorder hover:border-violet-500/50 rounded-full px-5 py-2.5 shadow-2xl transition-all duration-200 cursor-pointer active:scale-95 flex items-center space-x-2 font-bold text-xs uppercase tracking-wider bg-[#181C24]/90 backdrop-blur-md"
            title="Open Knowledge Base"
          >
            <span>📁</span>
            <span>Knowledge Base ({documents.length})</span>
          </button>
        )}
      </div>

      {/* Dependency-free custom toast notifications portal */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col space-y-3 max-w-sm pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`flex items-start space-x-3 rounded-lg border p-4 shadow-2xl transition-all duration-300 transform translate-y-0 opacity-100 pointer-events-auto animate-slideUp bg-darkPanel ${
              toast.type === 'success'
                ? 'border-emerald-500/30 text-emerald-400'
                : toast.type === 'error'
                ? 'border-rose-500/30 text-rose-400'
                : toast.type === 'warning'
                ? 'border-amber-500/30 text-amber-400'
                : 'border-darkBorder text-userBubble'
            }`}
          >
            <span className="shrink-0 mt-0.5">
              {toast.type === 'success' && <CheckCircle className="h-4.5 w-4.5" />}
              {toast.type === 'error' && <AlertTriangle className="h-4.5 w-4.5 animate-bounce" />}
              {toast.type === 'warning' && <AlertTriangle className="h-4.5 w-4.5" />}
              {toast.type === 'info' && <Info className="h-4.5 w-4.5" />}
            </span>
            <div className="flex-1 text-xs font-semibold leading-normal">{toast.message}</div>
            <button
              onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
              className="text-gray-500 hover:text-white cursor-pointer transition-all duration-150 focus:outline-none"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
