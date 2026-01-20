import React, { useState, useEffect, useRef } from 'react';
import { Play, Loader2, CheckCircle, AlertCircle, Terminal, FileJson, FileText, Download, Info, List, Grid } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';
import LeadDetailModal from './LeadDetailModal';
import ConsoleFooter from './ConsoleFooter';

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
  // Market Scraper specific state
  const [city, setCity] = useState('Madrid');
  const [maxItems, setMaxItems] = useState(10);

  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus['status']>('pending');
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<JobStatus['artifacts']>([]);
  const [leads, setLeads] = useState<any[]>([]);
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isConsoleOpen, setIsConsoleOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  // Polling logic
  useEffect(() => {
    if (!jobId) return;
    
    // Auto-open console on start
    if (status === 'running' && logs.length > 0 && !isConsoleOpen) {
        setIsConsoleOpen(true);
    }

    const pollInterval = setInterval(async () => {
      if (['complete', 'failed', 'cancelled'].includes(status)) {
          clearInterval(pollInterval);
          return;
      }

      try {
        const res = await fetch(`http://127.0.0.1:5000/api/miniapps/${appId}/status/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch status');
        
        const data: JobStatus = await res.json();
        
        setStatus(data.status);
        if (data.logs && data.logs.length > logs.length) {
            setLogs(data.logs);
        }
        
        if (data.status === 'failed') {
          setError(data.error || 'Unknown error occurred');
        }
        
        if (data.status === 'complete') {
            setArtifacts(data.artifacts);
        }

        if (appId === 'market_scraper_privados') {
            const leadsRes = await fetch(`http://127.0.0.1:5000/api/miniapps/${appId}/jobs/${jobId}/leads`);
            if (leadsRes.ok) {
                const leadsData = await leadsRes.json();
                setLeads(leadsData);
            }
        }

      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [jobId, status, appId, logs.length]);

  const handleRun = async () => {
    // Validate inputs
    if (appId === 'market_scraper_privados' && !city) return;
    if (appId !== 'market_scraper_privados' && !inputUrl) return;
    
    setStatus('running');
    setLogs(['Starting job...']);
    setError(null);
    setArtifacts([]);
    setLeads([]);
    setIsConsoleOpen(true); // Open console when starting
    
    try {
      let bodyData: any = { variant: 1 };
      
      if (appId === 'market_scraper_privados') {
          bodyData = { ...bodyData, city, max_items: maxItems };
      } else {
          bodyData = { ...bodyData, input: inputUrl };
      }

      const res = await fetch(`http://127.0.0.1:5000/api/miniapps/${appId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
      });
      
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.error || 'Failed to start job');
      
      setJobId(data.job_id);
      
    } catch (err: any) {
      setStatus('failed');
      setError(err.message);
      setLogs(prev => [...prev, `Error: ${err.message}`]);
    }
  };

  const handleLeadUpdate = async (leadId: number, updates: any) => {
    try {
        await fetch(`http://127.0.0.1:5000/api/miniapps/market_scraper_privados/leads/${leadId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        setLeads(prev => prev.map(l => l.id === leadId ? { ...l, ...updates } : l));
        if (selectedLead?.id === leadId) {
            setSelectedLead(prev => ({ ...prev, ...updates }));
        }
    } catch (err) {
        console.error("Failed to update lead", err);
    }
  };

  const openLeadDetail = (lead: any) => {
      setSelectedLead(lead);
      setIsModalOpen(true);
  };

  const isRunning = status === 'running';
  const canRun = appId === 'market_scraper_privados' ? !!city : !!inputUrl;

  return (
    <div className="flex flex-col gap-6 pb-24"> {/* Add padding bottom for footer */}
      <LeadDetailModal 
        lead={selectedLead} 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onUpdate={handleLeadUpdate}
      />

      {/* Input Section */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        {appId === 'market_scraper_privados' ? (
            <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-100 dark:border-blue-800">
                <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-2">¿Cómo funciona?</h3>
                <p className="text-sm text-blue-700 dark:text-blue-200 leading-relaxed">
                    1. Escriba la <strong>Ciudad</strong> donde busca piso (ej. "Madrid").<br/>
                    2. Elija <strong>cuántos anuncios</strong> quiere que revisemos.<br/>
                    3. Pulse <strong>"Buscar Particulares"</strong>.<br/>
                    <span className="block mt-2 opacity-80">El sistema buscará en internet y le mostrará aquí abajo solo los que parecen ser dueños directos (sin comisión de agencia).</span>
                </p>
            </div>
        ) : (
            <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        )}
        
        <div className="flex flex-wrap gap-4 items-end">
          {appId === 'market_scraper_privados' ? (
            <>
              <div className="flex-1 min-w-[200px] space-y-2">
                <label className="text-sm font-medium">Ciudad o Zona</label>
                <input
                  type="text"
                  placeholder="Ej: Madrid, Barcelona, Valencia..."
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="flex h-12 w-full rounded-md border border-input bg-background px-4 py-2 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-sm"
                />
              </div>
              <div className="w-32 space-y-2">
                <label className="text-sm font-medium">Nº anuncios</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={maxItems}
                  onChange={(e) => setMaxItems(parseInt(e.target.value))}
                  className="flex h-12 w-full rounded-md border border-input bg-background px-4 py-2 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-sm"
                />
              </div>
            </>
          ) : (
            <input
              type="url"
              placeholder="Enter listing URL (e.g. https://example.com/property)"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
          )}
          
          <Button 
            onClick={handleRun} 
            disabled={isRunning || !canRun}
            className={cn("h-12 px-6 font-semibold shadow-md", appId === 'market_scraper_privados' ? "w-auto min-w-[180px]" : "w-32")}
            size="lg"
          >
            {isRunning ? (
              <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Buscando...</>
            ) : (
              <><Play className="mr-2 h-5 w-5" /> {appId === 'market_scraper_privados' ? 'Buscar' : 'Run'}</>
            )}
          </Button>
        </div>
      </div>

      {/* Leads Area (Market Scraper Only) */}
      {appId === 'market_scraper_privados' && leads.length > 0 && (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold flex items-center gap-3 text-green-700 dark:text-green-400">
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                    Pisos de Particulares ({leads.length})
                </h2>
                <div className="flex bg-muted rounded-lg p-1">
                    <button 
                        onClick={() => setViewMode('grid')}
                        className={cn("p-1.5 rounded transition-all", viewMode === 'grid' ? "bg-background shadow-sm" : "hover:bg-background/50")}
                    >
                        <Grid className="w-4 h-4" />
                    </button>
                    <button 
                        onClick={() => setViewMode('list')}
                        className={cn("p-1.5 rounded transition-all", viewMode === 'list' ? "bg-background shadow-sm" : "hover:bg-background/50")}
                    >
                        <List className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className={cn(
                "gap-4",
                viewMode === 'grid' ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2" : "flex flex-col"
            )}>
                {leads.map((lead, i) => (
                    <div key={i} 
                        onClick={() => openLeadDetail(lead)}
                        className={cn(
                            "rounded-xl border bg-white dark:bg-card hover:shadow-md transition-all duration-300 group cursor-pointer relative",
                            viewMode === 'list' ? "flex items-center p-3 gap-4" : "flex flex-col p-5",
                            lead.status === 'rejected' ? "border-red-200 bg-red-50/50 opacity-60" : 
                            lead.status === 'called' ? "border-green-200 bg-green-50/50" :
                            "border-border hover:border-primary/50"
                        )}
                    >
                        {/* List Mode Layout */}
                        {viewMode === 'list' ? (
                            <>
                                <div className="w-24 shrink-0">
                                    <span className="text-xs font-bold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase">{lead.source}</span>
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h3 className="font-semibold truncate">{lead.parsed_data?.title || 'Sin Título'}</h3>
                                    <div className="text-xs text-muted-foreground truncate">{lead.notes || 'Sin notas'}</div>
                                </div>
                                <div className="w-24 font-bold text-right">
                                    {lead.parsed_data?.price || 'N/A'}
                                </div>
                                <div className="w-24 text-right">
                                    <span className={cn(
                                        "text-xs px-2 py-1 rounded-full font-semibold border inline-block",
                                        lead.status === 'new' ? "bg-green-100 text-green-800 border-green-200" :
                                        lead.status === 'seen' ? "bg-yellow-100 text-yellow-800 border-yellow-200" :
                                        lead.status === 'called' ? "bg-blue-100 text-blue-800 border-blue-200" :
                                        "bg-gray-100 text-gray-800 border-gray-200"
                                    )}>
                                        {lead.status === 'new' ? 'Nuevo' : 
                                         lead.status === 'seen' ? 'Visto' :
                                         lead.status === 'called' ? 'Llamado' : 'Desc.'}
                                    </span>
                                </div>
                            </>
                        ) : (
                            /* Grid Mode Layout (Existing) */
                            <>
                                <div className="flex justify-between items-start mb-3">
                                    <span className="text-xs font-bold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider">{lead.source}</span>
                                    <div className="flex gap-2">
                                        {lead.notes && (
                                            <div className="group/tooltip relative">
                                                <Info className="w-5 h-5 text-blue-500" />
                                                <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-black text-white text-xs rounded shadow-lg hidden group-hover/tooltip:block z-10 pointer-events-none">
                                                    {lead.notes}
                                                </div>
                                            </div>
                                        )}
                                        <span className={cn(
                                            "text-xs px-3 py-1 rounded-full font-semibold border",
                                            lead.status === 'new' ? "bg-green-100 text-green-800 border-green-200" :
                                            lead.status === 'seen' ? "bg-yellow-100 text-yellow-800 border-yellow-200" :
                                            lead.status === 'called' ? "bg-blue-100 text-blue-800 border-blue-200" :
                                            "bg-gray-100 text-gray-800 border-gray-200"
                                        )}>
                                            {lead.status === 'new' ? 'Nuevo' : 
                                             lead.status === 'seen' ? 'Visto' :
                                             lead.status === 'called' ? 'Llamado' : 'Descartado'}
                                        </span>
                                    </div>
                                </div>
                                
                                <h3 className="font-semibold text-lg mb-1 line-clamp-1 group-hover:text-primary transition-colors">{lead.parsed_data?.title || 'Sin Título'}</h3>
                                <div className="text-2xl font-bold text-slate-900 dark:text-white mb-3">{lead.parsed_data?.price || 'Precio N/A'}</div>
                                
                                <div className="grid grid-cols-2 gap-3 text-sm text-slate-600 dark:text-slate-400 mb-4 bg-slate-50 dark:bg-slate-900/50 p-3 rounded-lg">
                                    <div>
                                        <span className="block text-xs font-semibold uppercase opacity-70 mb-1">Contacto</span>
                                        <span className="font-medium text-slate-900 dark:text-slate-200">{lead.contact_name || 'No detectado'}</span>
                                    </div>
                                    <div>
                                        <span className="block text-xs font-semibold uppercase opacity-70 mb-1">Teléfono</span>
                                        <span className="font-medium text-slate-900 dark:text-slate-200">{lead.contact_phone || 'No detectado'}</span>
                                    </div>
                                </div>
                                
                                <div className="mt-auto pt-2 text-xs text-center text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                                    Clic para ver detalles
                                </div>
                            </>
                        )}
                    </div>
                ))}
            </div>
        </div>
      )}

      {/* Artifacts (Standard) */}
      {artifacts && artifacts.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Resultados Finales
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {artifacts.map((artifact, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/50 hover:bg-muted transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-background flex items-center justify-center border border-border text-foreground">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{artifact.label || artifact.filename}</div>
                    <div className="text-xs text-muted-foreground uppercase">{artifact.type}</div>
                  </div>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <a href={`http://127.0.0.1:5000/api/miniapps/${appId}/artifact/${jobId}/${artifact.path.split('/').pop()}`} download>
                    <Download className="w-4 h-4 mr-2" />
                    Descargar CSV
                  </a>
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fixed Console Footer */}
      <ConsoleFooter 
        logs={logs} 
        status={status} 
        isOpen={isConsoleOpen} 
        onToggle={() => setIsConsoleOpen(!isConsoleOpen)} 
      />
    </div>
  );
}
