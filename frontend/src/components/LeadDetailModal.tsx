import React, { useState } from 'react';
import { Button } from './ui/button';
import { X, Save, Phone, CheckCircle, XCircle, Eye } from 'lucide-react';

interface LeadDetailModalProps {
  lead: any;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (leadId: number, updates: any) => Promise<void>;
}

export default function LeadDetailModal({ lead, isOpen, onClose, onUpdate }: LeadDetailModalProps) {
  const [notes, setNotes] = useState(lead?.notes || '');
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen || !lead) return null;

  const handleStatusChange = async (newStatus: string) => {
    setIsSaving(true);
    await onUpdate(lead.id, { status: newStatus });
    setIsSaving(false);
    onClose();
  };

  const handleSaveNotes = async () => {
    setIsSaving(true);
    await onUpdate(lead.id, { notes });
    setIsSaving(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-background rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-border">
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-border bg-muted/20">
          <div>
            <h2 className="text-xl font-bold text-foreground mb-1">{lead.parsed_data?.title || 'Detalle del Piso'}</h2>
            <div className="flex gap-2">
                <span className="text-xs px-2 py-1 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono uppercase">{lead.source}</span>
                <span className={`text-xs px-2 py-1 rounded font-medium uppercase ${
                    lead.status === 'new' ? 'bg-blue-100 text-blue-700' :
                    lead.status === 'seen' ? 'bg-yellow-100 text-yellow-700' :
                    lead.status === 'called' ? 'bg-green-100 text-green-700' :
                    'bg-red-100 text-red-700'
                }`}>
                    {lead.status === 'new' ? 'Nuevo' :
                     lead.status === 'seen' ? 'Visto' :
                     lead.status === 'called' ? 'Llamado' : 'Descartado'}
                </span>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-muted rounded-full transition-colors">
            <X className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Key Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-muted/30 rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">Precio</div>
              <div className="text-2xl font-bold text-primary">{lead.parsed_data?.price || 'N/A'}</div>
            </div>
            <div className="p-4 bg-muted/30 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">Confianza IA</div>
                <div className="text-2xl font-bold text-green-600">{Math.round(lead.confidence * 100)}%</div>
            </div>
          </div>

          {/* Contact */}
          <div className="space-y-2">
            <h3 className="font-semibold flex items-center gap-2">
                <Phone className="w-4 h-4" /> Contacto
            </h3>
            <div className="p-4 border border-border rounded-lg bg-card">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <div className="text-xs uppercase text-muted-foreground font-semibold">Nombre</div>
                        <div className="text-lg">{lead.contact_name || 'No detectado'}</div>
                    </div>
                    <div>
                        <div className="text-xs uppercase text-muted-foreground font-semibold">Teléfono</div>
                        <div className="text-lg font-mono">{lead.contact_phone || 'No detectado'}</div>
                    </div>
                </div>
            </div>
          </div>

          {/* Description */}
          {lead.parsed_data?.description && (
            <div className="space-y-2">
                <h3 className="font-semibold">Descripción Original</h3>
                <p className="text-sm text-muted-foreground leading-relaxed bg-muted/30 p-3 rounded-lg max-h-40 overflow-y-auto">
                    {lead.parsed_data.description}
                </p>
            </div>
          )}

          {/* Notes */}
          <div className="space-y-2">
            <h3 className="font-semibold">Mis Notas</h3>
            <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Escribe aquí tus anotaciones sobre este piso (ej: 'Llamar por la tarde', 'Muy caro')..."
                className="w-full h-24 p-3 rounded-md border border-input bg-background text-sm focus:ring-2 focus:ring-primary focus:outline-none resize-none"
            />
            <div className="flex justify-end">
                <Button size="sm" onClick={handleSaveNotes} disabled={isSaving}>
                    <Save className="w-4 h-4 mr-2" /> Guardar Notas
                </Button>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-border bg-muted/20 flex flex-wrap gap-3 justify-end">
            <Button variant="outline" onClick={() => handleStatusChange('rejected')} className="text-red-600 hover:text-red-700 hover:bg-red-50">
                <XCircle className="w-4 h-4 mr-2" /> Descartar
            </Button>
            <Button variant="outline" onClick={() => handleStatusChange('seen')} className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50">
                <Eye className="w-4 h-4 mr-2" /> Marcar Visto
            </Button>
            <Button onClick={() => handleStatusChange('called')} className="bg-green-600 hover:bg-green-700 text-white">
                <Phone className="w-4 h-4 mr-2" /> Marcar Llamado
            </Button>
            
            <a 
                href={lead.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="ml-auto inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
            >
                Ver en Web
            </a>
        </div>
      </div>
    </div>
  );
}
