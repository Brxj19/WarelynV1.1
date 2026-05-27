import { useState } from 'react';

import { Button } from './ui/Button.jsx';
import { Card, CardBody, CardHeader } from './ui/Card.jsx';

export function SettingsForm({ children, description, error, fields, isLoading = false, onSave, onSuccess, sections = [], submitLabel = 'Save changes' }) {
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError('');
    setSaving(true);
    try {
      await onSave();
      if (onSuccess) onSuccess();
    } catch (err) {
      setFormError(err?.message || 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  }

  const displayError = formError || error;

  return (
    <form onSubmit={handleSubmit}>
      {sections.length > 0
        ? sections.map((section, idx) => (
            <Card key={idx} className="mb-6">
              <CardHeader>
                <h3 className="text-sm font-bold text-warelyn-text">{section.title}</h3>
                {section.description ? <p className="mt-1 text-xs text-warelyn-muted">{section.description}</p> : null}
              </CardHeader>
              <CardBody>
                <div className="grid gap-5 sm:grid-cols-2">{section.fields}</div>
              </CardBody>
            </Card>
          ))
        : null}
      {children ? <div className="mb-6">{children}</div> : null}
      {displayError ? <p className="mb-4 text-sm font-medium text-warelyn-danger">{displayError}</p> : null}
      <div className="flex items-center gap-3">
        <Button isLoading={saving || isLoading} type="submit" variant="primary">{submitLabel}</Button>
      </div>
    </form>
  );
}
