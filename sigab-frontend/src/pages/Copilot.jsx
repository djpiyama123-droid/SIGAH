import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api/sigab';
import toast from 'react-hot-toast';

// ── Iconos inline ─────────────────────────────────────────────────
const IconIA = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);
const IconSend = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
  </svg>
);
const IconStop = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
    <rect x="6" y="6" width="12" height="12" rx="1" />
  </svg>
);
const IconImage = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);
const IconClear = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

// ── Componente de mensaje ─────────────────────────────────────────
function ChatMessage({ msg }) {
  const isUser = msg.role === 'user';
  const isError = msg.error;

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-emerald-700/50 border border-emerald-600/40 rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm text-white">
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 mb-4">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mt-0.5">
        <IconIA />
      </div>
      <div className={`max-w-[80%] rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm ${
        isError
          ? 'bg-red-900/30 border border-red-500/40 text-red-300'
          : 'bg-slate-700/70 border border-slate-600/40 text-slate-200'
      }`}>
        {isError ? (
          <p className="text-xs">{msg.content}</p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none">
            {msg.content.split('\n').map((line, i) => {
              if (line.startsWith('**') && line.endsWith('**')) {
                return <p key={i} className="font-bold text-emerald-400 mt-2 mb-1">{line.replace(/\*\*/g, '')}</p>;
              }
              if (line.startsWith('- ') || line.startsWith('• ')) {
                return <p key={i} className="pl-3 text-slate-300">• {line.slice(2)}</p>;
              }
              if (/^\d+\. /.test(line)) {
                return <p key={i} className="pl-3 text-slate-300">{line}</p>;
              }
              if (line.trim() === '') return <br key={i} />;
              return <p key={i} className="text-slate-200">{line}</p>;
            })}
          </div>
        )}
        {msg.streaming && (
          <span className="inline-block w-1.5 h-4 bg-emerald-400 ml-0.5 animate-pulse" />
        )}
      </div>
    </div>
  );
}

// ── Componente análisis diagnóstico ──────────────────────────────
function DiagnosticoPanel({ onClose }) {
  const [equipos, setEquipos] = useState([]);
  const [equipoId, setEquipoId] = useState('');
  const [falla, setFalla] = useState('');
  const [marca, setMarca] = useState('');
  const [modelo, setModelo] = useState('');
  const [resultado, setResultado] = useState('');
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    api.getEquipos({ limit: 300 }).then(r => setEquipos(r.equipos || [])).catch(() => {});
  }, []);

  const handleEquipoChange = (e) => {
    const id = parseInt(e.target.value);
    setEquipoId(id);
    const eq = equipos.find(eq => eq.id === id);
    if (eq) {
      setMarca(eq.marca || '');
      setModelo(eq.modelo || '');
    }
  };

  const analizar = async () => {
    if (!falla.trim()) { toast.error('Describe la falla'); return; }
    setCargando(true);
    setResultado('');
    try {
      const res = await api.copilotDiagnostico({
        falla,
        equipo_id: equipoId || undefined,
        marca,
        modelo,
      });
      setResultado(res.diagnostico || 'Sin respuesta');
    } catch (err) {
      setResultado('Error: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-semibold text-yellow-400">Diagnóstico de Falla con IA</h3>
        <button onClick={onClose} className="text-slate-500 hover:text-white text-xs">✕ Cerrar</button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div className="col-span-2">
          <label className="text-xs text-slate-400 block mb-1">Equipo (opcional)</label>
          <select value={equipoId} onChange={handleEquipoChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white">
            <option value="">— Sin seleccionar —</option>
            {equipos.map(eq => (
              <option key={eq.id} value={eq.id}>{eq.nombre} — {eq.serie}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Marca</label>
          <input value={marca} onChange={e => setMarca(e.target.value)} placeholder="GE, Philips..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Modelo</label>
          <input value={modelo} onChange={e => setModelo(e.target.value)} placeholder="CARESCAPE B650..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white" />
        </div>
        <div className="col-span-2">
          <label className="text-xs text-slate-400 block mb-1">Falla reportada *</label>
          <textarea rows={2} value={falla} onChange={e => setFalla(e.target.value)}
            placeholder="Ej: El monitor no enciende, hace click al intentar prender..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" />
        </div>
      </div>
      <button onClick={analizar} disabled={cargando || !falla.trim()}
        className="w-full py-2 bg-yellow-600 hover:bg-yellow-500 text-white text-sm font-semibold rounded-lg disabled:opacity-40 transition-colors">
        {cargando ? 'Analizando con Gemma...' : 'Analizar falla'}
      </button>

      {resultado && (
        <div className="bg-slate-900/60 border border-yellow-500/20 rounded-lg p-3 text-xs text-slate-300 space-y-1 max-h-60 overflow-y-auto">
          {resultado.split('\n').map((line, i) => {
            if (line.startsWith('**') && line.endsWith('**'))
              return <p key={i} className="font-bold text-yellow-400 mt-2">{line.replace(/\*\*/g, '')}</p>;
            if (line.trim() === '') return <br key={i} />;
            return <p key={i}>{line}</p>;
          })}
        </div>
      )}
    </div>
  );
}

// ── Componente análisis de imagen (Vision) ────────────────────────
function VisionPanel({ onClose }) {
  const [imagen, setImagen] = useState(null);
  const [tipDoc, setTipDoc] = useState('etiqueta_equipo');
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const b64 = ev.target.result.split(',')[1];
      setImagen({ b64, preview: ev.target.result, name: file.name });
    };
    reader.readAsDataURL(file);
  };

  const analizar = async () => {
    if (!imagen) { toast.error('Selecciona una imagen'); return; }
    setCargando(true);
    setResultado(null);
    try {
      const res = await api.copilotVision({ imagen_b64: imagen.b64, tipo_doc: tipDoc });
      setResultado(res);
    } catch (err) {
      toast.error('Error en análisis de imagen');
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-semibold text-blue-400">Análisis de Imagen (Gemma Vision)</h3>
        <button onClick={onClose} className="text-slate-500 hover:text-white text-xs">✕ Cerrar</button>
      </div>

      <div>
        <label className="text-xs text-slate-400 block mb-1">Tipo de documento</label>
        <select value={tipDoc} onChange={e => setTipDoc(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white">
          <option value="etiqueta_equipo">Etiqueta / placa del equipo</option>
          <option value="reporte_servicio">Reporte de servicio externo</option>
          <option value="general">Análisis general</option>
        </select>
      </div>

      <div className="border-2 border-dashed border-slate-600 rounded-lg p-4 text-center">
        {imagen ? (
          <div className="space-y-2">
            <img src={imagen.preview} alt="preview" className="max-h-32 mx-auto rounded object-contain" />
            <p className="text-xs text-slate-400">{imagen.name}</p>
            <button onClick={() => setImagen(null)} className="text-xs text-red-400 hover:text-red-300">Cambiar</button>
          </div>
        ) : (
          <label className="cursor-pointer space-y-2">
            <IconImage />
            <p className="text-xs text-slate-400 mt-2">Click para seleccionar imagen</p>
            <p className="text-[10px] text-slate-600">PNG, JPG, WEBP — máx 10MB</p>
            <input type="file" accept="image/*" onChange={handleFile} className="hidden" />
          </label>
        )}
      </div>

      <button onClick={analizar} disabled={!imagen || cargando}
        className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg disabled:opacity-40 transition-colors">
        {cargando ? 'Analizando imagen...' : 'Analizar con Gemma Vision'}
      </button>

      {resultado && (
        <div className="bg-slate-900/60 border border-blue-500/20 rounded-lg p-3 text-xs text-slate-300 space-y-2 max-h-60 overflow-y-auto">
          {resultado.datos_extraidos && (
            <div className="mb-2">
              <p className="text-blue-400 font-semibold mb-1">Datos extraídos:</p>
              {Object.entries(resultado.datos_extraidos).map(([k, v]) =>
                v ? <p key={k}><span className="text-slate-500">{k}:</span> {v}</p> : null
              )}
            </div>
          )}
          <p className="text-slate-400 text-[10px] font-semibold">Análisis completo:</p>
          <p className="whitespace-pre-wrap">{resultado.analisis}</p>
        </div>
      )}
    </div>
  );
}

// ── Página principal Copilot ──────────────────────────────────────
export default function Copilot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const [edgeStatus, setEdgeStatus] = useState(null);
  const [promptsRapidos, setPromptsRapidos] = useState([]);
  const [resumenIA, setResumenIA] = useState(null);
  const [cargandoResumen, setCargandoResumen] = useState(false);
  const [showDiagnostico, setShowDiagnostico] = useState(false);
  const [showVision, setShowVision] = useState(false);
  const [contextoTipo, setContextoTipo] = useState('general');

  const messagesEndRef = useRef(null);
  const abortRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll al último mensaje
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  // Verificar estado de proveedores IA al cargar
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Estado detallado (edge + cloud) — nuevo endpoint
        const edge = await api.getCopilotEstadoEdge();
        setEdgeStatus(edge);
        // Mantener compatibilidad con lógica legacy usando los mismos datos
        setOllamaStatus({
          ok: edge.edge?.status === 'online',
          ollama_activo: edge.edge?.status === 'online',
          modelo: edge.edge?.modelo,
          modelo_disponible: edge.edge?.modelo_ok ?? false,
          modelos_instalados: edge.edge?.modelos ?? [],
        });
      } catch {
        // Fallback al endpoint legacy si el nuevo no está disponible
        try {
          const status = await api.getCopilotEstado();
          setOllamaStatus(status);
        } catch {
          setOllamaStatus({ ok: false, ollama_activo: false });
        }
      }
    };
    checkStatus();

    // Cargar prompts rápidos
    api.getCopilotPromptsRapidos()
      .then(res => setPromptsRapidos(res.prompts || []))
      .catch(() => {});
  }, []);

  // Mensaje de bienvenida
  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: `¡Hola! Soy **SIGAB Copilot**, tu asistente de IA biomédica local.

Estoy potenciado por **Gemma** ejecutándose directamente en el servidor del HGR No.1 — sin dependencias de nube, 100% on-premise.

Puedo ayudarte con:
- Diagnóstico de fallas en equipos médicos
- Análisis e interpretación de MTBF/MTTR
- Orientación sobre NOM-016, NOM-240 e ISO 13485
- Análisis de eventos adversos (Tecnovigilancia)
- Resúmenes ejecutivos del departamento

¿En qué puedo ayudarte hoy?`,
      streaming: false,
    }]);
  }, []);

  // Enviar mensaje con streaming SSE
  const enviarMensaje = async (textoOverride = null) => {
    const texto = (textoOverride || input).trim();
    if (!texto || streaming) return;

    setInput('');
    const historial = messages.filter(m => !m.error);
    const newMessages = [...historial, { role: 'user', content: texto }];
    setMessages(newMessages);
    setStreaming(true);

    // Placeholder para la respuesta en streaming
    const placeholderMsg = { role: 'assistant', content: '', streaming: true };
    setMessages(prev => [...prev, placeholderMsg]);

    const token = localStorage.getItem('token');
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch('/api/copilot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          contexto_tipo: contextoTipo,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let acumulado = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const data = JSON.parse(raw);
            if (data.error) {
              acumulado += `\n\n⚠️ ${data.error}`;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: 'assistant',
                  content: acumulado,
                  streaming: false,
                  error: true,
                };
                return updated;
              });
              break;
            }
            if (data.token) {
              acumulado += data.token;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: 'assistant',
                  content: acumulado,
                  streaming: !data.done,
                };
                return updated;
              });
            }
            if (data.done) break;
          } catch (e) {
            // JSON parse error, skip
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.streaming) {
            updated[updated.length - 1] = { ...last, streaming: false, content: last.content + '\n\n_[Generación detenida]_' };
          }
          return updated;
        });
      } else {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'assistant',
            content: `Error de conexión: ${err.message}. ¿Está Ollama corriendo en el servidor?`,
            streaming: false,
            error: true,
          };
          return updated;
        });
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
      inputRef.current?.focus();
    }
  };

  const detenerStream = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  const limpiarChat = () => {
    setMessages([{
      role: 'assistant',
      content: 'Chat reiniciado. ¿En qué puedo ayudarte?',
      streaming: false,
    }]);
  };

  const usarPromptRapido = (prompt) => {
    if (prompt.contexto_tipo) setContextoTipo(prompt.contexto_tipo);
    enviarMensaje(prompt.texto);
  };

  const generarResumenIA = async () => {
    setCargandoResumen(true);
    setResumenIA(null);
    try {
      const res = await api.copilotResumenIa();
      setResumenIA(res);
    } catch (err) {
      toast.error('Error al generar resumen: ¿Ollama está activo?');
    } finally {
      setCargandoResumen(false);
    }
  };

  const StatusBadge = () => {
    if (!ollamaStatus && !edgeStatus) {
      return <span className="text-xs text-slate-500">Verificando...</span>;
    }

    const modo = edgeStatus?.modo_activo;

    if (modo === 'edge') {
      return (
        <span className="flex items-center gap-1.5 text-xs text-emerald-400">
          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          Edge local · {edgeStatus.edge?.modelo}
        </span>
      );
    }
    if (modo === 'cloud') {
      return (
        <span className="flex items-center gap-1.5 text-xs text-sky-400">
          <span className="w-1.5 h-1.5 bg-sky-400 rounded-full animate-pulse" />
          Nube (MiniMax) · fallback activo
        </span>
      );
    }
    if (modo === 'edge_sin_modelo') {
      return (
        <span className="flex items-center gap-1.5 text-xs text-orange-400">
          <span className="w-1.5 h-1.5 bg-orange-500 rounded-full animate-pulse" />
          Edge activo · modelo no descargado
        </span>
      );
    }
    // sin_ia o estado legacy
    if (!ollamaStatus?.ollama_activo) {
      return (
        <span className="flex items-center gap-1.5 text-xs text-red-400">
          <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
          Sin IA disponible
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 text-xs text-emerald-400">
        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
        {ollamaStatus.modelo} · activo
      </span>
    );
  };

  return (
    <div className="h-full flex flex-col" style={{ minHeight: '0' }}>
      {/* Header */}
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-2xl">✦</span>
            SIGAB Copilot
          </h1>
          <p className="text-sm text-slate-400 mt-0.5 flex items-center gap-2">
            Asistente biomédico · IA local on-premise
            <StatusBadge />
          </p>
        </div>
        <div className="flex gap-2">
          {/* Contexto */}
          <select value={contextoTipo} onChange={e => setContextoTipo(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-300 rounded-lg px-2 py-1.5">
            <option value="general">Contexto: General</option>
            <option value="fiabilidad">Contexto: MTBF/Fiabilidad</option>
            <option value="equipo">Contexto: Equipo activo</option>
          </select>
          <button onClick={limpiarChat} title="Limpiar chat"
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-lg transition-colors">
            <IconClear />
          </button>
        </div>
      </div>

      {/* Warning si edge offline pero nube activa */}
      {edgeStatus?.modo_activo === 'cloud' && (
        <div className="mb-4 bg-sky-900/20 border border-sky-500/40 rounded-xl p-4 text-sm flex-shrink-0">
          <p className="text-sky-300 font-semibold">Modo fallback: usando MiniMax (nube)</p>
          <p className="text-sky-400/80 text-xs mt-1">
            El nodo edge (Ollama en Lenovo ThinkCentre) no está disponible. Las respuestas se generan via API MiniMax.
            Para restaurar la IA local, inicia Ollama en el servidor:
          </p>
          <code className="block mt-2 bg-black/30 rounded p-2 text-xs text-sky-200 font-mono">
            ollama serve &amp;&amp; ollama pull gemma3:4b
          </code>
        </div>
      )}

      {/* Warning si sin IA disponible */}
      {(edgeStatus?.modo_activo === 'sin_ia' || (!edgeStatus && ollamaStatus && !ollamaStatus.ollama_activo)) && (
        <div className="mb-4 bg-orange-900/20 border border-orange-500/40 rounded-xl p-4 text-sm flex-shrink-0">
          <p className="text-orange-300 font-semibold">Sin IA disponible</p>
          <p className="text-orange-400/80 text-xs mt-1">
            Ollama (edge) offline y fallback MiniMax no configurado. Inicia Ollama:
          </p>
          <code className="block mt-2 bg-black/30 rounded p-2 text-xs text-orange-200 font-mono">
            ollama serve &amp;&amp; ollama pull gemma3:4b
          </code>
        </div>
      )}

      {/* Warning modelo no descargado en edge */}
      {(edgeStatus?.modo_activo === 'edge_sin_modelo' || (ollamaStatus?.ollama_activo && !ollamaStatus?.modelo_disponible)) && (
        <div className="mb-4 bg-yellow-900/20 border border-yellow-500/40 rounded-xl p-4 text-sm flex-shrink-0">
          <p className="text-yellow-300 font-semibold">Modelo {ollamaStatus?.modelo ?? edgeStatus?.edge?.modelo} no descargado</p>
          <code className="block mt-1 bg-black/30 rounded p-2 text-xs text-yellow-200 font-mono">
            ollama pull {ollamaStatus?.modelo ?? edgeStatus?.edge?.modelo}
          </code>
          {ollamaStatus?.modelos_instalados?.length > 0 && (
            <p className="text-xs text-yellow-400/60 mt-1">
              Modelos disponibles: {ollamaStatus.modelos_instalados.join(', ')}
            </p>
          )}
        </div>
      )}

      <div className="flex gap-4 flex-1 min-h-0">
        {/* ── Chat principal ── */}
        <div className="flex flex-col flex-1 min-h-0 bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
          {/* Mensajes */}
          <div className="flex-1 overflow-y-auto p-4 space-y-1">
            {messages.map((msg, i) => (
              <ChatMessage key={i} msg={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Prompts rápidos — solo si chat vacío (1 mensaje) */}
          {messages.length === 1 && promptsRapidos.length > 0 && (
            <div className="px-4 pb-2 flex flex-wrap gap-2">
              {promptsRapidos.map(p => (
                <button key={p.id} onClick={() => usarPromptRapido(p)}
                  className="text-xs px-3 py-1.5 bg-slate-700 hover:bg-slate-600 border border-slate-600 text-slate-300 rounded-full transition-colors">
                  {p.label}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="border-t border-slate-700 p-3">
            <div className="flex gap-2 items-end">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    enviarMensaje();
                  }
                }}
                placeholder="Pregunta sobre equipos, mantenimiento, NOM-240, diagnósticos... (Enter para enviar)"
                rows={2}
                disabled={streaming}
                className="flex-1 bg-slate-900/60 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-emerald-600 resize-none disabled:opacity-50"
              />
              {streaming ? (
                <button onClick={detenerStream}
                  className="p-3 bg-red-600 hover:bg-red-500 text-white rounded-xl transition-colors flex-shrink-0">
                  <IconStop />
                </button>
              ) : (
                <button onClick={() => enviarMensaje()} disabled={!input.trim()}
                  className="p-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition-colors disabled:opacity-40 flex-shrink-0">
                  <IconSend />
                </button>
              )}
            </div>
            <p className="text-[10px] text-slate-600 mt-1 text-center">
              Shift+Enter para nueva línea · Enter para enviar · IA local — sin datos a la nube
            </p>
          </div>
        </div>

        {/* ── Panel lateral ── */}
        <div className="w-72 flex-shrink-0 space-y-3 overflow-y-auto">
          {/* Diagnóstico rápido */}
          {showDiagnostico ? (
            <DiagnosticoPanel onClose={() => setShowDiagnostico(false)} />
          ) : (
            <button onClick={() => { setShowDiagnostico(true); setShowVision(false); }}
              className="w-full text-left p-4 bg-slate-800 border border-slate-700 hover:border-yellow-500/50 rounded-xl transition-colors group">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-yellow-400">⚡</span>
                <span className="text-sm font-semibold text-white">Diagnóstico de Falla</span>
              </div>
              <p className="text-xs text-slate-400">
                Describe la falla de un equipo y Gemma sugiere causas, verificaciones y acciones.
              </p>
            </button>
          )}

          {/* Análisis de imagen (Gemma Vision) */}
          {showVision ? (
            <VisionPanel onClose={() => setShowVision(false)} />
          ) : (
            <button onClick={() => { setShowVision(true); setShowDiagnostico(false); }}
              className="w-full text-left p-4 bg-slate-800 border border-slate-700 hover:border-blue-500/50 rounded-xl transition-colors group">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-blue-400"><IconImage /></span>
                <span className="text-sm font-semibold text-white">Vision (Gemma 4)</span>
              </div>
              <p className="text-xs text-slate-400">
                Sube foto de etiqueta o reporte de servicio. Gemma extrae datos automáticamente.
              </p>
            </button>
          )}

          {/* Resumen IA diario */}
          <div className="p-4 bg-slate-800 border border-slate-700 rounded-xl space-y-2">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-emerald-400">📊</span>
              <span className="text-sm font-semibold text-white">Resumen Ejecutivo IA</span>
            </div>
            <p className="text-xs text-slate-400">
              Gemma analiza el estado actual del SIGAB y genera un resumen narrativo para el jefe.
            </p>
            <button onClick={generarResumenIA} disabled={cargandoResumen}
              className="w-full py-1.5 bg-emerald-700/50 hover:bg-emerald-700 border border-emerald-600/40 text-emerald-300 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50">
              {cargandoResumen ? 'Generando...' : 'Generar resumen del día'}
            </button>
            {resumenIA && (
              <div className="mt-2 bg-slate-900/60 rounded-lg p-3 text-xs text-slate-300 max-h-48 overflow-y-auto">
                <p className="text-emerald-400 font-semibold mb-1 text-[10px]">
                  {resumenIA.fecha} · {resumenIA.modelo}
                </p>
                <p className="whitespace-pre-wrap">{resumenIA.resumen_narrativo}</p>
              </div>
            )}
          </div>

          {/* Info de proveedores IA */}
          {edgeStatus ? (
            <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl space-y-3">
              <p className="text-xs font-semibold text-slate-400">Proveedores IA</p>

              {/* Edge */}
              <div>
                <div className="flex items-center gap-1.5 mb-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    edgeStatus.edge?.status === 'online' ? 'bg-emerald-400' : 'bg-slate-600'
                  }`} />
                  <p className="text-[10px] font-semibold text-slate-300">Nodo Edge (Lenovo)</p>
                  {edgeStatus.modo_activo === 'edge' && (
                    <span className="text-[9px] bg-emerald-700/50 text-emerald-300 px-1 rounded">ACTIVO</span>
                  )}
                </div>
                <div className="space-y-0.5 text-[10px] text-slate-500 pl-3">
                  <p>Modelo: <span className="text-slate-300 font-mono">{edgeStatus.edge?.modelo}</span></p>
                  <p>Estado: <span className={edgeStatus.edge?.status === 'online' ? 'text-emerald-400' : 'text-red-400'}>{edgeStatus.edge?.status}</span></p>
                  {edgeStatus.edge?.latencia_ms != null && (
                    <p>Latencia: <span className="text-slate-300">{edgeStatus.edge.latencia_ms} ms</span></p>
                  )}
                </div>
              </div>

              {/* Cloud fallback */}
              <div>
                <div className="flex items-center gap-1.5 mb-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    edgeStatus.cloud?.status === 'online' ? 'bg-sky-400' :
                    edgeStatus.cloud?.status === 'no_key' ? 'bg-slate-600' : 'bg-amber-500'
                  }`} />
                  <p className="text-[10px] font-semibold text-slate-300">Nube Fallback (MiniMax)</p>
                  {edgeStatus.modo_activo === 'cloud' && (
                    <span className="text-[9px] bg-sky-700/50 text-sky-300 px-1 rounded">ACTIVO</span>
                  )}
                </div>
                <div className="space-y-0.5 text-[10px] text-slate-500 pl-3">
                  <p>Modelo: <span className="text-slate-300 font-mono">{edgeStatus.cloud?.modelo}</span></p>
                  <p>Estado: <span className={
                    edgeStatus.cloud?.status === 'online' ? 'text-sky-400' :
                    edgeStatus.cloud?.status === 'no_key' ? 'text-slate-500' : 'text-amber-400'
                  }>{edgeStatus.cloud?.status === 'no_key' ? 'sin clave API' : edgeStatus.cloud?.status}</span></p>
                </div>
              </div>

              {edgeStatus.edge?.modelos?.length > 0 && (
                <div>
                  <p className="text-[10px] text-slate-500 mb-1">Modelos en edge:</p>
                  {edgeStatus.edge.modelos.map(m => (
                    <span key={m} className="inline-block mr-1 mb-1 px-1.5 py-0.5 bg-slate-700 text-slate-400 text-[9px] rounded font-mono">
                      {m}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : ollamaStatus?.ollama_activo && (
            <div className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
              <p className="text-xs font-semibold text-slate-400 mb-2">Configuración del modelo</p>
              <div className="space-y-1 text-[10px] text-slate-500">
                <p>Modelo: <span className="text-slate-300 font-mono">{ollamaStatus.modelo}</span></p>
                <p>Host: <span className="text-slate-300 font-mono">localhost:11434</span></p>
                <p>Modo: <span className="text-emerald-400">100% on-premise</span></p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
