import { FormEvent, useEffect, useState } from "react";

import {
  fetchBackupRuns,
  fetchBackupSettings,
  runBackupNow,
  updateBackupSettings,
  type BackupRun,
  type BackupSettings,
  type BackupSettingsInput,
} from "../../api/backup";
import { ApiError } from "../../api/client";
import { Button, EmptyState, FormSection, FormStickyActions, NumberStepper, Switch } from "../../components/ui";
import { formatInstantInTimeZone } from "../../lib/datetime";
import { useAuth } from "../auth/AuthContext";
import { SettingsPageShell } from "./SettingsPageShell";

function timeInputValue(value: string): string {
  return value.slice(0, 5);
}

export function BackupSettingsPage() {
  const { accessToken, isAdmin } = useAuth();
  const [settings, setSettings] = useState<BackupSettings | null>(null);
  const [runs, setRuns] = useState<BackupRun[]>([]);
  const [form, setForm] = useState<BackupSettingsInput>({
    enabled: false,
    run_time: "03:00",
    timezone: "Europe/Paris",
    retention_days: 30,
    backup_path: "/backups",
    include_json_export: true,
    include_pg_dump: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken || !isAdmin) {
      return;
    }
    let cancelled = false;
    Promise.all([fetchBackupSettings(accessToken), fetchBackupRuns(accessToken)])
      .then(([settingsData, runsData]) => {
        if (cancelled) {
          return;
        }
        setSettings(settingsData);
        setRuns(runsData);
        setForm({
          enabled: settingsData.enabled,
          run_time: timeInputValue(settingsData.run_time),
          timezone: settingsData.timezone,
          retention_days: settingsData.retention_days,
          backup_path: settingsData.backup_path,
          include_json_export: settingsData.include_json_export,
          include_pg_dump: settingsData.include_pg_dump,
        });
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load backup settings");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, isAdmin]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateBackupSettings(accessToken, {
        ...form,
        run_time: `${form.run_time}:00`,
      });
      setSettings(updated);
      setNotice("Backup settings saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save backup settings");
    } finally {
      setSaving(false);
    }
  }

  async function handleRunNow() {
    if (!accessToken) {
      return;
    }
    setRunning(true);
    setError(null);
    setNotice(null);
    try {
      const created = await runBackupNow(accessToken);
      setRuns(await fetchBackupRuns(accessToken));
      setNotice(`Backup finished (${created.length} artifact${created.length === 1 ? "" : "s"}).`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Backup run failed");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return (
      <SettingsPageShell title="Backups" subtitle="JSON export, schedule, and retention." loading>
        {null}
      </SettingsPageShell>
    );
  }

  return (
    <SettingsPageShell
      title="Backups"
      subtitle="Full JSON export to /backups, optional pg_dump, and nightly schedule."
    >
      <form onSubmit={handleSubmit} className="admin-form">
        <FormSection title="Schedule">
          <Switch
            checked={form.enabled === true}
            onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
            label="Enable scheduled backups"
          />
          <div className="grid-2">
            <label>
              Run time
              <input
                type="time"
                value={form.run_time ?? "03:00"}
                onChange={(event) => setForm({ ...form, run_time: event.target.value })}
              />
            </label>
            <label>
              Timezone
              <input
                value={form.timezone ?? "Europe/Paris"}
                onChange={(event) => setForm({ ...form, timezone: event.target.value })}
              />
            </label>
          </div>
          <NumberStepper
            ariaLabel="Retention days"
            label="Retention (days)"
            min={1}
            max={365}
            value={form.retention_days ?? 30}
            onChange={(retention_days) => setForm({ ...form, retention_days })}
          />
          <label>
            Backup path
            <input
              value={form.backup_path ?? "/backups"}
              onChange={(event) => setForm({ ...form, backup_path: event.target.value })}
            />
          </label>
          <div className="admin-switch-stack">
            <Switch
              checked={form.include_json_export === true}
              onChange={(event) => setForm({ ...form, include_json_export: event.target.checked })}
              label="JSON export"
            />
            <Switch
              checked={form.include_pg_dump === true}
              onChange={(event) => setForm({ ...form, include_pg_dump: event.target.checked })}
              label="PostgreSQL dump"
            />
          </div>
        </FormSection>

        <FormStickyActions>
          <Button type="submit" loading={saving} disabled={running}>
            Save settings
          </Button>
          <Button type="button" loading={running} disabled={saving} onClick={() => void handleRunNow()}>
            Run backup now
          </Button>
        </FormStickyActions>
      </form>

      {settings?.last_backup_at ? (
        <p className="muted admin-notice">
          Last backup: {formatInstantInTimeZone(settings.last_backup_at, settings.timezone)}
        </p>
      ) : null}
      {settings?.last_error ? <p className="error">{settings.last_error}</p> : null}
      {notice ? <p className="muted admin-notice">{notice}</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      <FormSection title="Recent runs">
        {runs.length === 0 ? (
          <EmptyState title="No backup runs yet" description="Run a backup manually or enable the schedule." />
        ) : (
          <ul className="admin-data-list">
            {runs.map((run) => (
              <li key={run.id} className="admin-data-card">
                <div className="admin-data-card-header">
                  <strong>
                    {run.backup_type} — {run.status}
                  </strong>
                </div>
                {run.file_path ? <p className="muted">{run.file_path}</p> : null}
                {run.error_message ? <p className="error">{run.error_message}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </FormSection>
    </SettingsPageShell>
  );
}
