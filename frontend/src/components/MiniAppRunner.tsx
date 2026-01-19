import React, { useState, useEffect, useRef } from 'react';
import { Play, Loader2, CheckCircle, AlertCircle, Terminal, FileJson, FileText, Download } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';

interface MiniAppRunnerProps {
  appId: string;
}

interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'cancelled';
  logs: string[];
  error?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  result?: any;
  artifacts?: Array<{
    type: string;
    label: string;
    path: string;
    filename?: string;
  }>;
}

export default function MiniAppRunner({ appId }: MiniAppRunnerProps) {
  const [inputUrl, setInputUrl] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus['status']>('pending');
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<JobStatus['artifacts']>([]);
  
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Polling logic
  useEffect(() => {
    if (!jobId || ['complete', 'failed', 'cancelled'].includes(status)) return;

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:5000/api/miniapps/${appId}/status/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch status');
        
        const data: JobStatus = await res.json();
        
        setStatus(data.status);
        setLogs(data.logs || []);
        
        if (data.status === 'failed') {
          setError(data.error || 'Unknown error occurred');
        }
        
        if (data.status === 'complete') {
            // Fetch artifacts if complete (usually included in status but just in case)
            // In our API design, status endpoint doesn't return artifacts by default? 
            // Actually artifacts are in the Job object, so they should be there.
            // Let's assume the API returns them or we need another call.
            // Based on backend implementation: to_dict includes artifacts.
            setArtifacts(data.artifacts);
        }

      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [jobId, status, appId]);

  const handleRun = async () => {
    if (!inputUrl) return;
    
    setStatus('running');
    setLogs(['Starting job...']);
    setError(null);
    setArtifacts([]);
    
    try {
      const res = await fetch(`http://127.0.0.1:5000/api/miniapps/${appId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: inputUrl, variant: 1 })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || 'Failed to start job');
      }
      
      setJobId(data.job_id);
      
    } catch (err: any) {
      setStatus('failed');
      setError(err.message);
      setLogs(prev => [...prev, `Error: ${err.message}`]);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Input Section */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        <div className="flex gap-3">
          <input
            type="url"
            placeholder="Enter listing URL (e.g. https://example.com/property)"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
          <Button 
            onClick={handleRun} 
            disabled={status === 'running' || !inputUrl}
            className="w-32"
          >
            {status === 'running' ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Running</>
            ) : (
              <><Play className="mr-2 h-4 w-4" /> Run</>
            )}
          </Button>
        </div>
      </div>

      {/* Logs Console */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col h-[400px]">
        <div className="bg-muted px-4 py-3 border-b border-border flex justify-between items-center">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Terminal className="w-4 h-4" />
            Execution Logs
          </div>
          <div className={cn(
            "text-xs px-2 py-1 rounded-full font-medium capitalize flex items-center gap-1.5",
            status === 'running' ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" :
            status === 'complete' ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
            status === 'failed' ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
            "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400"
          )}>
            {status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
            {status === 'complete' && <CheckCircle className="w-3 h-3" />}
            {status === 'failed' && <AlertCircle className="w-3 h-3" />}
            {status}
          </div>
        </div>
        <div className="flex-1 overflow-auto bg-black p-4 font-mono text-xs text-green-400">
          {logs.length === 0 ? (
            <span className="text-slate-500 italic">Waiting to start...</span>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="mb-1 break-all border-b border-white/5 pb-1 last:border-0 last:pb-0">
                <span className="opacity-50 mr-2">{log.substring(0, 10)}</span>
                {log.substring(11)}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Results / Artifacts */}
      {artifacts && artifacts.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Generated Results
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {artifacts.map((artifact, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/50 hover:bg-muted transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-background flex items-center justify-center border border-border text-foreground">
                    {artifact.type === 'json' ? <FileJson className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
                  </div>
                  <div>
                    <div className="font-medium text-sm">{artifact.label || artifact.filename}</div>
                    <div className="text-xs text-muted-foreground uppercase">{artifact.type}</div>
                  </div>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <a href={`http://127.0.0.1:5000/api/miniapps/${appId}/artifact/${jobId}/${artifact.path.split('/').pop()}`} download>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </a>
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
