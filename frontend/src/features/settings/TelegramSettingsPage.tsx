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
import { ButtonLink } from "../../components/ButtonLink";
import { useAuth } from "../auth/AuthContext";

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
    try {
      await updateTelegramSettings(accessToken, form);
      await reload();
      setNotice("Settings saved.");
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
    try {
      const result =
        action === "test" ? await sendTelegramTest(accessToken) : await sendTelegramDailyReminder(accessToken);
      setNotice(result.detail);
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Telegram action failed");
      await reload();
    } finally {
      setActionBusy(null);
    }
  };

  if (loading) {
    return (
      <section className="card">
        <p className="muted">Loading Telegram settings…</p>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between">
        <h2>Telegram reminders</h2>
        <ButtonLink to="/review" variant="secondary">
          Back
        </ButtonLink>
      </div>

      <p className="muted">
        Daily reminders and <strong>Send reminder now</strong> send the same HTML message as{" "}
        <code>/reminder</code> in Telegram (meal plan + ingredient breakdown). Pantry items are always
        included; the window is today through the next N−1 days in your timezone.
      </p>

      <p className="muted">
        Set <code>TELEGRAM_BOT_TOKEN</code> in <code>.env</code>, restart Docker, then message your bot with{" "}
        <strong>/subscribe</strong> in Telegram. Use <strong>/unsubscribe</strong> to stop.
      </p>

      {settings?.has_bot_token ? (
        <p className="muted">Bot token detected from environment.</p>
      ) : (
        <p className="error">TELEGRAM_BOT_TOKEN is not set in the API/worker environment.</p>
      )}

      {settings?.last_sent_at ? (
        <p className="muted">Last sent: {new Date(settings.last_sent_at).toLocaleString()}</p>
      ) : null}
      {settings?.last_error ? <p className="error">Last error: {settings.last_error}</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="muted">{notice}</p> : null}

      <fieldset>
        <legend>Subscribers ({subscribers.length})</legend>
        {subscribers.length === 0 ? (
          <p className="muted">No subscribers yet. Send /subscribe to the bot in Telegram.</p>
        ) : (
          <ul className="bulleted-list">
            {subscribers.map((subscriber) => (
              <li key={subscriber.id}>
                {subscriber.display_name ?? subscriber.username ?? subscriber.chat_id}
                {subscriber.username ? <span className="muted"> @{subscriber.username}</span> : null}
                <span className="muted"> · chat {subscriber.chat_id}</span>
              </li>
            ))}
          </ul>
        )}
      </fieldset>

      <form onSubmit={(event) => void handleSubmit(event)} className="stack">
        <label className="checkbox-pill">
          <input
            type="checkbox"
            checked={form.enabled ?? false}
            onChange={(event) => setForm({ ...form, enabled: event.target.checked })}
          />
          Enable daily reminders
        </label>

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
            <input
              value={form.timezone ?? "Europe/Paris"}
              onChange={(event) => setForm({ ...form, timezone: event.target.value })}
            />
          </label>
        </div>

        <label>
          Reminder window (days)
          <input
            type="number"
            min={1}
            max={14}
            value={form.shopping_window_days ?? 3}
            onChange={(event) => setForm({ ...form, shopping_window_days: Number(event.target.value) })}
          />
          <span className="muted">Same as </span>
          <code>/reminder {form.shopping_window_days ?? 3}</code>
        </label>

        <label className="checkbox-pill">
          <input
            type="checkbox"
            checked={Boolean(form.group_by_category)}
            onChange={(event) => setForm({ ...form, group_by_category: event.target.checked })}
          />
          Group ingredients by category when sending a saved shopping list via API
        </label>

        <div className="row-between">
          <button type="submit" className="button" disabled={saving}>
            {saving ? "Saving…" : "Save settings"}
          </button>
          <div className="row-actions">
            <button
              type="button"
              className="button button-secondary"
              disabled={actionBusy !== null}
              onClick={() => void runAction("test")}
            >
              {actionBusy === "test" ? "Sending…" : "Send test"}
            </button>
            <button
              type="button"
              className="button button-secondary"
              disabled={actionBusy !== null}
              onClick={() => void runAction("send")}
            >
              {actionBusy === "send" ? "Sending…" : "Send reminder now"}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
