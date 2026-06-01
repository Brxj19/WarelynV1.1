import { Bot, Send, Sparkles, X } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from './ui/Badge.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as faqService from '../services/faqService.js';

const allowedRoles = new Set([
  'TENANT_ADMIN',
  'INVENTORY_MANAGER',
  'SALES_STAFF',
  'PURCHASE_STAFF',
  'VIEWER',
]);

function confidenceTone(confidence) {
  if (confidence === 'HIGH') return 'success';
  if (confidence === 'MEDIUM') return 'warning';
  return 'neutral';
}

export function FaqChatWidget() {
  const { accessToken, user } = useAuth();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [messages, setMessages] = useState([]);
  const widgetBottomRef = useRef(null);

  const canUseFaq = useMemo(() => allowedRoles.has(user?.role), [user?.role]);

  useEffect(() => {
    if (!open || !canUseFaq || suggestions.length > 0) return;
    faqService.getFaqSuggestions(accessToken).then(setSuggestions).catch(() => {});
  }, [accessToken, canUseFaq, open, suggestions.length]);

  useEffect(() => {
    widgetBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, asking]);

  if (!canUseFaq) return null;

  async function ask(inputQuestion) {
    const value = (inputQuestion ?? question).trim();
    if (!value || asking) return;

    const promptMessage = { role: 'USER', content: value };
    setMessages((prev) => [...prev, promptMessage]);
    setQuestion('');
    setAsking(true);

    try {
      const response = await faqService.askFaq(accessToken, value);
      setMessages((prev) => [...prev, { role: 'ASSISTANT', content: response.answer, payload: response }]);
    } catch (error) {
      toast.error(error.message || 'Unable to answer right now.');
      setMessages((prev) => [...prev, { role: 'ASSISTANT', content: 'I could not answer right now. Please try again.' }]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-40">
      {open ? (
        <div className="absolute bottom-14 right-0 w-[22rem] rounded-xl border border-warelyn-border bg-white shadow-xl">
          <div className="flex items-center justify-between rounded-t-xl border-b border-warelyn-border bg-slate-50 px-3 py-2">
            <div className="inline-flex items-center gap-2 text-sm font-semibold text-warelyn-text">
              <Sparkles size={16} className="text-warelyn-primary" />
              FAQ Assistant
            </div>
            <button
              type="button"
              className="rounded-md p-1 text-warelyn-muted transition hover:bg-slate-100 hover:text-warelyn-text"
              onClick={() => setOpen(false)}
              aria-label="Close FAQ chat"
            >
              <X size={16} />
            </button>
          </div>

          <div className="max-h-80 space-y-3 overflow-y-auto px-3 py-3">
            {messages.length === 0 ? (
              suggestions.length === 0 ? (
                <div className="space-y-2">
                  <p className="text-xs text-warelyn-muted">Loading suggestions…</p>
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-8 bg-warelyn-border rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-warelyn-muted">Ask product and workflow questions.</p>
                  {suggestions.slice(0, 3).map((item) => (
                    <button
                      key={item.question}
                      type="button"
                      className="w-full rounded-lg border border-warelyn-border bg-white px-2 py-2 text-left text-xs font-medium text-warelyn-text transition hover:border-warelyn-primary hover:bg-blue-50/40"
                      onClick={() => ask(item.question)}
                    >
                      {item.question}
                    </button>
                  ))}
                </div>
              )
            ) : (
              <>
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`rounded-lg px-3 py-2 text-xs ${
                      message.role === 'USER'
                        ? 'ml-8 bg-warelyn-primary text-white'
                        : 'mr-8 border border-warelyn-border bg-slate-50 text-warelyn-text'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.role === 'ASSISTANT' && message.payload?.confidence ? (
                      <div className="mt-2">
                        <Badge tone={confidenceTone(message.payload.confidence)}>{message.payload.confidence}</Badge>
                      </div>
                    ) : null}
                    {message.role === 'ASSISTANT' && message.payload?.suggested_actions?.length ? (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {message.payload.suggested_actions.slice(0, 2).map((action) => (
                          <Link
                            key={`${action.to}-${action.label}`}
                            className="rounded-md border border-warelyn-border bg-white px-2 py-1 text-[11px] font-semibold text-warelyn-primary hover:bg-blue-50"
                            to={action.to}
                          >
                            {action.label}
                          </Link>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
                {asking && (
                  <div className="flex items-start gap-1.5 mr-8">
                    <div className="w-5 h-5 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Sparkles size={10} className="text-emerald-600" />
                    </div>
                    <div className="rounded-lg rounded-tl-sm bg-gray-50 border border-warelyn-border px-2.5 py-2 space-y-1.5">
                      <div className="h-2 bg-warelyn-border rounded animate-pulse w-32" />
                      <div className="h-2 bg-warelyn-border rounded animate-pulse w-24" />
                      <div className="flex items-center gap-1 pt-0.5">
                        {[0, 150, 300].map((delay) => (
                          <span
                            key={delay}
                            className="w-1 h-1 rounded-full bg-warelyn-muted animate-bounce"
                            style={{ animationDelay: `${delay}ms` }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={widgetBottomRef} />
              </>
            )}
          </div>

          <div className="border-t border-warelyn-border p-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    ask();
                  }
                }}
                placeholder="Ask a question..."
                className="h-9 w-full rounded-md border border-warelyn-border bg-white px-3 text-xs text-warelyn-text outline-none ring-0 placeholder:text-warelyn-muted focus:border-warelyn-primary"
              />
              <button
                type="button"
                onClick={() => ask()}
                disabled={asking}
                className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-warelyn-primary text-white transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
                aria-label="Send FAQ question"
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <button
        type="button"
        className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-warelyn-primary text-white shadow-lg transition hover:brightness-105"
        onClick={() => setOpen(true)}
        aria-label="Open FAQ assistant"
        title="FAQ Assistant"
      >
        <Sparkles size={20} />
      </button>
    </div>
  );
}
