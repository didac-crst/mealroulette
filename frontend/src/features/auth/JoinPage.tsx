import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import * as authApi from "../../api/auth";
import * as householdApi from "../../api/household";
import { ApiError } from "../../api/client";
import { BrandLogo } from "../../components/BrandLogo";
import { Button } from "../../components/ui";
import { saveTokens } from "./authStorage";
import { useAuth } from "./AuthContext";

export function JoinPage() {
  const [searchParams] = useSearchParams();
  const inviteToken = searchParams.get("token")?.trim() ?? "";
  const { user, accessToken, loading } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!inviteToken) {
    return (
      <main className="login-page">
        <section className="card login-card">
          <h1>Invalid invitation</h1>
          <p className="muted">This invite link is missing a token. Ask your household admin for a new link.</p>
          <p>
            <Link to="/login">Sign in</Link>
          </p>
        </section>
      </main>
    );
  }

  if (!loading && user && accessToken) {
    return (
      <main className="login-page">
        <section className="card login-card">
          <BrandLogo variant="login" />
          <h1>Join household</h1>
          <p className="muted">
            Signed in as <strong>{user.username}</strong>. Accept this invitation to join the household.
          </p>
          {error ? (
            <p className="error" role="alert">
              {error}
            </p>
          ) : null}
          <Button
            type="button"
            size="lg"
            loading={submitting}
            onClick={() => {
              setSubmitting(true);
              setError(null);
              void householdApi
                .acceptHouseholdInvitation(inviteToken, accessToken)
                .then(() => {
                  window.location.assign("/today");
                })
                .catch((err) => {
                  setError(err instanceof ApiError ? err.message : "Could not accept invitation.");
                })
                .finally(() => setSubmitting(false));
            }}
          >
            Accept invitation
          </Button>
        </section>
      </main>
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const tokens = await authApi.registerWithInvitation({
        token: inviteToken,
        username,
        email,
        password,
      });
      saveTokens({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });
      window.location.assign("/today");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="card login-card">
        <BrandLogo variant="login" />
        <h1>Join MealRoulette</h1>
        <p className="muted">Create your account to accept this household invitation.</p>
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
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="new-password"
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
          <Button type="submit" size="lg" loading={submitting} disabled={loading}>
            Create account and join
          </Button>
        </form>
        <p className="muted">
          Already have an account? <Link to={`/login?next=${encodeURIComponent(`/join?token=${inviteToken}`)}`}>Sign in</Link>
        </p>
      </section>
    </main>
  );
}
