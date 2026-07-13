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
      <SettingsPageShell title="Backups" subtitle="JSON export, schedule, and retention.">
        <p className="muted">Loading…</p>
      </SettingsPageShell>
    );
  }

  return (
    <SettingsPageShell
      title="Backups"
      subtitle="Full JSON export to /backups, optional pg_dump, and nightly schedule."
    >
      <form onSubmit={handleSubmit} className="stack">
        <label className="checkbox-pill">
          <input
            type="checkbox"
            checked={form.enabled === true}
            onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
          />
          Enable scheduled backups
        </label>
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
        <label>
          Retention (days)
          <input
            type="number"
            min={1}
            value={form.retention_days ?? 30}
            onChange={(event) => setForm({ ...form, retention_days: Number(event.target.value) })}
          />
        </label>
        <label>
          Backup path
          <input
            value={form.backup_path ?? "/backups"}
            onChange={(event) => setForm({ ...form, backup_path: event.target.value })}
          />
        </label>
        <div className="tag-grid">
          <label className="checkbox-pill">
            <input
              type="checkbox"
              checked={form.include_json_export === true}
              onChange={(event) => setForm({ ...form, include_json_export: event.target.checked })}
            />
            JSON export
          </label>
          <label className="checkbox-pill">
            <input
              type="checkbox"
              checked={form.include_pg_dump === true}
              onChange={(event) => setForm({ ...form, include_pg_dump: event.target.checked })}
            />
            PostgreSQL dump
          </label>
        </div>
        <button type="submit" className="button" disabled={saving}>
          {saving ? "Saving…" : "Save settings"}
        </button>
      </form>

      <div className="stack">
        <button type="button" className="button" onClick={handleRunNow} disabled={running}>
          {running ? "Running backup…" : "Run backup now"}
        </button>
        {settings?.last_backup_at ? (
          <p className="muted">
            Last backup: {formatInstantInTimeZone(settings.last_backup_at, settings.timezone)}
          </p>
        ) : null}
        {settings?.last_error ? <p className="error">{settings.last_error}</p> : null}
      </div>

      <div>
        <h3 className="section-title">Recent runs</h3>
        {runs.length === 0 ? (
          <p className="muted">No backup runs yet.</p>
        ) : (
          <ul className="stack">
            {runs.map((run) => (
              <li key={run.id} className="card subtle">
                <strong>{run.backup_type}</strong> — {run.status}
                {run.file_path ? ` · ${run.file_path}` : ""}
                {run.error_message ? <p className="error">{run.error_message}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      {notice ? <p className="notice">{notice}</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
    </SettingsPageShell>
  );
}
