import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { AppLogo } from '../components/AppLogo.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { PasswordInput } from '../components/ui/PasswordInput.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as authService from '../services/authService.js';

const RESET_STEP = {
  ENTER_EMAIL: 'ENTER_EMAIL',
  ENTER_CODE: 'ENTER_CODE',
  ENTER_PASSWORD: 'ENTER_PASSWORD',
};

const STEP_ORDER = [RESET_STEP.ENTER_EMAIL, RESET_STEP.ENTER_CODE, RESET_STEP.ENTER_PASSWORD];

function stepLabel(step) {
  const index = STEP_ORDER.indexOf(step);
  return `Step ${index + 1} of 3`;
}

export function ForgotPasswordPage() {
  const toast = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(RESET_STEP.ENTER_EMAIL);
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmitPassword = useMemo(
    () => newPassword.length >= 8 && confirmPassword.length >= 8 && newPassword === confirmPassword,
    [confirmPassword, newPassword],
  );

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) return;
    setResetToken(token);
    setStep(RESET_STEP.ENTER_PASSWORD);
    setError('');
  }, [searchParams]);

  async function sendCode(event) {
    event.preventDefault();
    if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
      setError('Enter a valid email address.');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      await authService.requestPasswordReset(email.trim());
      setStep(RESET_STEP.ENTER_CODE);
      toast.success('If the account exists, a reset code has been sent.');
    } catch (err) {
      setError(err.payload?.error?.message ?? 'Unable to send reset code right now.');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function verifyCode(event) {
    event.preventDefault();
    if (!code || code.trim().length < 6) {
      setError('Enter the 6-digit code from your email.');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      const data = await authService.verifyResetCode(email.trim(), code.trim());
      setResetToken(data.reset_token);
      setStep(RESET_STEP.ENTER_PASSWORD);
    } catch (err) {
      const codeValue = err.payload?.error?.code;
      if (codeValue === 'RESET_CODE_ATTEMPTS_EXCEEDED') {
        setError('Too many attempts. Request a new code.');
      } else {
        setError('That code is incorrect or has expired.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function resendCode(event) {
    event.preventDefault();
    if (!email) return;
    setError('');
    try {
      await authService.requestPasswordReset(email.trim());
      toast.success('Code resent. Check your inbox.');
    } catch {
      toast.error('Unable to resend code right now.');
    }
  }

  async function updatePassword(event) {
    event.preventDefault();
    if (!canSubmitPassword) {
      if (newPassword.length < 8) {
        setError('Password must be at least 8 characters.');
      } else if (newPassword !== confirmPassword) {
        setError('Passwords do not match.');
      }
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      await authService.resetPassword(resetToken, newPassword);
      navigate('/login', { state: { successMessage: 'Password updated. Please sign in.' }, replace: true });
    } catch (err) {
      const codeValue = err.payload?.error?.code;
      if (codeValue === 'INVALID_RESET_TOKEN' || codeValue === 'RESET_TOKEN_ALREADY_USED') {
        setStep(RESET_STEP.ENTER_EMAIL);
        setResetToken('');
        setCode('');
        setNewPassword('');
        setConfirmPassword('');
        setError('Your reset session expired. Request a new code.');
      } else {
        setError(err.payload?.error?.message ?? 'Unable to reset password right now.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-md rounded-[28px] border border-warelyn-border shadow-[0_20px_48px_rgba(15,23,42,0.08)]">
      <CardBody className="p-8 sm:p-9">
        <div className="mb-8">
          <AppLogo className="mb-6" size="auth-form" variant="full" />
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-warelyn-primary">Account recovery</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-warelyn-text">Forgot password</h1>
          <p className="mt-2 text-sm leading-6 text-warelyn-muted">Reset your password in a secure three-step flow.</p>
          <div className="mt-4 inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold text-warelyn-primary">
            {stepLabel(step)}
          </div>
        </div>

        {error ? <div className="mb-4"><ErrorState description={error} title="Action failed" /></div> : null}

        {step === RESET_STEP.ENTER_EMAIL ? (
          <form className="mt-6 space-y-4" onSubmit={sendCode}>
            <Input
              autoComplete="email"
              id="forgot-email"
              label="Email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              type="email"
              value={email}
            />
            <Button className="w-full" isLoading={isSubmitting} type="submit">
              {isSubmitting ? 'Sending code...' : 'Send reset code'}
            </Button>
          </form>
        ) : null}

        {step === RESET_STEP.ENTER_CODE ? (
          <form className="mt-6 space-y-4" onSubmit={verifyCode}>
            <p className="text-xs text-warelyn-muted">Code sent to {email}</p>
            <Input
              id="reset-code"
              inputMode="numeric"
              label="6-digit code"
              maxLength={6}
              onChange={(event) => setCode(event.target.value)}
              placeholder="123456"
              type="text"
              value={code}
            />
            <Button className="w-full" isLoading={isSubmitting} type="submit">
              {isSubmitting ? 'Verifying code...' : 'Verify code'}
            </Button>
            <button className="text-xs font-semibold text-warelyn-primary hover:underline" onClick={resendCode} type="button">
              Resend code
            </button>
          </form>
        ) : null}

        {step === RESET_STEP.ENTER_PASSWORD ? (
          <form className="mt-6 space-y-4" onSubmit={updatePassword}>
            <PasswordInput
              autoComplete="new-password"
              id="new-password"
              label="New password"
              minLength={8}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="At least 8 characters"
              value={newPassword}
            />
            <PasswordInput
              autoComplete="new-password"
              id="confirm-password"
              label="Confirm password"
              minLength={8}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Re-enter password"
              value={confirmPassword}
            />
            <Button className="w-full" disabled={!canSubmitPassword || isSubmitting} isLoading={isSubmitting} type="submit">
              {isSubmitting ? 'Updating password...' : 'Set new password'}
            </Button>
          </form>
        ) : null}

        <p className="mt-6 text-center text-sm text-warelyn-muted">
          Back to{' '}
          <Link className="font-semibold text-warelyn-primary hover:text-blue-900" to="/login">
            Sign in
          </Link>
        </p>
      </CardBody>
    </Card>
  );
}
