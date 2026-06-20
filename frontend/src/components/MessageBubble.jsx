import React from 'react';
import { User, Terminal } from 'lucide-react';
import CitationCard from './CitationCard';

/**
 * Message bubble representing a single dialogue transaction.
 * Renders user questions on the right and AI agent answers on the left.
 */
export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start space-x-4 ${
      isUser ? 'flex-row-reverse space-x-reverse' : ''
    } transition-all duration-300 animate-fadeIn`}>
      
      {/* User / Agent Avatar Badge */}
      <div className={`flex h-8.5 w-8.5 shrink-0 items-center justify-center rounded-xl shadow-lg border ${
        isUser 
          ? 'bg-blue-600/10 text-blue-400 border-blue-500/20 text-glow-blue shadow-[0_0_10px_rgba(31,111,235,0.1)]' 
          : 'bg-purple-600/10 text-purple-400 border-purple-500/20 text-glow-purple shadow-[0_0_10px_rgba(147,51,234,0.1)]'
      }`}>
        {isUser ? <User className="h-4.5 w-4.5" /> : <Terminal className="h-4.5 w-4.5" />}
      </div>

      {/* Message bubble context body */}
      <div className="flex flex-col space-y-2 max-w-[85%]">
        {/* Timestamp header */}
        <span className={`text-[9px] font-bold uppercase tracking-widest text-gray-500 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {isUser ? 'You' : 'Antigravity AI Agent'}
        </span>

        {/* Text body bubble */}
        <div className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-xl border whitespace-pre-wrap ${
          isUser 
            ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white border-blue-500/30 font-medium' 
            : 'glass-panel text-gray-200 border-darkBorder/40'
        }`}>
          {message.text}
        </div>

        {/* Citation cards deck (AI answers only) */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="flex flex-col space-y-2 pt-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 pl-1">
              Grounded Source Citations:
            </span>
            <div className="flex flex-wrap gap-2">
              {message.citations.map((citation, idx) => (
                <CitationCard key={idx} citation={citation} idx={idx} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
