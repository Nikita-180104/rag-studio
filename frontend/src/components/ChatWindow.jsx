import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, Loader2, Trash2 } from 'lucide-react';
import MessageBubble from './MessageBubble';

/**
 * Chat window containing the scrollable message log, empty-state helpers,
 * active loading status indicator, and prompt text inputs.
 */
export default function ChatWindow({ messages, loading, onSendMessage, isOnline, documents = [], onOpenKb, onClearChat }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Simple templates based on indexed filenames
  const getExampleQuestions = () => {
    if (!documents || documents.length === 0) {
      return [
        {
          title: "Standard Q&A",
          desc: "Retrieves answers directly from index",
          text: "What consensus engine does GroundLens AI run on?"
        },
        {
          title: "Unanswerable Q&A",
          desc: "Triggers pre-gen short-circuit gate",
          text: "What is the capital city of France?"
        },
        {
          title: "Multi-chunk Q&A",
          desc: "Synthesizes data across pages 1 and 3",
          text: "What consensus engine does GroundLens AI use, and how is its cross-node communication secured?"
        }
      ];
    }

    const filename = documents[0].filename;
    return [
      {
        title: "Coverage",
        desc: `Understand what ${filename} contains`,
        text: `What does ${filename} cover?`
      },
      {
        title: "Summarization",
        desc: "Extract key bullet points",
        text: `Summarize the key points in ${filename}`
      },
      {
        title: "Main Topic",
        desc: "Understand the core focus",
        text: `What is the main topic of ${filename}?`
      }
    ];
  };

  const exampleQuestions = getExampleQuestions();

  const handleSend = () => {
    if (!input.trim() || loading || !isOnline) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Automatically scrolls view to the bottom of the viewport
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="flex flex-1 flex-col bg-darkBg relative overflow-hidden">
      {/* Scrollable messages container */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 ? (
          /* Empty/Initial State Display */
          <div className="flex h-full flex-col items-center justify-center text-center max-w-4xl mx-auto py-12">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-600/10 border border-violet-500/20 mb-6 shadow-[0_0_20px_rgba(139,92,246,0.15)] animate-glow">
              <MessageSquare className="h-6 w-6 text-violet-400 text-glow-violet" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">GroundLens AI RAG Studio</h2>
            <p className="text-sm text-gray-400 mb-8 max-w-xl leading-relaxed">
              An enterprise-grade hybrid retrieval interface. Consults Chroma persistent vector blocks, applies Cross-Encoder compression, and enforces strict pre- and post-generation grounding guardrails.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 w-full">
              {exampleQuestions.map((q, idx) => (
                <button
                   key={idx}
                   onClick={() => setInput(q.text)}
                   disabled={!isOnline}
                   className="flex flex-col text-left p-5 rounded-xl glass-card text-sm cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shadow-xl active:scale-98"
                >
                  <span className="font-bold text-white mb-1.5 text-[10px] tracking-widest uppercase text-glow-violet">{q.title}</span>
                  <span className="text-xs text-gray-500 mb-4 font-semibold">{q.desc}</span>
                  <span className="text-xs font-mono text-violet-400 border-t border-darkBorder/40 pt-3 truncate w-full">{q.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Conversation Log viewport */
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <MessageBubble key={idx} message={msg} />
            ))}
            
            {/* Custom loader state card */}
            {loading && (
              <div className="flex items-start space-x-4 animate-pulse">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-600/10 border border-violet-500/20 shadow-lg">
                  <Loader2 className="h-4 w-4 animate-spin text-violet-400 text-glow-violet" />
                </div>
                <div className="flex flex-col space-y-2 flex-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">GroundLens AI Agent</span>
                  <div className="rounded-xl glass-panel border border-[#21262D]/60 px-5 py-4 text-sm text-gray-400 shadow-md">
                    Evaluating context scores, compressing chunks, and auditing factual grounding...
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input box bottom deck */}
      <div className="border-t border-darkBorder/50 glass-panel px-6 py-5 shadow-2xl backdrop-blur-xl">
        <div className="max-w-4xl mx-auto flex items-center space-x-3.5">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={!isOnline}
            placeholder={
              !isOnline 
                ? "FastAPI server unreachable. Re-connecting to localhost:8000..." 
                : "Ask a question about the systems architecture... (Press Enter to Send)"
            }
            rows={2}
            className="flex-1 resize-none h-16 rounded-xl bg-darkBg/60 border border-darkBorder/50 focus:border-violet-500/50 focus:outline-none px-4 py-3 text-sm text-white placeholder-gray-500 transition-all duration-200 focus:shadow-[0_0_20px_rgba(139,92,246,0.25)] focus:ring-1 focus:ring-violet-500/30 shadow-inner"
          />
          {onOpenKb && (
            <button
              onClick={onOpenKb}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#181C24]/60 hover:bg-[#181C24] border border-darkBorder hover:border-gray-500/50 text-gray-400 hover:text-white transition-all duration-200 cursor-pointer active:scale-90 shadow-lg"
              title="Open Knowledge Base Drawer"
            >
              <span className="text-md">📁</span>
            </button>
          )}
          {messages.length > 0 && onClearChat && (
            <button
              onClick={onClearChat}
              disabled={loading}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rose-600/10 hover:bg-rose-600/20 border border-rose-500/20 text-rose-400 hover:text-rose-300 transition-all duration-200 cursor-pointer active:scale-90 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              title="Clear Chat History"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading || !isOnline}
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-all duration-200 border ${
              !input.trim() || loading || !isOnline
                ? 'bg-[#181C24]/60 text-gray-600 border-darkBorder/40 cursor-not-allowed'
                : 'bg-violet-600 text-white border-violet-500 hover:bg-violet-500 shadow-[0_4px_12px_rgba(139,92,246,0.2)] hover:shadow-[0_4px_18px_rgba(139,92,246,0.35)] hover:-translate-y-0.5 active:translate-y-0 active:scale-90 cursor-pointer'
            }`}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
