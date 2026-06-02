import { ExternalLink, FileText, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as faqService from '../services/faqService.js';

function confidenceTone(confidence) {
  if (confidence === 'HIGH') return 'success';
  if (confidence === 'MEDIUM') return 'warning';
  return 'neutral';
}

export function FAQPage() {
  const { accessToken, user } = useAuth();
  const toast = useToast();
  const storageKey = `warelyn-faq-page-${user?.id ?? 'anon'}`;
  const [suggestions, setSuggestions] = useState([]);
  const [question, setQuestion] = useState(() => {
    try {
      return sessionStorage.getItem(`${storageKey}-q`) ?? '';
    } catch {
      return '';
    }
  });
  const [answer, setAnswer] = useState(() => {
    try {
      const stored = sessionStorage.getItem(`${storageKey}-answer`);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    faqService.getFaqSuggestions(accessToken)
      .then(setSuggestions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  useEffect(() => {
    try {
      const storedQuestion = sessionStorage.getItem(`${storageKey}-q`);
      const storedAnswer = sessionStorage.getItem(`${storageKey}-answer`);
      setQuestion(storedQuestion ?? '');
      setAnswer(storedAnswer ? JSON.parse(storedAnswer) : null);
    } catch {
      setQuestion('');
      setAnswer(null);
    }
  }, [storageKey]);

  useEffect(() => {
    try {
      sessionStorage.setItem(`${storageKey}-q`, question);
    } catch {
      // Session storage is a convenience only.
    }
  }, [question, storageKey]);

  useEffect(() => {
    try {
      if (answer) {
        sessionStorage.setItem(`${storageKey}-answer`, JSON.stringify(answer));
      } else {
        sessionStorage.removeItem(`${storageKey}-answer`);
      }
    } catch {
      // Session storage is a convenience only.
    }
  }, [answer, storageKey]);

  async function handleAsk(nextQuestion) {
    const value = (nextQuestion ?? question).trim();
    if (!value) return;
    setAsking(true);
    setError('');
    try {
      const row = await faqService.askFaq(accessToken, value);
      setAnswer(row);
      setQuestion(value);
    } catch (e) {
      toast.error(e.message || 'Failed to get FAQ answer.');
      setError(e.message);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Support"
        title="FAQ Assistant"
        description="Ask product and workflow questions. Answers are grounded to available knowledge with citations."
      />
      {error ? <ErrorState description={error} /> : null}

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-warelyn-text">Ask a question</h2>
        </CardHeader>
        <CardBody className="space-y-3">
          <Input
            label="Question"
            placeholder="e.g., Why is my order still pending fulfillment?"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button onClick={() => handleAsk()} disabled={asking}>
              <Search size={16} />
              {asking ? 'Finding answer...' : 'Ask FAQ'}
            </Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-warelyn-text">Suggested questions</h2>
        </CardHeader>
        <CardBody>
          {loading ? (
            <div className="grid gap-3 md:grid-cols-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="rounded-lg border border-warelyn-border bg-white px-3 py-3 space-y-1.5">
                  <div className="h-3 bg-warelyn-border rounded animate-pulse w-4/5" />
                  <div className="h-2.5 bg-warelyn-border rounded animate-pulse w-3/5" />
                </div>
              ))}
            </div>
          ) : suggestions.length === 0 ? (
            <EmptyState title="No suggestions available" description="Try asking your question directly above." />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {suggestions.map((item) => (
                <button
                  type="button"
                  key={item.question}
                  className="rounded-lg border border-warelyn-border bg-white px-3 py-3 text-left transition hover:border-warelyn-primary hover:bg-blue-50/40"
                  onClick={() => {
                    setQuestion(item.question);
                    handleAsk(item.question);
                  }}
                >
                  <p className="text-sm font-semibold text-warelyn-text">{item.question}</p>
                  {item.description ? <p className="mt-1 text-xs text-warelyn-muted">{item.description}</p> : null}
                </button>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {asking && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="h-4 w-24 bg-warelyn-border rounded animate-pulse" />
            <div className="h-5 w-16 bg-warelyn-border rounded-full animate-pulse" />
          </CardHeader>
          <CardBody className="space-y-3">
            <div className="space-y-2">
              <div className="h-3 bg-warelyn-border rounded animate-pulse w-full" />
              <div className="h-3 bg-warelyn-border rounded animate-pulse w-full" />
              <div className="h-3 bg-warelyn-border rounded animate-pulse w-4/5" />
              <div className="h-3 bg-warelyn-border rounded animate-pulse w-5/6" />
              <div className="h-3 bg-warelyn-border rounded animate-pulse w-3/5" />
            </div>
            <div className="flex gap-2 pt-1">
              <div className="h-5 w-24 bg-warelyn-border rounded-full animate-pulse" />
              <div className="h-5 w-28 bg-warelyn-border rounded-full animate-pulse" />
              <div className="h-5 w-20 bg-warelyn-border rounded-full animate-pulse" />
            </div>
            <div className="flex gap-2">
              <div className="h-7 w-32 bg-warelyn-border rounded-md animate-pulse" />
              <div className="h-7 w-28 bg-warelyn-border rounded-md animate-pulse" />
            </div>
          </CardBody>
        </Card>
      )}

      {answer ? (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-warelyn-text">Answer</h2>
            <Badge tone={confidenceTone(answer.confidence)}>
              {answer.confidence}
              {typeof answer.confidence_score === 'number' && ` · ${answer.confidence_score.toFixed(2)}`}
            </Badge>
          </CardHeader>
          <CardBody className="space-y-4">
            <p className="whitespace-pre-wrap text-sm text-warelyn-text">{answer.answer}</p>

            <div>
              <h3 className="text-sm font-semibold text-warelyn-text">Citations</h3>
              {answer.citations?.length ? (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {answer.citations.map((c, i) => (
                    <span key={i} className="inline-flex items-center gap-1 text-[11px] bg-gray-50 border border-warelyn-border rounded-full px-2.5 py-1 text-warelyn-muted">
                      <FileText size={10} />
                      {c.title}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-1 text-xs text-warelyn-muted">No citations were available for this response.</p>
              )}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-warelyn-text">Suggested actions</h3>
              {answer.suggested_actions?.length ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {answer.suggested_actions.map((action, index) => (
                    <Link
                      key={`${action.to}-${index}`}
                      className="inline-flex items-center gap-1 rounded-md border border-warelyn-border bg-white px-3 py-1.5 text-xs font-semibold text-warelyn-primary hover:bg-blue-50"
                      to={action.to}
                    >
                      {action.label}
                      <ExternalLink size={12} />
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="mt-1 text-xs text-warelyn-muted">No direct actions suggested.</p>
              )}
            </div>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
