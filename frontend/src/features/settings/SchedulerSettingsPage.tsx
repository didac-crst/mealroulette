import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  fetchSchedulerSettings,
  runSchedulerRouletteNow,
  schedulerWeekdayLabel,
  updateSchedulerSettings,
  type SchedulerSettings,
  type SchedulerSettingsInput,
} from "../../api/scheduler";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { useAuth } from "../auth/AuthContext";

function timeInputValue(value: string): string {
  return value.slice(0, 5);
}

export function SchedulerSettingsPage() {
  const { accessToken, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [settings, setSettings] = useState<SchedulerSettings | null>(null);
  const [form, setForm] = useState<SchedulerSettingsInput>({
    enabled: false,
    run_weekday: 4,
    run_time: "18:00",
    timezone: "Europe/Paris",
    target_week_offset: 1,
    notify_telegram: true,
    notify_planning_days: 7,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) {
      navigate("/review");
    }
  }, [isAdmin, navigate]);

  const reload = async () => {
    if (!accessToken) {
      return;
    }
    const settingsData = await fetchSchedulerSettings(accessToken);
    setSettings(settingsData);
    setForm({
      enabled: settingsData.enabled,
      run_weekday: settingsData.run_weekday,
      run_time: timeInputValue(settingsData.run_time),
      timezone: settingsData.timezone,
      target_week_offset: settingsData.target_week_offset,
      notify_telegram: settingsData.notify_telegram,
      notify_planning_days: settingsData.notify_planning_days,
    });
  };

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    reload()
      .then(() => {
        if (!cancelled) {
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load scheduler settings");
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
  }, [accessToken]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateSchedulerSettings(accessToken, {
        ...form,
        run_time: `${form.run_time}:00`,
      });
      setSettings(updated);
      setNotice("Settings saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleRunNow = async () => {
    if (!accessToken) {
      return;
    }
    setRunning(true);
    setError(null);
    setNotice(null);
    try {
      const result = await runSchedulerRouletteNow(accessToken);
      setNotice(result.detail);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Roulette run failed");
      await reload();
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <section className="card">
        <p className="muted">Loading scheduler settings…</p>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between">
        <h2>Scheduled roulette</h2>
        <ButtonLink to="/review" variant="secondary">
          Back
        </ButtonLink>
      </div>

      <p className="muted">
        The worker checks every minute. When enabled, it generates the target week (default: next
        Mon–Sun) at the configured weekday and time, then optionally broadcasts a{" "}
        <strong>New roulette</strong> Telegram message with the meal plan.
      </p>

      {settings?.last_roulette_at ? (
        <p className="muted">Last roulette: {new Date(settings.last_roulette_at).toLocaleString()}</p>
      ) : null}
      {settings?.last_error ? <p className="error">Last error: {settings.last_error}</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="muted">{notice}</p> : null}

      <form onSubmit={(event) => void handleSubmit(event)} className="stack">
        <label className="checkbox-pill">
          <input
            type="checkbox"
            checked={form.enabled ?? false}
            onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
          />
          Enable scheduled roulette
        </label>

        <div className="grid-2">
          <label>
            Run on
            <select
              value={form.run_weekday ?? 4}
              onChange={(event) => setForm({ ...form, run_weekday: Number(event.target.value) })}
            >
              {Array.from({ length: 7 }, (_, weekday) => (
                <option key={weekday} value={weekday}>
                  {schedulerWeekdayLabel(weekday)}
                </option>
              ))}
            </select>
          </label>
          <label>
            At
            <input
              type="time"
              value={form.run_time ?? "18:00"}
              onChange={(event) => setForm({ ...form, run_time: event.target.value })}
            />
          </label>
        </div>

        <div className="grid-2">
          <label>
            Timezone
            <input
              value={form.timezone ?? "Europe/Paris"}
              onChange={(event) => setForm({ ...form, timezone: event.target.value })}
            />
          </label>
          <label>
            Target week offset
            <input
              type="number"
              min={0}
              max={4}
              value={form.target_week_offset ?? 1}
              onChange={(event) => setForm({ ...form, target_week_offset: Number(event.target.value) })}
            />
            <span className="muted">0 = this week, 1 = next week</span>
          </label>
        </div>

        <label className="checkbox-pill">
          <input
            type="checkbox"
            checked={form.notify_telegram ?? true}
            onChange={(event) => setForm({ ...form, notify_telegram: event.target.checked })}
          />
          Notify Telegram subscribers after roulette
        </label>

        <label>
          Planning days in Telegram message
          <input
            type="number"
            min={1}
            max={14}
            value={form.notify_planning_days ?? 7}
            onChange={(event) => setForm({ ...form, notify_planning_days: Number(event.target.value) })}
          />
        </label>

        <div className="row-between">
          <button type="submit" className="button" disabled={saving}>
            {saving ? "Saving…" : "Save settings"}
          </button>
          <button
            type="button"
            className="button button-secondary"
            disabled={running}
            onClick={() => void handleRunNow()}
          >
            {running ? "Running…" : "Run roulette now"}
          </button>
        </div>
      </form>
    </section>
  );
}
