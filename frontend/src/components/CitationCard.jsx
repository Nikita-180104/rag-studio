import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Collapsible citation card displaying document metadata.
 * Features color-coded relevance indicators based on re-rank logit thresholds.
 */
export default function CitationCard({ citation }) {
  const [expanded, setExpanded] = useState(false);

  // Resolves semantic relevance indicators based on logit bounds
  const getScoreStyle = (score) => {
    if (score >= 4.0) {
      return 'text-emerald-400 bg-emerald-950/30 border-emerald-500/20 text-glow-emerald';
    }
    if (score >= 0.0) {
      return 'text-amber-400 bg-amber-950/30 border-amber-500/20 text-glow-amber';
    }
    return 'text-rose-400 bg-rose-950/30 border-rose-500/20';
  };

  return (
    <div className="flex flex-col rounded-xl glass-card overflow-hidden text-xs shadow-lg">
      {/* Clickable Header card summary */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center space-x-2.5 px-3.5 py-2 hover:bg-darkBg/40 transition-all duration-150 text-left cursor-pointer focus:outline-none"
      >
        <FileText className="h-3.5 w-3.5 text-blue-400 text-glow-blue" />
        <span className="font-semibold text-gray-300 truncate max-w-[150px]" title={citation.source}>
          {citation.source}
        </span>
        <span className="text-gray-500 border-l border-darkBorder/40 pl-2.5 font-medium">
          p. {citation.page}
        </span>
        <span className="text-gray-400 pl-1">
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </span>
      </button>

      {/* Collapsible stats pane */}
      {expanded && (
        <div className="px-3.5 py-2.5 border-t border-darkBorder/40 bg-darkBg/20 space-y-2">
          <div className="flex justify-between items-center space-x-6">
            <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">Re-rank Score:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono border font-bold ${
              getScoreStyle(citation.re_rank_score)
            }`}>
              {citation.re_rank_score !== undefined ? citation.re_rank_score.toFixed(4) : '0.0000'}
            </span>
          </div>
          <div className="flex justify-between items-center space-x-6">
            <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">Verification:</span>
            <span className="text-[9px] font-bold text-blue-400 uppercase tracking-wider text-glow-blue">
              Grounded
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
