import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { BrandLogo } from "../../components/BrandLogo";
import { Button } from "../../components/ui";
import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { login, user, loading } = useAuth();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    const stateRedirect = (location.state as { from?: { pathname: string } } | null)?.from?.pathname;
    const redirect = searchParams.get("next") ?? stateRedirect ?? "/today";
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
    <main className="login-page">
      <section className="card login-card">
        <BrandLogo variant="login" />
        <h1>MealRoulette</h1>
        <p className="login-welcome muted">Welcome back</p>
        <p className="login-tagline">Plan less. Eat better.</p>
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
        <Button type="submit" size="lg" loading={submitting} disabled={loading} className="login-submit">
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
        </form>
        <p className="muted">
          New household? <Link to="/signup">Create one</Link>
        </p>
      </section>
    </main>
  );
}
