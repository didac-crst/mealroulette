import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import * as authApi from "../../api/auth";
import { ApiError } from "../../api/client";
import { BrandLogo } from "../../components/BrandLogo";
import { Button } from "../../components/ui";
import { saveTokens } from "./authStorage";
import { useAuth } from "./AuthContext";

export function SignupPage() {
  const { user, loading } = useAuth();
  const [householdName, setHouseholdName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    return <Navigate to="/today" replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const tokens = await authApi.register({
        username,
        email,
        password,
        household_name: householdName.trim() || "My household",
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
        <h1>Create your household</h1>
        <p className="login-welcome muted">Start with a household account.</p>
        <form onSubmit={handleSubmit} className="stack">
          <label>
            Household name
            <input
              type="text"
              autoComplete="organization"
              value={householdName}
              onChange={(event) => setHouseholdName(event.target.value)}
              required
              maxLength={128}
            />
          </label>
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
          <Button type="submit" size="lg" loading={submitting} disabled={loading} className="login-submit">
            Create household
          </Button>
        </form>
        <p className="muted">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
