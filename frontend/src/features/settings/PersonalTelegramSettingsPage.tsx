import { FormEvent, useCallback, useEffect, useState } from "react";
import QRCode from "qrcode";

import * as householdApi from "../../api/household";
import type { NotificationSubscription, TelegramLinkStatus, TelegramLinkToken } from "../../api/household";
import { ApiError } from "../../api/client";
import {
  Button,
  FormStickyActions,
  NumberStepper,
  PageLoadingState,
  Switch,
  TechnicalValue,
  TimezoneSelect,
} from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { SettingsPageShell } from "./SettingsPageShell";

function timeInputValue(value: string): string {
  return value.slice(0, 5);
}

export function PersonalTelegramSettingsPage() {
  const { accessToken, hasHousehold } = useAuth();
  const [link, setLink] = useState<TelegramLinkStatus | null>(null);
  const [invite, setInvite] = useState<TelegramLinkToken | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<NotificationSubscription | null>(null);
  const [reminderTime, setReminderTime] = useState("08:00");
  const [timezone, setTimezone] = useState("Europe/Paris");
  const [shoppingWindowDays, setShoppingWindowDays] = useState(3);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionBusy, setActionBusy] = useState<"test" | "send" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [autoInviteAttempted, setAutoInviteAttempted] = useState(false);

  const loadAll = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const status = await householdApi.fetchTelegramLink(accessToken);
      setLink(status);
      if (status.linked) {
        setInvite(null);
        setQrDataUrl(null);
      }

      if (hasHousehold) {
        const sub = await householdApi.fetchNotificationSubscription(accessToken);
        setSubscription(sub);
        setReminderTime(timeInputValue(String(sub.daily_reminder_time)));
        setTimezone(sub.timezone);
        setShoppingWindowDays(sub.shopping_window_days);
      } else {
        setSubscription(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load Telegram settings.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, hasHousehold]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  useEffect(() => {
    if (
      !accessToken ||
      loading ||
      link === null ||
      link.linked ||
      invite !== null ||
      busy ||
      autoInviteAttempted
    ) {
      return;
    }
    setAutoInviteAttempted(true);
    void handleCreateLink();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, loading, link, invite, busy, autoInviteAttempted]);

  useEffect(() => {
    if (!invite?.deep_link_url) {
      setQrDataUrl(null);
      return;
    }
    let cancelled = false;
    void QRCode.toDataURL(invite.deep_link_url, {
      width: 240,
      margin: 2,
      errorCorrectionLevel: "M",
    })
      .then((url) => {
        if (!cancelled) {
          setQrDataUrl(url);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setQrDataUrl(null);
          setError("Could not generate QR code. Use the deep link below instead.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [invite?.deep_link_url]);

  async function handleCreateLink() {
    if (!accessToken) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const token = await householdApi.createTelegramLinkToken(accessToken);
      setInvite(token);
      if (!token.deep_link_url) {
        setError("Telegram bot username is not configured. Ask a platform admin to set TELEGRAM_BOT_USERNAME.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create link QR.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUnlink() {
    if (!accessToken) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await householdApi.unlinkTelegram(accessToken);
      setLink({ linked: false });
      setInvite(null);
      setQrDataUrl(null);
      setAutoInviteAttempted(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not unlink Telegram.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubscriptionToggle(patch: Partial<NotificationSubscription>) {
    if (!accessToken || !subscription) {
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const next = await householdApi.updateNotificationSubscription(accessToken, patch);
      setSubscription(next);
      setNotice("Notification preferences saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update preferences.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveSchedule(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const next = await householdApi.updateNotificationSubscription(accessToken, {
        daily_reminder_time: reminderTime,
        timezone,
        shopping_window_days: shoppingWindowDays,
      });
      setSubscription(next);
      setReminderTime(timeInputValue(String(next.daily_reminder_time)));
      setTimezone(next.timezone);
      setShoppingWindowDays(next.shopping_window_days);
      setNotice("Reminder schedule saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save reminder schedule.");
    } finally {
      setSaving(false);
    }
  }

  async function handleAction(kind: "test" | "send") {
    if (!accessToken) {
      return;
    }
    setActionBusy(kind);
    setError(null);
    setNotice(null);
    try {
      const result =
        kind === "test"
          ? await householdApi.sendPersonalTelegramTest(accessToken)
          : await householdApi.sendPersonalDailyReminder(accessToken);
      setNotice(result.detail);
      await loadAll();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send Telegram message.");
    } finally {
      setActionBusy(null);
    }
  }

  if (loading && !link) {
    return (
      <div className="admin-page">
        <PageLoadingState message="Loading Telegram…" />
      </div>
    );
  }

  const linked = link?.linked === true;

  return (
    <SettingsPageShell title="Telegram" subtitle="Link your account and choose which notifications you receive.">
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="success">{notice}</p> : null}

      {linked ? (
        <section className="settings-section stack">
          <h2 className="settings-group-title">Account link</h2>
          <p>
            Linked as <strong>{link?.display_name || link?.username || "Telegram user"}</strong>
            {link?.username ? <span className="muted"> (@{link.username})</span> : null}.
          </p>
          {link?.linked_at ? (
            <p className="muted">Linked {new Date(link.linked_at).toLocaleString()}</p>
          ) : null}
          <Button type="button" variant="ghost" disabled={busy} onClick={() => void handleUnlink()}>
            Unlink Telegram
          </Button>
        </section>
      ) : (
        <section className="settings-section stack">
          <h2 className="settings-group-title">Account link</h2>
          <p className="muted">
            Scan the QR code (or open the link) in Telegram and tap Start. Reminders and cooking timers only reach your
            linked account.
          </p>
          {!invite ? (
            <Button type="button" disabled={busy} loading={busy} onClick={() => void handleCreateLink()}>
              {busy ? "Preparing QR…" : "Show link QR code"}
            </Button>
          ) : (
            <div className="telegram-link-qr stack">
              {qrDataUrl ? (
                <img
                  className="telegram-link-qr-image"
                  src={qrDataUrl}
                  alt="QR code to link Telegram"
                  width={240}
                  height={240}
                />
              ) : (
                <p className="muted">Generating QR…</p>
              )}
              {invite.deep_link_url ? (
                <TechnicalValue label="Or open this link" value={invite.deep_link_url} copyLabel="Copy link" />
              ) : null}
              <p className="muted">Expires {new Date(invite.expires_at).toLocaleString()}.</p>
              <div className="cluster">
                <Button type="button" disabled={busy || loading} onClick={() => void loadAll()}>
                  I’ve linked — refresh
                </Button>
                <Button type="button" variant="ghost" disabled={busy} onClick={() => void handleCreateLink()}>
                  New QR code
                </Button>
              </div>
            </div>
          )}
        </section>
      )}

      {hasHousehold && subscription ? (
        <section className="settings-section">
          <form className="stack" onSubmit={(event) => void handleSaveSchedule(event)}>
            <h2 className="settings-group-title">Your notifications</h2>
            <p className="muted">These apply to your linked Telegram account.</p>

            <Switch
              label="Daily reminder"
              checked={subscription.notify_daily_reminder}
              disabled={busy || !linked}
              onChange={(event) =>
                void handleSubscriptionToggle({ notify_daily_reminder: event.target.checked })
              }
            />
            <Switch
              label="Shopping updates"
              checked={subscription.notify_shopping}
              disabled={busy || !linked}
              onChange={(event) => void handleSubscriptionToggle({ notify_shopping: event.target.checked })}
            />
            <Switch
              label="New roulette"
              checked={subscription.notify_roulette}
              disabled={busy || !linked}
              onChange={(event) => void handleSubscriptionToggle({ notify_roulette: event.target.checked })}
            />

            <label>
              Reminder time
              <input
                type="time"
                value={reminderTime}
                onChange={(event) => setReminderTime(event.target.value)}
                disabled={!linked}
              />
            </label>
            <TimezoneSelect value={timezone} onChange={setTimezone} disabled={!linked} />
            <NumberStepper
              label="Shopping window (days)"
              ariaLabel="Shopping window days"
              value={shoppingWindowDays}
              min={1}
              max={14}
              onChange={setShoppingWindowDays}
              disabled={!linked}
            />

            {subscription.last_reminder_sent_at ? (
              <p className="muted">
                Last reminder sent {new Date(subscription.last_reminder_sent_at).toLocaleString()}
              </p>
            ) : null}

            {!linked ? <p className="muted">Link Telegram above to receive these notifications.</p> : null}

            <div className="cluster">
              <Button
                type="button"
                variant="ghost"
                disabled={!linked || actionBusy !== null || saving}
                loading={actionBusy === "test"}
                onClick={() => void handleAction("test")}
              >
                Send test
              </Button>
              <Button
                type="button"
                variant="ghost"
                disabled={!linked || actionBusy !== null || saving}
                loading={actionBusy === "send"}
                onClick={() => void handleAction("send")}
              >
                Send reminder now
              </Button>
            </div>

            <FormStickyActions>
              <Button type="submit" loading={saving} disabled={!linked}>
                Save schedule
              </Button>
            </FormStickyActions>
          </form>
        </section>
      ) : null}
    </SettingsPageShell>
  );
}
