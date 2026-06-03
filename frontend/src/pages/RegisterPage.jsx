import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { AppLogo } from '../components/AppLogo.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { PasswordInput } from '../components/ui/PasswordInput.jsx';
import { PhoneInput } from '../components/ui/PhoneInput.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { isValidPhone, parsePhone } from '../lib/phone.js';

const initialValues = {
  company_name: '',
  name: '',
  email: '',
  phone: '',
  password: '',
};

function validate(values) {
  if (!values.company_name || !values.name || !values.email || !values.password) {
    return 'Company name, admin name, email, and password are required.';
  }
  if (!/^\S+@\S+\.\S+$/.test(values.email)) {
    return 'Enter a valid email address.';
  }
  if (values.password.length < 8) {
    return 'Password must be at least 8 characters.';
  }
  if (values.phone) {
    const { countryCode, localNumber } = parsePhone(values.phone);
    const phoneResult = isValidPhone(countryCode, localNumber);
    if (!phoneResult.valid) return phoneResult.error;
  }
  return null;
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [values, setValues] = useState(initialValues);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const validationError = validate(values);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await register({ ...values, phone: values.phone || null });
      setSuccess('Tenant created. You can now sign in with the tenant admin account.');
      setTimeout(() => navigate('/login'), 900);
    } catch (err) {
      setError(err.payload?.error?.message ?? 'Unable to register tenant.');
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateField(field) {
    return (event) => setValues((current) => ({ ...current, [field]: event.target.value }));
  }

  return (
    <Card className="w-full max-w-lg rounded-[28px] border border-warelyn-border shadow-[0_20px_48px_rgba(15,23,42,0.08)]">
      <CardBody className="p-8 sm:p-9">
        <div className="mb-8">
          <AppLogo className="mb-6" size="auth-form" variant="full" />
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-warelyn-primary">New workspace</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-warelyn-text">Create your Warelyn workspace</h1>
          <p className="mt-2 text-sm leading-6 text-warelyn-muted">Set up the tenant workspace and first admin account for your operations team.</p>
        </div>

        {error ? <div className="mb-4"><ErrorState description={error} title="Registration failed" /></div> : null}
        {success ? <div className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700">{success}</div> : null}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <Input id="company_name" label="Company name" onChange={updateField('company_name')} placeholder="Acme Warehousing" value={values.company_name} />
          <Input id="name" label="Admin name" onChange={updateField('name')} placeholder="Jane Operator" value={values.name} />
          <Input autoComplete="email" id="email" label="Admin email" onChange={updateField('email')} placeholder="admin@example.com" type="email" value={values.email} />
          <PhoneInput label="Phone (optional)" value={values.phone} onChange={(val) => setValues((current) => ({ ...current, phone: val }))} />
          <PasswordInput
            autoComplete="new-password"
            id="password"
            label="Password"
            minLength={8}
            onChange={updateField('password')}
            placeholder="Minimum 8 characters"
            value={values.password}
          />
          <Button className="w-full" isLoading={isSubmitting} type="submit">
            {isSubmitting ? 'Creating workspace...' : 'Create workspace'}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-warelyn-muted">
          Already registered?{' '}
          <Link className="font-semibold text-warelyn-primary hover:text-blue-900" to="/login">
            Sign in
          </Link>
        </p>
      </CardBody>
    </Card>
  );
}
