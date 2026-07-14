import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  fetchTelegramSettings,
  fetchTelegramSubscribers,
  sendTelegramDailyReminder,
  sendTelegramTest,
  updateTelegramSettings,
  type TelegramSettings,
  type TelegramSettingsInput,
  type TelegramSubscriber,
} from "../../api/telegram";
import { ApiError } from "../../api/client";
import { Button, EmptyState, FormSection, FormStickyActions, NumberStepper, Switch, TimezoneSelect } from "../../components/ui";
import { formatInstantInTimeZone } from "../../lib/datetime";
// planning window is now a 1–7 day stepper
import { useAuth } from "../auth/AuthContext";
import { SettingsPageShell } from "./SettingsPageShell";

function timeInputValue(value: string): string {
  return value.slice(0, 5);
}

export function TelegramSettingsPage() {
  const { accessToken, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [settings, setSettings] = useState<TelegramSettings | null>(null);
  const [subscribers, setSubscribers] = useState<TelegramSubscriber[]>([]);
  const [form, setForm] = useState<TelegramSettingsInput>({
    enabled: false,
    daily_reminder_time: "08:00",
    shopping_window_days: 3,
    include_today: true,
    include_pantry_items: false,
    group_by_category: true,
    timezone: "Europe/Paris",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [actionBusy, setActionBusy] = useState<"test" | "send" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [refreshWarning, setRefreshWarning] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) {
      navigate("/review");
    }
  }, [isAdmin, navigate]);

  const reload = async () => {
    if (!accessToken) {
      return;
    }
    const [settingsData, subscribersData] = await Promise.all([
      fetchTelegramSettings(accessToken),
      fetchTelegramSubscribers(accessToken),
    ]);
    setSettings(settingsData);
    setSubscribers(subscribersData);
    setForm({
      enabled: settingsData.enabled,
      daily_reminder_time: timeInputValue(settingsData.daily_reminder_time),
      shopping_window_days: settingsData.shopping_window_days,
      include_today: settingsData.include_today,
      include_pantry_items: settingsData.include_pantry_items,
      group_by_category: settingsData.group_by_category,
      timezone: settingsData.timezone,
    });
  };

  const reloadSilently = async () => {
    try {
      await reload();
      setRefreshWarning(null);
    } catch (err) {
      setRefreshWarning(err instanceof ApiError ? err.message : "Failed to refresh settings");
    }
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
          setError(err instanceof ApiError ? err.message : "Failed to load Telegram settings");
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
    setRefreshWarning(null);
    try {
      await updateTelegramSettings(accessToken, form);
      setNotice("Settings saved.");
      await reloadSilently();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const runAction = async (action: "test" | "send") => {
    if (!accessToken || actionBusy) {
      return;
    }
    setActionBusy(action);
    setError(null);
    setNotice(null);
    setRefreshWarning(null);
    try {
      const result =
        action === "test" ? await sendTelegramTest(accessToken) : await sendTelegramDailyReminder(accessToken);
      setNotice(result.detail);
      await reloadSilently();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Telegram action failed");
      await reloadSilently();
    } finally {
      setActionBusy(null);
    }
  };

  if (loading) {
    return (
      <SettingsPageShell title="Telegram" subtitle="Reminders and bot commands." loading>
        {null}
      </SettingsPageShell>
    );
  }

  return (
    <SettingsPageShell title="Telegram" subtitle="Daily reminders and on-demand bot commands.">
      <p className="muted admin-notice">
        Set <code>TELEGRAM_BOT_TOKEN</code> in <code>.env</code>, restart Docker, then message your bot with{" "}
        <strong>/subscribe</strong> in Telegram. Use <strong>/unsubscribe</strong> to stop.
      </p>

      {settings?.has_bot_token ? (
        <p className="muted admin-notice">Bot token detected from environment.</p>
      ) : (
        <p className="error">TELEGRAM_BOT_TOKEN is not set in the API/worker environment.</p>
      )}

      {settings?.last_sent_at ? (
        <p className="muted admin-notice">
          Last sent ({settings.timezone}): {formatInstantInTimeZone(settings.last_sent_at, settings.timezone)}
        </p>
      ) : null}
      {settings?.last_error ? <p className="error">Last error: {settings.last_error}</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="muted admin-notice">{notice}</p> : null}
      {refreshWarning ? <p className="muted">Saved, but refresh failed: {refreshWarning}</p> : null}

      <FormSection title={`Subscribers (${subscribers.length})`}>
        {subscribers.length === 0 ? (
          <EmptyState
            title="No subscribers yet"
            description="Send /subscribe to the bot in Telegram."
          />
        ) : (
          <ul className="admin-subscriber-list">
            {subscribers.map((subscriber) => (
              <li key={subscriber.id} className="admin-subscriber-item">
                {subscriber.display_name ?? subscriber.username ?? subscriber.chat_id}
                {subscriber.username ? <span className="muted"> @{subscriber.username}</span> : null}
                <span className="muted"> · chat {subscriber.chat_id}</span>
              </li>
            ))}
          </ul>
        )}
      </FormSection>

      <form onSubmit={(event) => void handleSubmit(event)} className="admin-form">
        <FormSection title="Daily reminders" description="Send a daily shopping reminder through the household bot.">
          <div className="settings-section-header-trailing-only">
            <Switch
              checked={form.enabled ?? false}
              onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
              label="Enable daily reminders"
            />
          </div>

          <div className="grid-2">
            <label>
              Daily reminder time
              <input
                type="time"
                value={form.daily_reminder_time ?? "08:00"}
                onChange={(event) => setForm({ ...form, daily_reminder_time: event.target.value })}
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

          <NumberStepper
            ariaLabel="Planning days included"
            label="Planning days included"
            min={1}
            max={7}
            value={form.shopping_window_days ?? 3}
            onChange={(shopping_window_days) => setForm({ ...form, shopping_window_days })}
          />
          <p className="muted admin-field-hint">
            Includes today and the following {Math.max(0, (form.shopping_window_days ?? 3) - 1)} day
            {(form.shopping_window_days ?? 3) - 1 === 1 ? "" : "s"}.
          </p>

          <Switch
            checked={Boolean(form.group_by_category)}
            onChange={(event) => setForm({ ...form, group_by_category: event.target.checked })}
            label="Group ingredients by category when sending a saved shopping list via API"
          />
        </FormSection>

        <FormStickyActions>
          <Button type="submit" loading={saving} disabled={actionBusy !== null}>
            Save settings
          </Button>
          <Button
            type="button"
            variant="secondary"
            loading={actionBusy === "test"}
            disabled={saving || actionBusy === "send"}
            onClick={() => void runAction("test")}
          >
            Send test
          </Button>
          <Button
            type="button"
            variant="secondary"
            loading={actionBusy === "send"}
            disabled={saving || actionBusy === "test"}
            onClick={() => void runAction("send")}
          >
            Send reminder now
          </Button>
        </FormStickyActions>
      </form>
    </SettingsPageShell>
  );
}
