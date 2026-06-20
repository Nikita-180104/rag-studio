import React, { useState } from 'react';
import { Trash2, Loader2 } from 'lucide-react';

/**
 * Cache control button with loading states.
 * Integrates into the navbar and allows clearing SQLite persistence caches.
 */
export default function CacheControl({ onClearCache, isOnline }) {
  const [clearing, setClearing] = useState(false);

  const handleClear = async () => {
    if (!isOnline || clearing) return;
    setClearing(true);
    try {
      await onClearCache();
    } catch (err) {
      console.error('Failed to clear cache:', err);
    } finally {
      setClearing(false);
    }
  };

  return (
    <button
      onClick={handleClear}
      disabled={!isOnline || clearing}
      title={!isOnline ? "Clear Cache disabled (Backend Offline)" : "Empty all cached query sessions"}
      className={`flex items-center space-x-2 rounded px-3.5 py-1.5 text-xs font-bold uppercase tracking-wider transition-all duration-200 border ${
        !isOnline
          ? 'bg-[#181C24] text-gray-600 border-darkBorder cursor-not-allowed'
          : clearing
          ? 'bg-[#181C24] text-gray-400 border-darkBorder cursor-wait'
          : 'bg-rose-950/20 text-rose-400 border-rose-900/30 hover:bg-rose-900/30 hover:border-rose-600/50 cursor-pointer shadow-md active:scale-95'
      }`}
    >
      {clearing ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <Trash2 className="h-3.5 w-3.5" />
      )}
      <span>{clearing ? 'Clearing...' : 'Clear Cache'}</span>
    </button>
  );
}
