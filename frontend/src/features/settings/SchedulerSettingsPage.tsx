import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  fetchSchedulerSettings,
  runSchedulerRouletteNow,
  updateSchedulerSettings,
  type SchedulerSettings,
  type SchedulerSettingsInput,
} from "../../api/scheduler";
import { ApiError } from "../../api/client";
import {
  Button,
  FormSection,
  FormStickyActions,
  NumberStepper,
  SchedulerWeekdayPicker,
  SegmentedControl,
  SettingsSectionHeader,
  Switch,
  TimezoneSelect,
} from "../../components/ui";
import { formatInstantInTimeZone } from "../../lib/datetime";
import { WEEK_OFFSET_OPTIONS } from "../../lib/timezones";
import { useAuth } from "../auth/AuthContext";
import { SettingsPageShell } from "./SettingsPageShell";

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
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Roulette run failed");
    }
    try {
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to refresh scheduler settings");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <SettingsPageShell title="Auto roulette" subtitle="Scheduled week generation." loading>
        {null}
      </SettingsPageShell>
    );
  }

  return (
    <SettingsPageShell
      title="Auto roulette"
      subtitle="Generate next week on a schedule; optional Telegram “New roulette”."
    >
      {settings?.last_roulette_at ? (
        <p className="muted admin-notice">
          Last roulette ({settings.timezone}):{" "}
          {formatInstantInTimeZone(settings.last_roulette_at, settings.timezone)}
        </p>
      ) : null}
      {settings?.last_error ? <p className="error">Last error: {settings.last_error}</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="muted admin-notice">{notice}</p> : null}

      <form onSubmit={(event) => void handleSubmit(event)} className="admin-form">
        <FormSection title="Schedule">
          <SettingsSectionHeader
            title="Schedule automatic roulette"
            description="Automatically generate the plan on selected days."
            trailing={
              <Switch
                checked={form.enabled ?? false}
                onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
                label="Enable scheduled roulette"
              />
            }
          />

          <div className="admin-field-stack">
            <span className="muted">Run on</span>
            <SchedulerWeekdayPicker
              value={form.run_weekday ?? 4}
              onChange={(run_weekday) => setForm({ ...form, run_weekday })}
              ariaLabel="Run on weekday"
            />
          </div>

          <div className="grid-2">
            <label>
              At
              <input
                type="time"
                value={form.run_time ?? "18:00"}
                onChange={(event) => setForm({ ...form, run_time: event.target.value })}
              />
            </label>
            <label>
              Timezone
              <TimezoneSelect
                value={form.timezone ?? "Europe/Paris"}
                onChange={(timezone) => setForm({ ...form, timezone })}
              />
            </label>
          </div>

          <div className="stack">
            <span className="muted">Plan for</span>
            <SegmentedControl
              className="segmented-control-full"
              ariaLabel="Target week offset"
              value={form.target_week_offset ?? 1}
              options={[...WEEK_OFFSET_OPTIONS]}
              onChange={(target_week_offset) => setForm({ ...form, target_week_offset })}
            />
          </div>
        </FormSection>

        <FormSection title="Telegram notification">
          <SettingsSectionHeader
            title="Telegram notification"
            description="Notify Telegram subscribers after roulette."
            trailing={
              <Switch
                checked={form.notify_telegram ?? true}
                onChange={(event) => setForm({ ...form, notify_telegram: event.target.checked })}
                label="Notify Telegram subscribers after roulette"
              />
            }
          />

          <NumberStepper
            ariaLabel="Planning days in Telegram message"
            label="Planning days in Telegram message"
            min={1}
            max={7}
            value={form.notify_planning_days ?? 7}
            onChange={(notify_planning_days) => setForm({ ...form, notify_planning_days })}
          />
          <p className="muted admin-field-hint">
            Includes today and the following {Math.max(0, (form.notify_planning_days ?? 7) - 1)} day
            {(form.notify_planning_days ?? 7) - 1 === 1 ? "" : "s"}.
          </p>
        </FormSection>

        <FormStickyActions>
          <Button type="submit" loading={saving} disabled={running}>
            Save settings
          </Button>
          <Button
            type="button"
            variant="roulette"
            loading={running}
            disabled={saving}
            onClick={() => void handleRunNow()}
          >
            Run roulette now
          </Button>
        </FormStickyActions>
      </form>
    </SettingsPageShell>
  );
}
