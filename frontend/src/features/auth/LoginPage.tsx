import { FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { ApiError } from "../../api/client";
import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { login, user, loading } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    const redirect = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/review";
    return <Navigate to={redirect} replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="card login-card">
        <picture className="login-logo">
          <source srcSet="/logo-header.webp" type="image/webp" />
          <img src="/logo-header.png" alt="" width={72} height={72} />
        </picture>
        <h1>MealRoulette</h1>
        <p className="muted">Sign in to manage your household meal library.</p>
        <form onSubmit={handleSubmit} className="stack">
          <label>
            Username
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={8}
            />
          </label>
          {error ? (
            <p className="error" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" disabled={submitting || loading}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
