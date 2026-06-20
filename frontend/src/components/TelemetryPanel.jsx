import React from 'react';
import { Clock, Coins, ShieldAlert, HelpCircle } from 'lucide-react';

/**
 * Collapsible side-panel containing granular execution metrics,
 * token diagnostics, financial summaries, and two-layer guardrail status badges.
 */
export default function TelemetryPanel({ telemetry, isOpen, onClose }) {
  if (!isOpen) return null;

  // Resolves color-coded status badges for grounding check gates
  const getGuardrailStyle = (status) => {
    if (!status) return 'bg-[#181C24]/60 text-gray-500 border-darkBorder/40';
    const s = status.toUpperCase();
    if (s.includes('PASS')) {
      return 'bg-emerald-950/30 text-emerald-400 border-emerald-500/20 text-glow-emerald';
    }
    if (s.includes('FAIL')) {
      return 'bg-rose-950/30 text-rose-400 border-rose-500/20';
    }
    return 'bg-[#181C24]/60 text-gray-400 border-[#30363D]/40';
  };

  return (
    <aside className="w-80 border-l border-darkBorder/50 glass-panel flex flex-col h-full overflow-y-auto shrink-0 shadow-[0_0_35px_rgba(0,0,0,0.3)] animate-slideLeft backdrop-blur-xl">
      {/* Side rail header deck */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-darkBorder/50 bg-darkBg/30">
        <div className="flex items-center space-x-2.5 text-white">
          <HelpCircle className="h-4.5 w-4.5 text-blue-400 text-glow-blue animate-glow" />
          <h2 className="font-bold tracking-widest text-xs uppercase">Query Telemetry</h2>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-[10px] font-bold uppercase tracking-widest cursor-pointer transition-all duration-150 focus:outline-none"
        >
          Close
        </button>
      </div>

      {/* Telemetry body deck */}
      <div className="flex-1 p-6 space-y-6">
        {!telemetry ? (
          /* Empty side-rail panel view */
          <div className="h-full flex flex-col items-center justify-center text-center py-24 text-gray-500 max-w-[220px] mx-auto">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gray-500/5 border border-darkBorder/30 mb-4">
              <ShieldAlert className="h-5 w-5 text-gray-500" />
            </div>
            <p className="text-xs leading-relaxed text-gray-500 font-medium">
              No active query telemetry. Execute a question prompt to benchmark operational statistics.
            </p>
          </div>
        ) : (
          /* Structured metric list */
          <div className="space-y-6 text-sm">
            {/* Cache Status Heartbeat */}
            <div className="flex flex-col space-y-2.5 border-b border-darkBorder/40 pb-5">
              <span className="text-[9px] text-gray-500 uppercase tracking-widest font-bold">Cache Status:</span>
              <div className="flex items-center justify-between">
                <span className={`inline-flex rounded-md px-3 py-0.5 text-xs font-bold uppercase tracking-wider border ${
                  telemetry.cached
                    ? 'bg-emerald-950/30 text-emerald-400 border-emerald-500/20 text-glow-emerald'
                    : 'bg-rose-950/30 text-rose-400 border-rose-500/20'
                }`}>
                  {telemetry.cached ? 'Cache HIT' : 'Cache MISS'}
                </span>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-gray-400 bg-darkBg/60 px-2 py-0.5 rounded border border-darkBorder/20">
                  {telemetry.provider}
                </span>
              </div>
            </div>

            {/* Latency card details */}
            <div className="flex items-center justify-between border-b border-darkBorder/40 pb-5">
              <div className="flex items-center space-x-2.5">
                <Clock className="h-4 w-4 text-emerald-400 text-glow-emerald" />
                <span className="text-xs text-gray-400 font-medium">Response Latency:</span>
              </div>
              <span className="font-mono font-bold text-white text-sm text-glow-emerald">
                {telemetry.elapsed_seconds !== undefined ? `${telemetry.elapsed_seconds.toFixed(4)}s` : '0.0000s'}
              </span>
            </div>

            {/* Financial cost metrics card */}
            <div className="space-y-3.5 border-b border-darkBorder/40 pb-5">
              <div className="flex items-center space-x-2.5">
                <Coins className="h-4 w-4 text-amber-400 text-glow-amber" />
                <span className="text-xs text-gray-400 font-medium">Cost Telemetry:</span>
              </div>
              <div className="grid grid-cols-2 gap-3 pl-6.5">
                <div className="flex flex-col bg-darkBg/40 p-2.5 rounded-lg border border-darkBorder/20">
                  <span className="text-[9px] text-gray-500 uppercase font-bold tracking-wider">Input Tokens:</span>
                  <span className="font-mono text-white font-bold text-xs mt-0.5">{telemetry.input_tokens || 0}</span>
                </div>
                <div className="flex flex-col bg-darkBg/40 p-2.5 rounded-lg border border-darkBorder/20">
                  <span className="text-[9px] text-gray-500 uppercase font-bold tracking-wider">Output Tokens:</span>
                  <span className="font-mono text-white font-bold text-xs mt-0.5">{telemetry.output_tokens || 0}</span>
                </div>
              </div>
              <div className="flex justify-between items-center pl-6.5 pt-3 border-t border-darkBorder/20">
                <span className="text-[9px] text-gray-500 uppercase font-bold tracking-wider">Financial Cost:</span>
                <span className="font-mono text-amber-400 font-bold text-xs text-glow-amber">
                  ${telemetry.transaction_cost_usd !== undefined ? telemetry.transaction_cost_usd.toFixed(8) : '0.00000000'} USD
                </span>
              </div>
            </div>

            {/* Factual audit checklist */}
            <div className="space-y-3.5 pb-4">
              <div className="flex items-center space-x-2.5">
                <ShieldAlert className="h-4 w-4 text-purple-400 text-glow-purple" />
                <span className="text-xs text-gray-400 font-medium">Guardrail Checklist:</span>
              </div>
              <div className="space-y-2.5 pl-6.5">
                <div className="flex justify-between items-center">
                  <span className="text-[9px] text-gray-500 uppercase font-semibold">Layer 1 (Pre-Gen):</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${
                    getGuardrailStyle(telemetry.l1_relevance_check)
                  }`}>
                    {telemetry.l1_relevance_check || 'SKIPPED'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[9px] text-gray-500 uppercase font-semibold">Layer 2 (Post-Gen):</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${
                    getGuardrailStyle(telemetry.l2_grounding_check)
                  }`}>
                    {telemetry.l2_grounding_check || 'SKIPPED'}
                  </span>
                </div>
              </div>
            </div>
            
            {/* System config metadata */}
            <div className="pt-4 border-t border-darkBorder/40 text-[10px] text-gray-500 space-y-1.5 font-bold uppercase tracking-widest bg-darkBg/20 p-3 rounded-lg border border-darkBorder/20">
              <div><span className="font-bold text-gray-600">Prompt:</span> {telemetry.prompt_version || 'v1'}</div>
              <div><span className="font-bold text-gray-600">Re-rank:</span> {telemetry.reranking_enabled ? 'Enabled' : 'Disabled'}</div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
