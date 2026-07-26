import React, { useState } from 'react';
import { User, Terminal } from 'lucide-react';
import CitationCard from './CitationCard';

/**
 * Parses inline citations formatted as [Source: filename, Page: page]
 * and converts them into clickable, interactive UI chips.
 */
const parseInlineCitations = (text, citations = []) => {
  if (!text) return '';
  const regex = /\[Source:\s*([^,\]]+),\s*Page:\s*([^\]]+)\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    const matchIndex = match.index;
    if (matchIndex > lastIndex) {
      parts.push(text.substring(lastIndex, matchIndex));
    }

    const source = match[1].trim();
    const page = match[2].trim();

    // Click handler to highlight and scroll to the citation card
    const handleClick = () => {
      const element = document.getElementById(`citation-${source}-${page}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        element.classList.add('ring-2', 'ring-violet-500', 'animate-pulse');
        setTimeout(() => {
          element.classList.remove('ring-2', 'ring-violet-500', 'animate-pulse');
        }, 2000);
      }
    };

    parts.push(
      <span 
        key={matchIndex}
        onClick={handleClick}
        className="inline-flex items-center mx-0.5 px-1.5 py-0.5 rounded bg-violet-500/10 hover:bg-violet-500/25 text-violet-400 border border-violet-500/20 hover:border-violet-500/30 transition-all cursor-pointer font-mono text-[11px] select-none"
        title={`Source: ${source}, Page: ${page}`}
      >
        [{source.length > 18 ? source.substring(0, 15) + '...' : source} p.{page}]
      </span>
    );

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
};

/**
 * Message bubble representing a single dialogue transaction.
 * Renders user questions on the right and AI agent answers on the left.
 */
export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  // BUG 3: Hide red-scored citation cards (score < 2.0) by default
  const citations = message.citations || [];
  const nonRedCitations = citations.filter(c => c.re_rank_score >= 2.0);
  const redCitations = citations.filter(c => c.re_rank_score < 2.0);

  let citationsToUse = [];
  let isLowConfidence = false;

  if (nonRedCitations.length > 0) {
    citationsToUse = nonRedCitations;
  } else if (redCitations.length > 0) {
    // If ALL cards are red, show a maximum of 2
    citationsToUse = redCitations.slice(0, 2);
    isLowConfidence = true;
  }

  // Calculate unique documents count
  const uniqueDocsCount = new Set(citationsToUse.map(c => c.source)).size;

  const [showTelemetryDetails, setShowTelemetryDetails] = useState(false);
  const [showSources, setShowSources] = useState(uniqueDocsCount > 1);

  // Unicode bar relevance visualizer
  const getRelevanceBar = (score) => {
    if (score >= 5.0) return '█████';
    if (score >= 3.0) return '████░';
    if (score >= 1.0) return '███░░';
    if (score >= -2.0) return '██░░░';
    return '█░░░░';
  };

  return (
    <div className={`flex items-start space-x-4 ${
      isUser ? 'flex-row-reverse space-x-reverse' : ''
    } transition-all duration-300 animate-fadeIn`}>
      
      {/* User / Agent Avatar Badge */}
      <div className={`flex h-8.5 w-8.5 shrink-0 items-center justify-center rounded-xl shadow-lg border ${
        isUser 
          ? 'bg-violet-600/10 text-violet-400 border-violet-500/20 text-glow-violet shadow-[0_0_10px_rgba(139,92,246,0.1)]' 
          : 'bg-purple-600/10 text-purple-400 border-purple-500/20 text-glow-purple shadow-[0_0_10px_rgba(147,51,234,0.1)]'
      }`}>
        {isUser ? <User className="h-4.5 w-4.5" /> : <Terminal className="h-4.5 w-4.5" />}
      </div>

      {/* Message bubble context body */}
      <div className="flex flex-col space-y-2 max-w-[85%]">
        {/* Timestamp header */}
        <div className="flex items-center">
          <span className={`text-[9px] font-bold uppercase tracking-widest text-gray-500 ${
            isUser ? 'text-right' : 'text-left'
          }`}>
            {isUser ? 'You' : 'GroundLens AI Agent'}
          </span>
        </div>

        {/* Text body bubble */}
        <div className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-xl border whitespace-pre-wrap ${
          isUser 
            ? 'bg-gradient-to-br from-violet-600 to-violet-700 text-white border-violet-500/30 font-medium' 
            : 'glass-panel text-gray-200 border-darkBorder/40'
        }`}>
          {isUser ? message.text : parseInlineCitations(message.text, message.citations)}
        </div>

        {/* Collapsed inline telemetry stats bar (AI answers only) */}
        {!isUser && message.telemetry && (
          <div className="flex flex-col space-y-1.5 pt-1.5 pl-1.5">
            <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-[10px] font-bold text-gray-500 tracking-wider">
              <span className="flex items-center space-x-1 text-sky-400" title="Elapsed Time">
                <span>⚡</span>
                <span className="font-mono">
                  {message.telemetry.elapsed_seconds !== undefined 
                    ? `${message.telemetry.elapsed_seconds.toFixed(1)}s` 
                    : 'N/A'}
                </span>
              </span>
              <span className="text-darkBorder/85">|</span>
              <span className="flex items-center space-x-1 text-amber-400" title="Query Transaction Cost">
                <span>🪙</span>
                <span className="font-mono">
                  {message.telemetry.transaction_cost_usd !== undefined 
                    ? `$${message.telemetry.transaction_cost_usd.toFixed(6)}` 
                    : 'N/A'}
                </span>
              </span>
              <span className="text-darkBorder/85">|</span>
              <span className="flex items-center space-x-1 text-purple-400" title="Persistent Cache Status">
                <span>💾</span>
                <span className="font-mono">{message.telemetry.cached ? 'HIT' : 'MISS'}</span>
              </span>
              <span className="text-darkBorder/85">|</span>
              
              {/* Grounding indicator */}
              {(() => {
                const grounding = message.telemetry.l2_grounding_check;
                const isGrounded = grounding === "PASSED" || (grounding && grounding.startsWith("PASSED"));
                const isFailed = grounding === "FAILED" || (grounding && grounding.startsWith("FAILED"));
                if (isGrounded) {
                  return (
                    <span className="flex items-center space-x-1 text-emerald-400" title="Telemetry Grounding Level 2 Audit">
                      <span>✓</span>
                      <span>GROUNDED</span>
                    </span>
                  );
                } else if (isFailed) {
                  return (
                    <span className="flex items-center space-x-1 text-rose-400 animate-pulse" title="Telemetry Grounding Level 2 Audit">
                      <span>✗</span>
                      <span>UNGROUNDED</span>
                    </span>
                  );
                } else {
                  return (
                    <span className="flex items-center space-x-1 text-amber-500" title="Telemetry Grounding Level 2 Audit">
                      <span>⚠</span>
                      <span>UNCHECKED</span>
                    </span>
                  );
                }
              })()}
              
              <span className="text-darkBorder/85">|</span>
              <button 
                onClick={() => setShowTelemetryDetails(!showTelemetryDetails)}
                className="text-violet-400 hover:text-violet-300 font-extrabold cursor-pointer focus:outline-none transition-colors duration-150"
              >
                {showTelemetryDetails ? 'Hide Details' : 'Details'}
              </button>
            </div>

            {/* Expanded Telemetry details block */}
            {showTelemetryDetails && (
              <div className="mt-2.5 p-4 rounded-xl border border-darkBorder/30 bg-[#161B22]/40 backdrop-blur-md space-y-3 text-xs text-gray-400 font-semibold animate-fadeIn max-w-xl">
                <div className="grid grid-cols-2 gap-x-4 gap-y-2.5">
                  <div>
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold block">LLM Engine</span>
                    <span className="text-white font-mono">Groq LLaMA 3.1 70B</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold block">Prompt Version</span>
                    <span className="text-white font-mono">{message.telemetry.prompt_version || 'v3'}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold block">Token Ingest</span>
                    <span className="text-white font-mono">{message.telemetry.input_tokens || 0} in | {message.telemetry.output_tokens || 0} out</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold block">Re-ranking Threshold</span>
                    <span className="text-white font-mono">{message.telemetry.reranking_enabled ? 'Active (min score: 2.0)' : 'Disabled'}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold block">L1 Relevance Check</span>
                    <span className={`font-mono font-bold ${message.telemetry.l1_relevance_check === 'PASSED' ? 'text-emerald-400 text-glow-emerald' : 'text-rose-400 text-glow-rose'}`}>
                      {message.telemetry.l1_relevance_check || 'PENDING'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold block">L2 Grounding Check</span>
                    <span className={`font-mono font-bold ${message.telemetry.l2_grounding_check === 'PASSED' ? 'text-emerald-400 text-glow-emerald' : 'text-rose-400 text-glow-rose'}`}>
                      {message.telemetry.l2_grounding_check || 'PENDING'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Collapsible Sources list (AI answers only) */}
        {!isUser && citationsToUse.length > 0 && (
          <div className="flex flex-col space-y-2 pt-2">
            <button 
              onClick={() => setShowSources(!showSources)}
              className="text-[10px] font-bold uppercase tracking-wider text-gray-500 hover:text-white flex items-center space-x-1.5 focus:outline-none transition-colors duration-150 pl-1 w-fit cursor-pointer"
            >
              <span>{showSources ? '▼' : '▶'}</span>
              <span>Sources ({citationsToUse.length})</span>
              {isLowConfidence && (
                <span className="ml-1.5 text-[9px] font-extrabold text-rose-400 uppercase tracking-widest text-glow-rose normal-case">
                  (Low confidence sources)
                </span>
              )}
            </button>

            {showSources && (
              <ul className="pl-5 space-y-1.5 text-xs text-gray-400 border-l border-darkBorder/40 ml-2 py-1 animate-fadeIn">
                {citationsToUse.map((citation, idx) => {
                  const bar = getRelevanceBar(citation.re_rank_score);
                  let barColor = "text-rose-400";
                  if (citation.re_rank_score >= 5.0) barColor = "text-emerald-400";
                  else if (citation.re_rank_score >= 2.0) barColor = "text-amber-400";

                  return (
                    <li 
                      id={`citation-${citation.source}-${citation.page}`} 
                      key={idx}
                      className="transition-all duration-300 py-0.5 rounded px-2 hover:bg-darkBg/40 w-fit flex items-center space-x-2 border border-transparent"
                    >
                      <span className="text-gray-500">•</span>
                      <span className="text-gray-300 font-semibold">{citation.source}</span>
                      <span className="text-gray-500">—</span>
                      <span className="text-gray-400 font-mono">p. {citation.page}</span>
                      <span className="text-gray-500">—</span>
                      <span className="text-gray-500">score</span>
                      <span className={`font-mono leading-none tracking-widest ${barColor}`} title={`Score: ${citation.re_rank_score.toFixed(2)}`}>
                        {bar}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
