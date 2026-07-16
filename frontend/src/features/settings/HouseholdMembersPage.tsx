import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import * as householdApi from "../../api/household";
import type { HouseholdInvitation, HouseholdMember, HouseholdRole } from "../../api/household";
import { ApiError } from "../../api/client";
import { Button, PageLoadingState, PageShell, SettingsSectionHeader } from "../../components/ui";
import { copyTextToClipboard } from "../../lib/copyTextToClipboard";
import { useAuth } from "../auth/AuthContext";

const INVITE_URL_STORAGE_KEY = "mealroulette.householdInviteUrls";

function readStoredInviteUrls(): Record<string, string> {
  try {
    const raw = sessionStorage.getItem(INVITE_URL_STORAGE_KEY);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, string>;
    }
  } catch {
    // Ignore corrupt session storage.
  }
  return {};
}

function writeStoredInviteUrls(urls: Record<string, string>) {
  sessionStorage.setItem(INVITE_URL_STORAGE_KEY, JSON.stringify(urls));
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function isInvitationExpired(invitation: HouseholdInvitation): boolean {
  return new Date(invitation.expires_at).getTime() < Date.now();
}

function InviteLinkCell({ url }: { url: string | null }) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  if (!url) {
    return (
      <span className="muted household-invite-link-unavailable" title="Invite links are shown once when created">
        Link unavailable
      </span>
    );
  }

  const inviteUrl = url;

  async function handleCopy() {
    const copied = await copyTextToClipboard(inviteUrl);
    setCopyState(copied ? "copied" : "failed");
    window.setTimeout(() => setCopyState("idle"), copied ? 1200 : 1800);
  }

  const label = copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy link";

  return (
    <div className="household-invite-link" role="group" aria-label="Invitation link">
      <code className="household-invite-link-code" title={url}>
        {inviteUrl}
      </code>
      <button
        type="button"
        className={`technical-value-copy${copyState === "failed" ? " technical-value-copy-failed" : ""}`}
        onClick={() => void handleCopy()}
        aria-label="Copy invitation link"
      >
        {label}
      </button>
    </div>
  );
}

export function HouseholdMembersPage() {
  const { accessToken, user, isHouseholdAdmin, loading: authLoading, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [members, setMembers] = useState<HouseholdMember[]>([]);
  const [invitations, setInvitations] = useState<HouseholdInvitation[]>([]);
  const [inviteUrls, setInviteUrls] = useState<Record<string, string>>(() => readStoredInviteUrls());
  const [householdName, setHouseholdName] = useState("");
  const [householdNameDraft, setHouseholdNameDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [savingName, setSavingName] = useState(false);
  const [busyMembershipId, setBusyMembershipId] = useState<string | null>(null);
  const [busyInvitationId, setBusyInvitationId] = useState<string | null>(null);

  const currentUserId = user?.id ?? null;

  const sortedMembers = useMemo(() => {
    return [...members].sort((a, b) => {
      if (currentUserId && a.user_id === currentUserId) {
        return -1;
      }
      if (currentUserId && b.user_id === currentUserId) {
        return 1;
      }
      return a.username.localeCompare(b.username);
    });
  }, [members, currentUserId]);

  const load = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [memberRows, invitationRows, household] = await Promise.all([
        householdApi.listHouseholdMembers(accessToken),
        householdApi.listHouseholdInvitations(accessToken),
        householdApi.fetchHousehold(accessToken),
      ]);
      setMembers(memberRows);
      setInvitations(invitationRows);
      setHouseholdName(household.name);
      setHouseholdNameDraft(household.name);
      setInviteUrls((prev) => {
        const activeIds = new Set(invitationRows.map((row) => row.id));
        const next = Object.fromEntries(Object.entries(prev).filter(([id]) => activeIds.has(id)));
        writeStoredInviteUrls(next);
        return next;
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load household members.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    if (!authLoading && !isHouseholdAdmin) {
      navigate("/today");
    }
  }, [authLoading, isHouseholdAdmin, navigate]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleRenameHousehold(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    const nextName = householdNameDraft.trim();
    if (!nextName || nextName === householdName) {
      return;
    }
    setSavingName(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await householdApi.updateHousehold(accessToken, nextName);
      setHouseholdName(updated.name);
      setHouseholdNameDraft(updated.name);
      await refreshUser();
      setNotice("Household name updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not rename household.");
    } finally {
      setSavingName(false);
    }
  }

  async function handleCreateInvitation() {
    if (!accessToken) {
      return;
    }
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const created = await householdApi.createHouseholdInvitation(accessToken);
      const absoluteUrl = `${window.location.origin}${created.invite_url}`;
      setInviteUrls((prev) => {
        const next = { ...prev, [created.invitation.id]: absoluteUrl };
        writeStoredInviteUrls(next);
        return next;
      });
      await load();
      await copyTextToClipboard(absoluteUrl);
      setNotice("Invitation link created.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create invitation.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(invitationId: string) {
    if (!accessToken) {
      return;
    }
    setBusyInvitationId(invitationId);
    setError(null);
    setNotice(null);
    try {
      await householdApi.revokeHouseholdInvitation(accessToken, invitationId);
      setInviteUrls((prev) => {
        const next = { ...prev };
        delete next[invitationId];
        writeStoredInviteUrls(next);
        return next;
      });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not revoke invitation.");
    } finally {
      setBusyInvitationId(null);
    }
  }

  async function handleRoleChange(membershipId: string, role: HouseholdRole) {
    if (!accessToken) {
      return;
    }
    setBusyMembershipId(membershipId);
    setError(null);
    setNotice(null);
    try {
      await householdApi.updateMemberRole(accessToken, membershipId, role);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update member role.");
    } finally {
      setBusyMembershipId(null);
    }
  }

  async function handleRemove(membershipId: string) {
    if (!accessToken) {
      return;
    }
    setBusyMembershipId(membershipId);
    setError(null);
    setNotice(null);
    try {
      await householdApi.removeHouseholdMember(accessToken, membershipId);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not remove member.");
    } finally {
      setBusyMembershipId(null);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="admin-page">
        <PageLoadingState message="Loading members..." />
      </div>
    );
  }

  if (!isHouseholdAdmin) {
    return null;
  }

  return (
    <div className="admin-page">
      <PageShell title="Household settings" subtitle="Name, invites, and member roles.">
        {error ? <p className="form-error">{error}</p> : null}
        {notice ? <p className="success">{notice}</p> : null}

        <section className="settings-section">
          <SettingsSectionHeader title="Household" description="Name shown in the app for everyone in this household." />
          <form className="stack settings-form" onSubmit={(event) => void handleRenameHousehold(event)}>
            <label>
              Name
              <input
                type="text"
                value={householdNameDraft}
                onChange={(event) => setHouseholdNameDraft(event.target.value)}
                required
                maxLength={128}
                disabled={savingName || busy}
              />
            </label>
            <Button
              type="submit"
              disabled={savingName || busy || householdNameDraft.trim() === householdName || !householdNameDraft.trim()}
              loading={savingName}
            >
              Save name
            </Button>
          </form>
        </section>

        <section className="settings-section">
          <SettingsSectionHeader title="Members" description="Active people in this household." />
          <div className="household-admin-table" role="table" aria-label="Household members">
            <div className="household-admin-table-header household-members-grid" role="row">
              <span role="columnheader">User</span>
              <span role="columnheader">Email</span>
              <span role="columnheader">Role</span>
              <span role="columnheader">Actions</span>
            </div>
            {sortedMembers.map((member) => {
              const isSelf = currentUserId !== null && member.user_id === currentUserId;
              const rowBusy = busyMembershipId === member.membership_id;
              return (
                <div
                  key={member.membership_id}
                  className={`household-admin-table-row household-members-grid${isSelf ? " household-admin-table-row-self" : ""}`}
                  role="row"
                >
                  <div role="cell">
                    <span className="admin-mobile-label">User</span>
                    <strong>{member.username}</strong>
                    {isSelf ? <span className="muted"> · you</span> : null}
                  </div>
                  <div role="cell">
                    <span className="admin-mobile-label">Email</span>
                    <span className="household-admin-table-secondary">{member.email}</span>
                  </div>
                  <div role="cell">
                    <span className="admin-mobile-label">Role</span>
                    <select
                      value={member.role}
                      disabled={busy || isSelf || rowBusy}
                      aria-label={`Role for ${member.username}`}
                      onChange={(event) => void handleRoleChange(member.membership_id, event.target.value as HouseholdRole)}
                    >
                      <option value="household_admin">Admin</option>
                      <option value="household_member">Member</option>
                    </select>
                  </div>
                  <div role="cell" className="household-admin-table-actions">
                    <span className="admin-mobile-label">Actions</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      disabled={busy || isSelf || rowBusy}
                      title={isSelf ? "You cannot remove yourself here" : `Remove ${member.username}`}
                      onClick={() => void handleRemove(member.membership_id)}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="settings-section">
          <SettingsSectionHeader
            title="Invitations"
            description="Pending invite links. Copy a link to share it; revoke to invalidate it."
            trailing={
              <Button type="button" disabled={busy} onClick={() => void handleCreateInvitation()}>
                Create invite link
              </Button>
            }
          />
          {invitations.length === 0 ? (
            <p className="muted">No pending invitations.</p>
          ) : (
            <div className="household-admin-table" role="table" aria-label="Pending invitations">
              <div className="household-admin-table-header household-invitations-grid" role="row">
                <span role="columnheader">Created</span>
                <span role="columnheader">Expires</span>
                <span role="columnheader">Invite link</span>
                <span role="columnheader">Actions</span>
              </div>
              {invitations.map((invitation) => {
                const expired = isInvitationExpired(invitation);
                const rowBusy = busyInvitationId === invitation.id;
                return (
                  <div
                    key={invitation.id}
                    className={`household-admin-table-row household-invitations-grid${expired ? " household-admin-table-row-muted" : ""}`}
                    role="row"
                  >
                    <div role="cell">
                      <span className="admin-mobile-label">Created</span>
                      <span>{formatDateTime(invitation.created_at)}</span>
                    </div>
                    <div role="cell">
                      <span className="admin-mobile-label">Expires</span>
                      <span>
                        {formatDateTime(invitation.expires_at)}
                        {expired ? <span className="muted"> · expired</span> : null}
                      </span>
                    </div>
                    <div role="cell">
                      <span className="admin-mobile-label">Invite link</span>
                      <InviteLinkCell url={inviteUrls[invitation.id] ?? null} />
                    </div>
                    <div role="cell" className="household-admin-table-actions">
                      <span className="admin-mobile-label">Actions</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={busy || rowBusy}
                        onClick={() => void handleRevoke(invitation.id)}
                      >
                        Revoke
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </PageShell>
    </div>
  );
}
