import { Bot, ChevronDown, ChevronLeft, ExternalLink, FileText, MessageSquare, Plus, Send, Sparkles, ThumbsDown, ThumbsUp, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { CopilotReportBlock } from '../components/CopilotReportBlock.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as assistantService from '../services/assistantService.js';

const LS_KEY = 'warelyn_copilot_active_session_id';

function samplePrompts() {
  return [
    'Show warehouse stock report',
    'Which items are low on stock?',
    'Show open workflow tasks by role',
    'What needs my attention today?',
    'Show stock movements this week',
    'Which products need reordering?',
    'Show me the reconciliation report',
    'Biggest workflow bottleneck?',
  ];
}

export function AdminAICopilotPage() {
  const { accessToken } = useAuth();
  const toast = useToast();
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [telemetry, setTelemetry] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  async function loadSessions() {
    try {
      const list = await assistantService.listAssistantSessions(accessToken);
      setSessions(list);
    } catch {
    }
  }

  async function loadSession(sessionId) {
    setLoading(true);
    setError('');
    try {
      const detail = await assistantService.getAssistantSession(accessToken, sessionId);
      setSession(detail.session);
      setMessages(detail.messages);
      localStorage.setItem(LS_KEY, String(sessionId));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function boot() {
    setLoading(true);
    setError('');
    try {
      const list = await assistantService.listAssistantSessions(accessToken);
      setSessions(list);

      const savedId = localStorage.getItem(LS_KEY);
      const savedSession = savedId ? list.find((s) => String(s.id) === savedId) : null;

      if (savedSession) {
        const detail = await assistantService.getAssistantSession(accessToken, savedSession.id);
        setSession(detail.session);
        setMessages(detail.messages);
      } else {
        const created = await assistantService.createAssistantSession(accessToken, `Session ${new Date().toLocaleString()}`);
        setSessions((prev) => [created, ...prev]);
        const detail = await assistantService.getAssistantSession(accessToken, created.id);
        setSession(detail.session);
        setMessages(detail.messages);
        localStorage.setItem(LS_KEY, String(created.id));
      }

      const telemetryRow = await assistantService.getAssistantTelemetry(accessToken);
      setTelemetry(telemetryRow);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    boot();
  }, [accessToken]);

  async function sendQuestion(nextQuestion) {
    if (!session) return;
    const value = (nextQuestion ?? question).trim();
    if (!value) return;
    const userMessage = { id: `user-${Date.now()}`, role: 'USER', content: value };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);
    setError('');
    try {
      const isFirstMessage = messages.length === 0;
      const result = await assistantService.askAssistant(accessToken, session.id, value);
      const messageWithReport = {
        ...result.message,
        _report_data: result.report_data || null,
        _is_off_topic: result.is_off_topic || false,
      };
      setMessages((prev) => [...prev, messageWithReport]);
      setQuestion('');
      if (isFirstMessage) {
        const title = value.length > 80 ? value.slice(0, 80).trimEnd() : value;
        setSession((prev) => prev ? { ...prev, title } : prev);
        setSessions((prev) => prev.map((s) => s.id === session.id ? { ...s, title } : s));
      }
      const telemetryRow = await assistantService.getAssistantTelemetry(accessToken);
      setTelemetry(telemetryRow);
    } catch (e) {
      toast.error(e.message || 'Failed to get assistant response.');
      setError(e.message);
    } finally {
      setSending(false);
    }
  }

  async function feedback(messageId, value) {
    try {
      await assistantService.submitAssistantFeedback(accessToken, messageId, value);
      toast.success('Feedback captured.');
    } catch (e) {
      toast.error(e.message || 'Failed to submit feedback.');
    }
  }

  async function handleNewSession() {
    try {
      const created = await assistantService.createAssistantSession(accessToken, `Session ${new Date().toLocaleString()}`);
      setSessions((prev) => [created, ...prev]);
      localStorage.setItem(LS_KEY, String(created.id));
      await loadSession(created.id);
      setSidebarOpen(false);
    } catch (e) {
      toast.error(e.message || 'Failed to create session.');
    }
  }

  async function handleSelectSession(sessionId) {
    if (session?.id === sessionId) return;
    await loadSession(sessionId);
    if (window.innerWidth < 768) setSidebarOpen(false);
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    try {
      await assistantService.deleteAssistantSession(accessToken, deleteTarget);
      setSessions((prev) => prev.filter((s) => s.id !== deleteTarget));
      if (session?.id === deleteTarget) {
        const remaining = sessions.filter((s) => s.id !== deleteTarget);
        if (remaining.length > 0) {
          await handleSelectSession(remaining[0].id);
        } else {
          await handleNewSession();
        }
      }
    } catch (e) {
      toast.error(e.message || 'Failed to delete session.');
    } finally {
      setDeleteTarget(null);
    }
  }

  if (loading) return (
    <div className="space-y-4">
      <div className="h-8 w-48 bg-warelyn-border rounded animate-pulse" />
      <div className="border border-warelyn-border rounded-xl overflow-hidden" style={{ height: 'calc(100vh - 180px)' }}>
        <div className="p-4 space-y-4">
          {[80, 65, 90, 55].map((w, i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start gap-2.5'}`}>
              {i % 2 !== 0 && <div className="w-7 h-7 rounded-full bg-warelyn-border animate-pulse flex-shrink-0" />}
              <div className="h-10 bg-warelyn-border rounded-2xl animate-pulse" style={{ width: `${w}%` }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-100px)] gap-0">
      <aside className={`flex flex-col border-r border-warelyn-border bg-white transition-all duration-200 overflow-hidden flex-shrink-0 ${sidebarOpen ? 'w-64' : 'w-0 border-r-0'}`}>
        <div className="flex items-center justify-between p-3 border-b border-warelyn-border">
          <span className="text-xs font-semibold text-warelyn-muted uppercase tracking-wider">History</span>
          <button
            type="button"
            onClick={handleNewSession}
            className="w-6 h-6 rounded-md hover:bg-gray-100 flex items-center justify-center text-warelyn-muted hover:text-warelyn-text transition-colors"
            title="New session"
          >
            <Plus size={14} />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {sessions.map((s) => (
            <div key={s.id} className={`group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer text-sm transition-colors ${session?.id === s.id ? 'bg-blue-50 text-warelyn-primary font-medium' : 'text-warelyn-text hover:bg-gray-50'}`} onClick={() => handleSelectSession(s.id)}>
              <MessageSquare size={14} className="flex-shrink-0 opacity-60" />
              <span className="truncate flex-1">{s.title}</span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(s.id); }}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-50 text-warelyn-muted hover:text-red-500 transition-all flex-shrink-0"
                title="Delete session"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-warelyn-muted text-center py-8">No sessions yet.</p>
          )}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between px-4 pt-3 pb-0">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarOpen((prev) => !prev)}
              className="w-7 h-7 rounded-md hover:bg-gray-100 flex items-center justify-center text-warelyn-muted hover:text-warelyn-text transition-colors"
              title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
              <ChevronLeft size={15} className={`transition-transform ${sidebarOpen ? '' : 'rotate-180'}`} />
            </button>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-warelyn-muted page-kicker">Tenant Admin</p>
              <h1 className="text-xl font-bold text-warelyn-text">AI Copilot</h1>
              <p className="text-sm text-warelyn-muted">Read-only operational copilot with grounded answers and citations.</p>
            </div>
          </div>
          {telemetry && (
            <details className="text-xs text-warelyn-muted flex-shrink-0">
              <summary className="cursor-pointer hover:text-warelyn-text list-none flex items-center gap-1">
                <ChevronDown size={12} /> Health
              </summary>
              <div className="flex gap-4 mt-1 pl-4">
                <span>Requests: {telemetry.total_requests}</span>
                <span>Avg latency: {telemetry.avg_latency_ms}ms</span>
                <span>Abstain rate: {telemetry.abstain_rate_pct}%</span>
                <span>Citation rate: {telemetry.citation_rate_pct}%</span>
              </div>
            </details>
          )}
        </div>

        {error ? <div className="mx-4 mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

        <div className="flex-1 flex flex-col mx-3 my-3 border border-warelyn-border rounded-xl bg-white overflow-hidden" style={{ minHeight: '400px' }}>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !sending ? (
              <div className="flex flex-col items-center justify-center h-full gap-3 py-12 text-center">
                <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
                  <Bot size={22} className="text-warelyn-primary" />
                </div>
                <p className="text-sm text-warelyn-muted max-w-xs">Ask about your operations, reports, stock levels, or workflows.</p>
                <p className="text-xs text-warelyn-muted/70">Only Warelyn Inventory questions answered.</p>
                <div className="flex flex-wrap justify-center gap-2 mt-2 max-w-md">
                  {samplePrompts().map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => sendQuestion(prompt)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border border-warelyn-border bg-white text-warelyn-primary hover:bg-blue-50 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  message.role === 'ASSISTANT' || message.role === 'assistant' ? (
                    <div key={message.id} className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Bot size={14} className="text-emerald-600" />
                      </div>
                      <div className="max-w-[88%] rounded-2xl rounded-tl-sm bg-gray-50 border border-warelyn-border px-4 py-3 space-y-2">
                        <p className="text-sm text-warelyn-text leading-relaxed whitespace-pre-wrap">{message.content}</p>
                        {message._report_data && <CopilotReportBlock data={message._report_data} />}
                        {message.citations_json?.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1">
                            {message.citations_json.slice(0, 4).map((c, i) => (
                              <span key={i} className="inline-flex items-center gap-1 text-[10px] bg-white border border-warelyn-border rounded-full px-2 py-0.5 text-warelyn-muted">
                                <FileText size={9} />
                                {c.title}
                              </span>
                            ))}
                          </div>
                        )}
                        {message.suggested_actions_json?.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-0.5">
                            {message.suggested_actions_json.map((action, i) => (
                              <Link
                                key={i}
                                to={action.to}
                                className="inline-flex items-center gap-1 text-[11px] border border-warelyn-border rounded-md px-2 py-1 text-warelyn-primary bg-white hover:bg-blue-50 transition-colors"
                              >
                                {action.label}
                                <ExternalLink size={9} />
                              </Link>
                            ))}
                          </div>
                        )}
                        <div className="flex items-center gap-2 pt-1">
                          <button onClick={() => feedback(message.id, 'UP')} className="p-1 rounded hover:bg-white text-warelyn-muted hover:text-warelyn-text transition-colors">
                            <ThumbsUp size={13} />
                          </button>
                          <button onClick={() => feedback(message.id, 'DOWN')} className="p-1 rounded hover:bg-white text-warelyn-muted hover:text-warelyn-text transition-colors">
                            <ThumbsDown size={13} />
                          </button>
                          {typeof message.confidence_score === 'number' && (
                            <span className="ml-auto text-[10px] text-warelyn-muted">
                              confidence {message.confidence_score.toFixed(2)}
                            </span>
                          )}
                          {message.confidence_score != null && (
                            <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                              message.confidence_score >= 0.75 ? 'bg-emerald-50 text-emerald-700' :
                              message.confidence_score >= 0.45 ? 'bg-amber-50 text-amber-700' :
                              'bg-gray-100 text-gray-500'
                            }`}>
                              {message.confidence_score >= 0.75 ? 'HIGH' : message.confidence_score >= 0.45 ? 'MEDIUM' : 'LOW'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div key={message.id} className="flex justify-end">
                      <div className="max-w-[78%] rounded-2xl rounded-br-sm bg-warelyn-primary text-white px-4 py-2.5 text-sm leading-relaxed">
                        {message.content}
                      </div>
                    </div>
                  )
                ))}
                {sending && (
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot size={14} className="text-emerald-600" />
                    </div>
                    <div className="max-w-[70%] rounded-2xl rounded-tl-sm bg-gray-50 border border-warelyn-border px-4 py-3 space-y-2">
                      <div className="space-y-1.5">
                        <div className="h-2.5 bg-warelyn-border rounded animate-pulse w-full" />
                        <div className="h-2.5 bg-warelyn-border rounded animate-pulse w-4/5" />
                        <div className="h-2.5 bg-warelyn-border rounded animate-pulse w-3/5" />
                      </div>
                      <div className="flex items-center gap-1 pt-1">
                        {[0, 150, 300].map((delay) => (
                          <span
                            key={delay}
                            className="w-1.5 h-1.5 rounded-full bg-warelyn-muted animate-bounce"
                            style={{ animationDelay: `${delay}ms` }}
                          />
                        ))}
                        <span className="text-[11px] text-warelyn-muted ml-1">Thinking…</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </>
            )}
          </div>

          <div className="border-t border-warelyn-border p-3 bg-white">
            <div className="flex items-center gap-2 border border-warelyn-border rounded-full px-3 py-2 bg-white focus-within:border-warelyn-primary transition-colors">
              <Sparkles size={15} className="text-warelyn-primary flex-shrink-0" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuestion(); } }}
                placeholder="Ask about stock, orders, reports, workflows…"
                disabled={sending}
                className="flex-1 text-sm bg-transparent outline-none text-warelyn-text placeholder:text-warelyn-muted disabled:cursor-not-allowed"
              />
              <button
                type="button"
                onClick={() => sendQuestion()}
                disabled={sending || !question.trim()}
                className="w-7 h-7 rounded-full bg-warelyn-primary text-white flex items-center justify-center flex-shrink-0 transition hover:brightness-105 disabled:opacity-40 disabled:cursor-not-allowed"
                aria-label="Send"
              >
                <Send size={13} />
              </button>
            </div>
            <p className="text-[10px] text-center text-warelyn-muted mt-1.5">
              Warelyn Copilot · Read-only · Grounded answers only
            </p>
          </div>
        </div>
      </div>

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setDeleteTarget(null)}>
          <div className="w-80 rounded-xl border border-warelyn-border bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-semibold text-warelyn-text">Delete session?</h3>
            <p className="mt-1 text-xs text-warelyn-muted">This will permanently delete the session and all its messages.</p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                className="rounded-lg border border-warelyn-border px-3 py-1.5 text-xs font-medium text-warelyn-text hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}