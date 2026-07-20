import React from 'react';
import { Activity, Database, Cpu } from 'lucide-react';
import CacheControl from './CacheControl';

/**
 * Top Navbar displaying real-time operational metrics, connection status,
 * configuration parameters, and cache controls.
 */
export default function HealthBar({ health, isOnline, onClearCache }) {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-4.5 shadow-2xl glass-panel border-b border-darkBorder/50 backdrop-blur-xl">
      {/* Brand logo & title */}
      <div className="flex items-center space-x-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600/10 border border-blue-500/30 shadow-[0_0_15px_rgba(31,111,235,0.15)] animate-glow">
          <Cpu className="h-5 w-5 text-blue-400 text-glow-blue" />
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Workspace Monitor</span>
          <h1 className="text-md font-bold tracking-tight text-white -mt-0.5">GroundLens AI RAG Studio</h1>
        </div>
      </div>

      {/* Health status & systems badges */}
      <div className="flex items-center space-x-6">
        {/* Heartbeat Status Indicator */}
        <div className="flex items-center space-x-2.5 bg-darkBg/60 px-3.5 py-1.5 rounded-full border border-darkBorder/30">
          <span className="relative flex h-2 w-2">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
              isOnline ? 'bg-emerald-400' : 'bg-rose-400'
            }`}></span>
            <span className={`relative inline-flex h-2 w-2 rounded-full ${
              isOnline ? 'bg-emerald-500' : 'bg-rose-500'
            }`}></span>
          </span>
          <span className={`text-[10px] font-bold tracking-widest uppercase ${
            isOnline ? 'text-emerald-400 text-glow-emerald' : 'text-rose-400 text-glow-rose'
          }`}>
            {isOnline ? 'Active' : 'Offline'}
          </span>
        </div>

        {/* Active Vector Store Engine */}
        {isOnline && health && (
          <div className="hidden items-center space-x-2 border-l border-darkBorder/40 pl-6 md:flex">
            <Database className="h-4 w-4 text-gray-400" />
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Vector DB:</span>
            <span className="rounded bg-blue-950/20 px-2.5 py-0.5 text-xs font-bold font-mono uppercase tracking-wider text-blue-400 border border-blue-500/20 text-glow-blue">
              {health.vector_db_provider || 'Chroma'}
            </span>
          </div>
        )}

        {/* Active Prompt Configurations Version */}
        {isOnline && health && (
          <div className="hidden items-center space-x-2 border-l border-darkBorder/40 pl-6 md:flex">
            <Activity className="h-4 w-4 text-gray-400" />
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Prompt Schema:</span>
            <span className="rounded bg-purple-950/20 px-2.5 py-0.5 text-xs font-bold font-mono uppercase tracking-wider text-purple-400 border border-purple-500/20 text-glow-purple">
              {health.active_prompt_version || 'v1'}
            </span>
          </div>
        )}

        {/* Cache Clearing Integration Button */}
        <div className="border-l border-darkBorder/40 pl-6">
          <CacheControl onClearCache={onClearCache} isOnline={isOnline} />
        </div>
      </div>
    </header>
  );
}
