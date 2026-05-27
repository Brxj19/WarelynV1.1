import { CheckCircle2, Smartphone } from 'lucide-react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as verificationService from '../services/verificationService.js';

export function VerifyPhonePage() {
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [code, setCode] = useState('');
  const [sending, setSending] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [sendMeta, setSendMeta] = useState(null);

  async function handleSend() {
    setSending(true);
    setError('');
    try {
      const response = await verificationService.sendPhoneVerification(accessToken);
      setSent(true);
      setSendMeta(response);
      toast.success('Verification code sent to your phone.');
    } catch (e) {
      setError(e.message || 'Failed to send verification code.');
      toast.error(e.message || 'Failed to send verification code.');
    } finally {
      setSending(false);
    }
  }

  async function handleConfirm() {
    if (!code.trim()) return;
    setConfirming(true);
    setError('');
    try {
      await verificationService.confirmPhoneVerification(accessToken, code.trim());
      toast.success('Phone verified successfully!');
      navigate('/settings');
    } catch (e) {
      setError(e.message || 'Invalid verification code.');
      toast.error(e.message || 'Invalid verification code.');
    } finally {
      setConfirming(false);
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md">
      <BackButton to="/settings" />
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
              <Smartphone size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-warelyn-text">Verify Phone</h2>
              <p className="text-xs text-warelyn-muted">Confirm your phone number</p>
            </div>
          </div>
        </CardHeader>
        <CardBody>
          {user?.phone_verified_at ? (
            <div className="flex flex-col items-center gap-3 py-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600">
                <CheckCircle2 size={24} />
              </div>
              <p className="text-sm font-medium text-green-700">Phone already verified</p>
              <Button variant="secondary" onClick={() => navigate('/settings')}>Back to Settings</Button>
            </div>
          ) : (
            <>
          {error ? <ErrorState className="mb-4" description={error} /> : null}

          {!sent ? (
            <Button className="w-full" isLoading={sending} onClick={handleSend} variant="primary">
              Send Verification Code
            </Button>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-warelyn-muted">Enter the 6-digit code sent to your phone. Code expires in 10 minutes.</p>
              {sendMeta?.destination_hint ? <p className="text-xs text-warelyn-muted">Sent to {sendMeta.destination_hint}.</p> : null}
              {sendMeta?.development_code ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                  Development code: <span className="font-semibold tracking-[0.2em]">{sendMeta.development_code}</span>
                </div>
              ) : null}
              <input
                className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-center text-2xl tracking-[8px] text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                maxLength={6}
                placeholder="000000"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              />
              <div className="flex gap-3">
                <Button className="flex-1" isLoading={sending} onClick={handleSend} variant="secondary">
                  Resend Code
                </Button>
                <Button className="flex-1" isLoading={confirming} onClick={handleConfirm} variant="primary">
                  <CheckCircle2 size={16} />
                  Verify
                </Button>
              </div>
            </div>
          )}
            </>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
