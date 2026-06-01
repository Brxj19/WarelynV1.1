import { ExternalLink, Search } from 'lucide-react';
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
import * as faqService from '../services/faqService.js';

function confidenceTone(confidence) {
  if (confidence === 'HIGH') return 'success';
  if (confidence === 'MEDIUM') return 'warning';
  return 'neutral';
}

export function FAQPage() {
  const { accessToken } = useAuth();
  const toast = useToast();
  const [suggestions, setSuggestions] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    faqService.getFaqSuggestions(accessToken)
      .then(setSuggestions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

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

  if (loading) return <LoadingState message="Loading FAQ suggestions..." />;

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
          {suggestions.length === 0 ? (
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

      {answer ? (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-warelyn-text">Answer</h2>
            <Badge tone={confidenceTone(answer.confidence)}>{answer.confidence}</Badge>
          </CardHeader>
          <CardBody className="space-y-4">
            <p className="whitespace-pre-wrap text-sm text-warelyn-text">{answer.answer}</p>

            <div>
              <h3 className="text-sm font-semibold text-warelyn-text">Citations</h3>
              {answer.citations?.length ? (
                <div className="mt-2 space-y-2">
                  {answer.citations.map((citation, index) => (
                    <div className="rounded-lg border border-warelyn-border bg-slate-50 px-3 py-2 text-xs" key={`${citation.chunk_id}-${index}`}>
                      <p className="font-semibold text-warelyn-text">{citation.title}</p>
                      <p className="text-warelyn-muted">{citation.source_type}</p>
                      {citation.source_uri ? <p className="text-warelyn-muted">{citation.source_uri}</p> : null}
                    </div>
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
