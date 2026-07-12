import { useEffect, useState } from "react";

import { fetchSchedulerSettings } from "../../api/scheduler";
import { useAuth } from "../auth/AuthContext";
import { formatNowInTimeZone } from "../../lib/datetime";

const DEFAULT_TIMEZONE = "Europe/Paris";
const TICK_MS = 30_000;

export function HouseholdClock() {
  const { accessToken } = useAuth();
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), TICK_MS);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    fetchSchedulerSettings(accessToken)
      .then((settings) => {
        if (!cancelled) {
          setTimezone(settings.timezone);
        }
      })
      .catch(() => {
        // Keep default timezone when settings cannot be loaded.
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  return (
    <p className="household-clock muted" aria-live="polite">
      <span className="household-clock-label">Household time</span>
      <time className="household-clock-value" dateTime={now.toISOString()}>
        {formatNowInTimeZone(timezone, now)} ({timezone})
      </time>
    </p>
  );
}
