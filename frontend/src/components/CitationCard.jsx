import React from 'react';
import { FileText } from 'lucide-react';

/**
 * Truncates filename to specified length while preserving the extension.
 */
const truncateFilename = (name, maxLen = 25) => {
  if (!name) return 'Unknown';
  if (name.length <= maxLen) return name;
  const extIdx = name.lastIndexOf('.');
  if (extIdx !== -1 && name.length - extIdx < 8) {
    const ext = name.substring(extIdx);
    const base = name.substring(0, extIdx);
    return base.substring(0, maxLen - ext.length - 3) + '...' + ext;
  }
  return name.substring(0, maxLen - 3) + '...';
};

/**
 * Redesigned citation card displaying document source and page, with a visual re-rank score bar.
 */
export default function CitationCard({ citation }) {
  const score = citation.re_rank_score;
  
  const getScoreColorClass = (val) => {
    if (val > 5) return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]';
    if (val >= 2) return 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.3)]';
    return 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.3)]';
  };

  const getBarWidth = (val) => {
    if (val === undefined || val === null) return '5%';
    // Mapping score from -10 to 10 to a width percentage
    const min = -10;
    const max = 10;
    const pct = ((val - min) / (max - min)) * 100;
    return `${Math.min(Math.max(pct, 5), 100)}%`;
  };

  const cleanFilename = citation.source;
  const truncatedName = truncateFilename(cleanFilename, 25);

  return (
    <div className="flex flex-col rounded-xl bg-darkBg/60 border border-darkBorder/40 overflow-hidden text-xs shadow-lg p-3 min-w-[150px] max-w-[190px] hover:border-violet-500/30 transition-all duration-200">
      <div className="flex items-center space-x-2 mb-2">
        <FileText className="h-3.5 w-3.5 text-violet-400 shrink-0 text-glow-violet" />
        <span className="font-semibold text-gray-300 truncate" title={cleanFilename}>
          {truncatedName}
        </span>
      </div>
      
      <div className="flex justify-between items-center text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">
        <span>Page {citation.page}</span>
        <span className="text-[8px] tracking-widest text-gray-400">Re-rank</span>
      </div>

      {/* Visual Progress Bar */}
      <div className="w-full bg-[#181C24] rounded-full h-1.5 overflow-hidden border border-darkBorder/20">
        <div 
          className={`h-full rounded-full transition-all duration-300 ${getScoreColorClass(score)}`}
          style={{ width: getBarWidth(score) }}
        />
      </div>
    </div>
  );
}
