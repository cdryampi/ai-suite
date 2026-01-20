import React, { useState, useEffect, useRef } from 'react';
import { Terminal, ChevronUp, ChevronDown, X, Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './ui/button';

interface ConsoleFooterProps {
  logs: string[];
  status: string;
  isOpen: boolean;
  onToggle: () => void;
}

export default function ConsoleFooter({ logs, status, isOpen, onToggle }: ConsoleFooterProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [isMaximized, setIsMaximized] = useState(false);

  // Auto-scroll logs
  useEffect(() => {
    if (isOpen) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isOpen]);

  return (
    <div 
      className={cn(
        "fixed bottom-0 left-0 right-0 bg-black border-t border-white/10 z-40 transition-all duration-300 shadow-2xl flex flex-col",
        isOpen ? (isMaximized ? "h-[80vh]" : "h-64") : "h-10"
      )}
    >
      {/* Header / Tabs */}
      <div 
        className="h-10 bg-[#1e1e1e] flex items-center justify-between px-4 cursor-pointer hover:bg-[#2d2d2d] transition-colors border-b border-white/5"
        onClick={onToggle}
      >
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-medium text-blue-400 uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" />
            Terminal Output
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              "w-2 h-2 rounded-full",
              status === 'running' ? "bg-blue-500 animate-pulse" :
              status === 'complete' ? "bg-green-500" :
              status === 'failed' ? "bg-red-500" : "bg-slate-500"
            )} />
            <span className="text-xs text-slate-400 capitalize">{status}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {isOpen && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-6 w-6 p-0 hover:bg-white/10 text-slate-400"
              onClick={(e) => { e.stopPropagation(); setIsMaximized(!isMaximized); }}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </Button>
          )}
          <div className="text-slate-400">
            {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden relative font-mono text-xs">
        <div className="absolute inset-0 overflow-auto p-4 space-y-1">
          {logs.length === 0 ? (
            <div className="text-slate-500 italic p-2">Ready to start...</div>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex gap-3 text-slate-300 hover:bg-white/5 px-2 py-0.5 rounded">
                <span className="text-slate-600 select-none w-16 text-right shrink-0">{log.substring(1, 9)}</span>
                <span className={cn(
                  "break-all",
                  log.toLowerCase().includes('error') ? "text-red-400" : 
                  log.toLowerCase().includes('success') || log.includes('finished') ? "text-green-400" :
                  log.toLowerCase().includes('warning') ? "text-yellow-400" : "text-slate-300"
                )}>
                  {log.substring(11).replace(/^]/, '')}
                </span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}
