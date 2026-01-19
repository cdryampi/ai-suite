import React, { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';

export default function SystemStatus() {
  const [status, setStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        // In dev, we assume backend is at port 5000
        const res = await fetch('http://127.0.0.1:5000/api/health');
        if (res.ok) {
          const data = await res.json();
          setStatus('online');
          setVersion(data.version || 'v0.1.0');
        } else {
          setStatus('offline');
        }
      } catch (e) {
        setStatus('offline');
      }
    };

    checkHealth();
    // Poll every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-2 h-2 rounded-full ${
          status === 'online' ? 'bg-green-500 animate-pulse' : 
          status === 'checking' ? 'bg-yellow-500' : 'bg-red-500'
        }`}></div>
        <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
          {status === 'online' ? 'System Online' : 
           status === 'checking' ? 'Checking...' : 'System Offline'}
        </span>
      </div>
      <div className="text-xs text-slate-500 dark:text-slate-400 flex justify-between items-center">
        <span>{version || 'Unknown Version'}</span>
        {status === 'offline' && (
          <Activity className="w-3 h-3 text-red-400" />
        )}
      </div>
    </div>
  );
}
