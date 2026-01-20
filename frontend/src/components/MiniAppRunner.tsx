import React, { useState, useEffect, useRef } from 'react';
import { Play, Loader2, CheckCircle, AlertCircle, Terminal, FileJson, FileText, Download, Info } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';
import LeadDetailModal from './LeadDetailModal';

interface MiniAppRunnerProps {
  appId: string;
}
// ... existing types ...

export default function MiniAppRunner({ appId }: MiniAppRunnerProps) {
  // ... existing state ...
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // ... existing useEffects ...

  const handleLeadUpdate = async (leadId: number, updates: any) => {
    try {
        await fetch(`http://127.0.0.1:5000/api/miniapps/market_scraper_privados/leads/${leadId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        // Update local state to reflect changes immediately
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

  // ... existing handleRun ...

  return (
    <div className="flex flex-col gap-6">
      <LeadDetailModal 
        lead={selectedLead} 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onUpdate={handleLeadUpdate}
      />
      
      {/* ... existing Input Section & Logs ... */}

      {/* Leads Grid (Market Scraper Only) */}
      {appId === 'market_scraper_privados' && leads.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-3 text-green-700 dark:text-green-400">
                <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                Pisos de Particulares Encontrados ({leads.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {leads.map((lead, i) => (
                    <div key={i} 
                        onClick={() => openLeadDetail(lead)}
                        className={cn(
                            "flex flex-col p-5 rounded-xl border bg-white dark:bg-card hover:shadow-md transition-all duration-300 group cursor-pointer relative",
                            lead.status === 'rejected' ? "border-red-200 bg-red-50/50 opacity-60" : 
                            lead.status === 'called' ? "border-green-200 bg-green-50/50" :
                            "border-border hover:border-primary/50"
                        )}
                    >
                        <div className="flex justify-between items-start mb-3">
                            <span className="text-xs font-bold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 uppercase tracking-wider">{lead.source}</span>
                            <div className="flex gap-2">
                                {lead.notes && (
                                    <div className="group/tooltip relative">
                                        <Info className="w-5 h-5 text-blue-500" />
                                        <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-black text-white text-xs rounded shadow-lg hidden group-hover/tooltip:block z-10">
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
                            Clic para ver detalles y gestionar
                        </div>
                    </div>
                ))}
            </div>
        </div>
      )}

      {/* ... existing Results / Artifacts ... */}
    </div>
  );
}
