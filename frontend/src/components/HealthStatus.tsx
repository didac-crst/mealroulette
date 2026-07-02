import { useEffect, useState } from "react";

import { fetchHealth } from "../api/client";

export function HealthStatus() {
  const [status, setStatus] = useState<string>("checking...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((payload) => {
        if (!cancelled) {
          setStatus(payload.status);
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setStatus("unavailable");
          setError(err.message);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section aria-label="API health status">
      <h2>API Health</h2>
      <p data-testid="health-status">Status: {status}</p>
      {error ? <p role="alert">{error}</p> : null}
    </section>
  );
}
