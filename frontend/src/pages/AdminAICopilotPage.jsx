import { Bot, MessageSquare, Send, ThumbsDown, ThumbsUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as assistantService from '../services/assistantService.js';

function confidenceTone(confidenceScore) {
  if (typeof confidenceScore !== 'number') return 'neutral';
  if (confidenceScore >= 0.75) return 'success';
  if (confidenceScore >= 0.45) return 'warning';
  return 'neutral';
}

function samplePrompts() {
  return [
    'What needs my attention today?',
    'Which workflow queue is currently the biggest bottleneck?',
    'How can I reduce pending returns and reconciliation mismatches?',
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

  async function boot() {
    setLoading(true);
    setError('');
    try {
      const created = await assistantService.createAssistantSession(accessToken, `Session ${new Date().toLocaleString()}`);
      const detail = await assistantService.getAssistantSession(accessToken, created.id);
      setSession(detail.session);
      setMessages(detail.messages);
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
    setSending(true);
    setError('');
    try {
      const result = await assistantService.askAssistant(accessToken, session.id, value);
      setMessages((prev) => [...prev, result.message]);
      setQuestion('');
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

  if (loading) return <LoadingState message="Loading AI copilot..." />;

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Tenant Admin"
        title="AI Copilot"
        description="Read-only operational copilot with grounded answers and citations."
      />
      {error ? <ErrorState description={error} /> : null}

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold text-warelyn-text">Assistant health</h2>
          </CardHeader>
          <CardBody className="space-y-2 text-sm">
            <p>Total requests: <span className="font-semibold">{telemetry?.total_requests ?? 0}</span></p>
            <p>Avg latency: <span className="font-semibold">{telemetry?.avg_latency_ms ?? 0} ms</span></p>
            <p>Abstain rate: <span className="font-semibold">{telemetry?.abstain_rate_pct ?? 0}%</span></p>
            <p>Citation rate: <span className="font-semibold">{telemetry?.citation_rate_pct ?? 0}%</span></p>
          </CardBody>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <h2 className="text-base font-semibold text-warelyn-text">Ask the copilot</h2>
          </CardHeader>
          <CardBody className="space-y-3">
            <Input
              label="Question"
              placeholder="Ask about workload, bottlenecks, workflow risks..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <div className="flex items-center gap-2">
              <Button onClick={() => sendQuestion()} disabled={sending}>
                <Send size={16} />
                {sending ? 'Thinking...' : 'Send'}
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-warelyn-text">Suggested prompts</h2>
        </CardHeader>
        <CardBody className="flex flex-wrap gap-2">
          {samplePrompts().map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="rounded-full border border-warelyn-border bg-white px-3 py-1.5 text-xs font-semibold text-warelyn-primary transition hover:bg-blue-50"
              onClick={() => {
                setQuestion(prompt);
                sendQuestion(prompt);
              }}
            >
              {prompt}
            </button>
          ))}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-warelyn-text">Conversation</h2>
        </CardHeader>
        <CardBody>
          {messages.length === 0 ? (
            <EmptyState title="No messages yet" description="Ask your first question to start the copilot conversation." />
          ) : (
            <div className="space-y-3">
              {messages.map((message) => (
                <div key={message.id} className="rounded-xl border border-warelyn-border bg-white p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="inline-flex items-center gap-2 text-xs font-semibold text-warelyn-muted">
                      {message.role === 'ASSISTANT' ? <Bot size={14} /> : <MessageSquare size={14} />}
                      {message.role}
                    </div>
                    {message.role === 'ASSISTANT' ? (
                      <Badge tone={confidenceTone(message.confidence_score)}>
                        confidence {typeof message.confidence_score === 'number' ? message.confidence_score.toFixed(2) : 'n/a'}
                      </Badge>
                    ) : null}
                  </div>

                  <p className="whitespace-pre-wrap text-sm text-warelyn-text">{message.content}</p>

                  {message.citations_json?.length ? (
                    <div className="mt-3 space-y-2">
                      <p className="text-xs font-semibold text-warelyn-text">Citations</p>
                      {message.citations_json.map((citation, index) => (
                        <div className="rounded-md border border-warelyn-border bg-slate-50 px-2 py-1 text-xs" key={`${message.id}-${index}`}>
                          <p className="font-semibold text-warelyn-text">{citation.title}</p>
                          <p className="text-warelyn-muted">{citation.source_type}</p>
                          {citation.source_uri ? <p className="text-warelyn-muted">{citation.source_uri}</p> : null}
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {message.suggested_actions_json?.length ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {message.suggested_actions_json.map((action, index) => (
                        <Link key={`${message.id}-a-${index}`} to={action.to} className="rounded-md border border-warelyn-border px-2 py-1 text-xs font-semibold text-warelyn-primary hover:bg-blue-50">
                          {action.label}
                        </Link>
                      ))}
                    </div>
                  ) : null}

                  {message.role === 'ASSISTANT' ? (
                    <div className="mt-3 flex items-center gap-2">
                      <Button size="sm" variant="ghost" onClick={() => feedback(message.id, 'UP')}>
                        <ThumbsUp size={14} />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => feedback(message.id, 'DOWN')}>
                        <ThumbsDown size={14} />
                      </Button>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
