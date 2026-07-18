import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import * as proposalsApi from "../../api/ingredientProposals";
import type { IngredientProposal, IngredientProposalMatch } from "../../api/ingredientProposals";
import { Button, EmptyState, PageShell, SegmentedControl, StatusBadge } from "../../components/ui";
import type { StatusBadgeVariant } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

type ProposalTab = "propose" | "mine";

function statusVariant(status: IngredientProposal["resolution_status"]): StatusBadgeVariant {
  switch (status) {
    case "approved":
      return "success";
    case "rejected":
    case "withdrawn":
      return "danger";
    case "needs_information":
      return "warning";
    case "duplicate":
      return "info";
    default:
      return "default";
  }
}

function formatStatus(status: string): string {
  return status.replace(/_/g, " ");
}

function formatMatchKind(kind: string): string {
  switch (kind) {
    case "ingredient":
      return "Ingredient";
    case "alias":
      return "Alias";
    case "pending_proposal":
      return "Pending proposal";
    default:
      return formatStatus(kind);
  }
}

function hasExistingCatalogMatch(matches: IngredientProposalMatch[]): boolean {
  return matches.some((match) => match.kind === "ingredient" || match.kind === "alias");
}

export function MyIngredientProposalsPage() {
  const { accessToken, hasHousehold } = useAuth();
  const [tab, setTab] = useState<ProposalTab>("propose");
  const [proposals, setProposals] = useState<IngredientProposal[]>([]);
  const [proposedName, setProposedName] = useState("");
  const [description, setDescription] = useState("");
  const [culinaryContext, setCulinaryContext] = useState("");
  const [sourceLocale, setSourceLocale] = useState("en");
  const [matches, setMatches] = useState<IngredientProposalMatch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [respondingId, setRespondingId] = useState<string | null>(null);
  const [responseDescription, setResponseDescription] = useState("");
  const [responseContext, setResponseContext] = useState("");
  const [responseNote, setResponseNote] = useState("");
  const [responding, setResponding] = useState(false);

  const loadProposals = useCallback(async () => {
    if (!accessToken || !hasHousehold) {
      setLoading(false);
      return;
    }
    try {
      const data = await proposalsApi.listMyIngredientProposals(accessToken);
      setProposals(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load proposals");
    } finally {
      setLoading(false);
    }
  }, [accessToken, hasHousehold]);

  useEffect(() => {
    void loadProposals();
  }, [loadProposals]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!accessToken || !hasHousehold) {
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    setMatches([]);
    try {
      const result = await proposalsApi.createIngredientProposal(accessToken, {
        proposed_name: proposedName,
        source_locale: sourceLocale,
        description: description || undefined,
        culinary_context: culinaryContext || undefined,
      });
      setProposedName("");
      setDescription("");
      setCulinaryContext("");
      setMatches(result.matches);
      setSuccess("Proposal submitted for platform review.");
      await loadProposals();
      setTab("mine");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit proposal.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleWithdraw(proposalId: string) {
    if (!accessToken) {
      return;
    }
    setError(null);
    try {
      await proposalsApi.withdrawIngredientProposal(accessToken, proposalId);
      setSuccess("Proposal withdrawn.");
      await loadProposals();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not withdraw proposal.");
    }
  }

  function startRespond(proposal: IngredientProposal) {
    setRespondingId(proposal.id);
    setResponseDescription(proposal.description ?? "");
    setResponseContext(proposal.culinary_context ?? "");
    setResponseNote("");
    setError(null);
    setSuccess(null);
  }

  async function handleProvideInformation(event: FormEvent) {
    event.preventDefault();
    if (!accessToken || !respondingId) {
      return;
    }
    setResponding(true);
    setError(null);
    try {
      await proposalsApi.provideIngredientProposalInformation(accessToken, respondingId, {
        description: responseDescription,
        culinary_context: responseContext,
        review_response: responseNote || undefined,
      });
      setRespondingId(null);
      setSuccess("Information sent. Proposal is pending review again.");
      await loadProposals();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send information.");
    } finally {
      setResponding(false);
    }
  }

  if (!hasHousehold) {
    return (
      <div className="admin-page">
        <PageShell
          title="Ingredient proposals"
          subtitle="Propose missing ingredients for the global catalog."
          actions={<Link to="/ingredients">Back to ingredients</Link>}
        >
          <EmptyState
            title="Household required"
            description="Join or create a household to submit ingredient proposals."
          />
        </PageShell>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <PageShell
        title="Ingredient proposals"
        subtitle="Report a missing or ambiguous ingredient without changing the global catalog."
        loading={loading && proposals.length === 0 && tab === "mine"}
        loadingMessage="Loading proposals…"
        actions={<Link to="/ingredients">Back to ingredients</Link>}
      >
        <SegmentedControl
          ariaLabel="Proposal sections"
          value={tab}
          onChange={setTab}
          options={[
            { value: "propose", label: "Propose" },
            { value: "mine", label: "My proposals" },
          ]}
        />

        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="success" role="status">
            {success}
          </p>
        ) : null}

        {tab === "propose" ? (
          <form className="stack settings-form" onSubmit={(event) => void handleSubmit(event)}>
            <label>
              Proposed name
              <input
                value={proposedName}
                onChange={(event) => setProposedName(event.target.value)}
                required
                maxLength={128}
                placeholder="e.g. Torch ginger flower"
              />
            </label>
            <p className="muted">
              Use a normal display name. Platform admins choose the internal catalog identifier.
            </p>
            <label>
              Source locale
              <input
                value={sourceLocale}
                onChange={(event) => setSourceLocale(event.target.value)}
                required
                maxLength={16}
              />
            </label>
            <label>
              Description
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                maxLength={4000}
              />
            </label>
            <label>
              Culinary context
              <textarea
                value={culinaryContext}
                onChange={(event) => setCulinaryContext(event.target.value)}
                rows={3}
                maxLength={4000}
                placeholder="How you use it in recipes"
              />
            </label>
            <Button type="submit" loading={submitting}>
              Submit proposal
            </Button>
          </form>
        ) : null}

        {matches.length > 0 ? (
          <section className="stack" aria-label="Possible matches">
            <h2>Possible matches</h2>
            {hasExistingCatalogMatch(matches) ? (
              <p className="form-error" role="status">
                This may already exist in the catalog. Your proposal was still submitted for review.
              </p>
            ) : null}
            <ul className="stack">
              {matches.map((match) => (
                <li key={`${match.kind}-${match.ingredient_id ?? match.proposal_id ?? match.label}`}>
                  {formatMatchKind(match.kind)}: {match.label}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {tab === "mine" ? (
          <section className="stack" aria-label="My proposals">
            {proposals.length === 0 ? (
              <EmptyState title="No proposals yet" description="Use Propose to submit a missing ingredient." />
            ) : (
              <ul className="stack">
                {proposals.map((proposal) => (
                  <li key={proposal.id} className="stack">
                    <div className="row-actions">
                      <strong>{proposal.proposed_name}</strong>
                      <StatusBadge variant={statusVariant(proposal.resolution_status)}>
                        {formatStatus(proposal.resolution_status)}
                      </StatusBadge>
                    </div>
                    {proposal.review_note ? <p className="muted">{proposal.review_note}</p> : null}
                    {proposal.resolution_status === "needs_information" ? (
                      respondingId === proposal.id ? (
                        <form
                          className="stack settings-form"
                          onSubmit={(event) => void handleProvideInformation(event)}
                        >
                          <h3>Provide information</h3>
                          <label>
                            Description
                            <textarea
                              value={responseDescription}
                              onChange={(event) => setResponseDescription(event.target.value)}
                              rows={3}
                            />
                          </label>
                          <label>
                            Culinary context
                            <textarea
                              value={responseContext}
                              onChange={(event) => setResponseContext(event.target.value)}
                              rows={3}
                            />
                          </label>
                          <label>
                            Response to reviewer
                            <textarea
                              value={responseNote}
                              onChange={(event) => setResponseNote(event.target.value)}
                              rows={3}
                              placeholder="Answer the reviewer's question"
                            />
                          </label>
                          <div className="row-actions">
                            <Button type="submit" loading={responding}>
                              Send information
                            </Button>
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() => setRespondingId(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </form>
                      ) : (
                        <div className="row-actions">
                          <Button type="button" onClick={() => startRespond(proposal)}>
                            Provide information
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={() => void handleWithdraw(proposal.id)}
                          >
                            Withdraw
                          </Button>
                        </div>
                      )
                    ) : null}
                    {proposal.resolution_status === "pending" ? (
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => void handleWithdraw(proposal.id)}
                      >
                        Withdraw
                      </Button>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : null}
      </PageShell>
    </div>
  );
}
