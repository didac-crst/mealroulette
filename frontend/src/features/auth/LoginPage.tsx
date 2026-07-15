import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import * as authApi from "../../api/auth";
import { ApiError } from "../../api/client";
import { BrandLogo } from "../../components/BrandLogo";
import { Button } from "../../components/ui";
import { HomeRedirect } from "../../routes/HomeRedirect";
import { useAuth } from "./AuthContext";

type LoginMode = "password" | "telegram";

export function LoginPage() {
  const { login, loginWithTelegramOtp, user, loading } = useAuth();
  const [mode, setMode] = useState<LoginMode>("password");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    return <HomeRedirect />;
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRequestOtp(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      const result = await authApi.requestTelegramOtp(username);
      setOtpSent(true);
      setNotice(result.detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not request a login code.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyOtp(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      await loginWithTelegramOtp(username, otpCode);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Invalid code");
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(next: LoginMode) {
    setMode(next);
    setError(null);
    setNotice(null);
    setOtpSent(false);
    setOtpCode("");
    setPassword("");
  }

  return (
    <main className="login-page">
      <section className="card login-card">
        <BrandLogo variant="login" />
        <h1>MealRoulette</h1>
        <p className="login-welcome muted">Welcome back</p>
        <p className="login-tagline">Plan less. Eat better.</p>

        {mode === "password" ? (
          <>
            <form onSubmit={(event) => void handlePasswordSubmit(event)} className="stack">
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

            <p className="login-or muted" role="separator">
              or
            </p>

            <Button type="button" variant="secondary" size="lg" className="login-submit" onClick={() => switchMode("telegram")}>
              One Time Password
            </Button>
          </>
        ) : (
          <>
            <form
              onSubmit={(event) => void (otpSent ? handleVerifyOtp(event) : handleRequestOtp(event))}
              className="stack"
            >
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
              {otpSent ? (
                <label>
                  Code from Telegram
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    value={otpCode}
                    onChange={(event) => setOtpCode(event.target.value)}
                    required
                    minLength={6}
                    maxLength={8}
                  />
                </label>
              ) : (
                <p className="muted">We’ll send a one-time code to your linked Telegram account.</p>
              )}
              {notice ? <p className="success">{notice}</p> : null}
              {error ? (
                <p className="error" role="alert">
                  {error}
                </p>
              ) : null}
              <Button type="submit" size="lg" loading={submitting} disabled={loading} className="login-submit">
                {otpSent ? (submitting ? "Signing in…" : "Sign in with code") : submitting ? "Sending…" : "Send code"}
              </Button>
              {otpSent ? (
                <Button
                  type="button"
                  variant="ghost"
                  disabled={submitting}
                  onClick={() => {
                    setOtpSent(false);
                    setOtpCode("");
                    setNotice(null);
                    setError(null);
                  }}
                >
                  Use a different username
                </Button>
              ) : null}
            </form>

            <p className="login-or muted" role="separator">
              or
            </p>

            <Button type="button" variant="secondary" size="lg" className="login-submit" onClick={() => switchMode("password")}>
              Password
            </Button>
          </>
        )}

        <p className="login-footer muted">
          New here? <Link to="/signup">Create a household</Link>
        </p>
      </section>
    </main>
  );
}
