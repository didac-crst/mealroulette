import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchIngredients, fetchUnits, type Ingredient, type Unit } from "../../api/catalog";
import { ApiError } from "../../api/client";
import * as proposalsApi from "../../api/ingredientProposals";
import type { IngredientProposal } from "../../api/ingredientProposals";
import { fetchFoodGroups, fetchFoodGroupFamilies, type FoodGroup, type IngredientFamily } from "../../api/taxonomy";
import { Button, EmptyState, PageShell, SearchSelect, StatusBadge } from "../../components/ui";
import type { StatusBadgeVariant } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

const REVIEW_QUEUE_PATH = "/ingredients/proposal-review";

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

function parseAliases(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((alias) => alias.trim())
    .filter(Boolean);
}

export function IngredientProposalReviewQueuePage() {
  const { accessToken } = useAuth();
  const [proposals, setProposals] = useState<IngredientProposal[]>([]);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    setProposals([]);
    setError(null);
    proposalsApi
      .listPlatformIngredientProposals(accessToken, statusFilter || undefined)
      .then((data) => {
        if (!cancelled) {
          setProposals(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setProposals([]);
          setError(err instanceof ApiError ? err.message : "Failed to load proposals");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, statusFilter]);

  return (
    <div className="admin-page">
      <PageShell
        title="Ingredient proposal review"
        subtitle="Resolve missing-ingredient requests into mappings, aliases, or new catalog entries."
        loading={loading && proposals.length === 0}
        loadingMessage="Loading proposals…"
        actions={<Link to="/ingredients">Back to ingredients</Link>}
      >
        <label>
          Status filter
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="pending">Pending</option>
            <option value="needs_information">Needs information</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="duplicate">Duplicate</option>
            <option value="withdrawn">Withdrawn</option>
            <option value="">All</option>
          </select>
        </label>
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        {proposals.length === 0 && !loading ? (
          <EmptyState title="No proposals" description="Nothing in this review queue." />
        ) : (
          <ul className="stack">
            {proposals.map((proposal) => (
              <li key={proposal.id} className="stack">
                <Link to={`${REVIEW_QUEUE_PATH}/${proposal.id}`}>
                  <strong>{proposal.proposed_name}</strong>
                </Link>
                <StatusBadge variant={statusVariant(proposal.resolution_status)}>
                  {formatStatus(proposal.resolution_status)}
                </StatusBadge>
                <div className="muted">
                  {proposal.source_locale} · {proposal.source_type}
                </div>
              </li>
            ))}
          </ul>
        )}
      </PageShell>
    </div>
  );
}

export function IngredientProposalReviewDetailPage() {
  const { proposalId = "" } = useParams();
  const { accessToken } = useAuth();
  const [proposal, setProposal] = useState<IngredientProposal | null>(null);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [foodGroups, setFoodGroups] = useState<FoodGroup[]>([]);
  const [families, setFamilies] = useState<IngredientFamily[]>([]);
  const [ingredientId, setIngredientId] = useState("");
  const [aliasText, setAliasText] = useState("");
  const [aliasLanguage, setAliasLanguage] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [canonicalName, setCanonicalName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [aliasesText, setAliasesText] = useState("");
  const [foodGroup, setFoodGroup] = useState("");
  const [family, setFamily] = useState("");
  const [storageClass, setStorageClass] = useState("");
  const [productForm, setProductForm] = useState("");
  const [preservation, setPreservation] = useState("");
  const [defaultUnitId, setDefaultUnitId] = useState("");
  const [shoppingUnitId, setShoppingUnitId] = useState("");
  const [conversionNotes, setConversionNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const loadProposal = useCallback(async () => {
    if (!accessToken || !proposalId) {
      return;
    }
    setLoading(true);
    try {
      const data = await proposalsApi.getPlatformIngredientProposal(accessToken, proposalId);
      setProposal(data);
      setCanonicalName(data.suggested_canonical_name || data.normalized_name.replace(/ /g, "_"));
      setDisplayName(data.proposed_name);
      setAliasesText(data.proposed_name);
      setAliasText(data.proposed_name);
      setAliasLanguage(data.source_locale || "");
      setFoodGroup(data.suggested_food_group_id ?? "");
      setFamily(data.suggested_family_id ?? "");
      setStorageClass(data.suggested_storage_class ?? "");
      setProductForm(data.suggested_product_form ?? "");
      setPreservation(data.suggested_preservation ?? "");
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load proposal");
    } finally {
      setLoading(false);
    }
  }, [accessToken, proposalId]);

  useEffect(() => {
    void loadProposal();
  }, [loadProposal]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setOptionsError(null);
    Promise.all([
      fetchUnits(accessToken),
      fetchFoodGroups(accessToken),
      fetchIngredients(accessToken),
    ])
      .then(([nextUnits, nextFoodGroups, nextIngredients]) => {
        if (cancelled) {
          return;
        }
        setUnits(nextUnits);
        setFoodGroups(nextFoodGroups);
        setIngredients(nextIngredients);
        setOptionsError(null);
      })
      .catch((err) => {
        if (!cancelled) {
          setUnits([]);
          setFoodGroups([]);
          setIngredients([]);
          setOptionsError(err instanceof ApiError ? err.message : "Failed to load review options");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const ingredientOptions = useMemo(
    () =>
      ingredients.map((ingredient) => ({
        value: String(ingredient.id),
        label: `${ingredient.display_name} (${ingredient.canonical_name}) · #${ingredient.id}`,
      })),
    [ingredients],
  );

  useEffect(() => {
    setFamilies([]);
    if (!accessToken || !foodGroup) {
      return;
    }
    let cancelled = false;
    const requestedGroup = foodGroup;
    fetchFoodGroupFamilies(accessToken, requestedGroup)
      .then((data) => {
        if (!cancelled && requestedGroup === foodGroup) {
          setFamilies(data);
          setOptionsError(null);
        }
      })
      .catch((err) => {
        if (!cancelled && requestedGroup === foodGroup) {
          setFamilies([]);
          setOptionsError(err instanceof ApiError ? err.message : "Failed to load families");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, foodGroup]);

  async function runAction(action: () => Promise<IngredientProposal>) {
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await action();
      setProposal(updated);
      setSuccess(`Proposal marked ${formatStatus(updated.resolution_status)}.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Review action failed.");
    } finally {
      setBusy(false);
    }
  }

  function requireReviewNote(): string | null {
    const note = reviewNote.trim();
    if (!note) {
      setError("Add a review note explaining why or what the submitter should do next.");
      setSuccess(null);
      return null;
    }
    return note;
  }

  function handleMapExisting(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    const id = Number(ingredientId);
    if (!Number.isFinite(id) || id <= 0) {
      setError("Select an existing ingredient.");
      return;
    }
    void runAction(() =>
      proposalsApi.mapExistingIngredientProposal(accessToken, proposalId, {
        ingredient_id: id,
        review_note: reviewNote || undefined,
      }),
    );
  }

  function handleAddAlias(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    const id = Number(ingredientId);
    if (!Number.isFinite(id) || id <= 0) {
      setError("Select an existing ingredient.");
      return;
    }
    void runAction(() =>
      proposalsApi.addAliasIngredientProposal(accessToken, proposalId, {
        ingredient_id: id,
        alias: aliasText || undefined,
        language: aliasLanguage || undefined,
        review_note: reviewNote || undefined,
      }),
    );
  }

  function handleApproveNew(event: FormEvent) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    void runAction(() =>
      proposalsApi.approveNewIngredientProposal(accessToken, proposalId, {
        canonical_name: canonicalName || undefined,
        display_name: displayName || undefined,
        aliases: parseAliases(aliasesText),
        food_group: foodGroup || undefined,
        family: family || undefined,
        storage_class: storageClass || undefined,
        product_form: productForm || undefined,
        preservation: preservation || undefined,
        default_unit_id: defaultUnitId ? Number(defaultUnitId) : undefined,
        preferred_shopping_unit_id: shoppingUnitId ? Number(shoppingUnitId) : undefined,
        conversion_notes: conversionNotes || undefined,
        review_note: reviewNote || undefined,
      }),
    );
  }

  if (!proposal && !loading) {
    return (
      <div className="admin-page">
        <PageShell title="Proposal not found">
          <p className="form-error" role="alert">
            {error ?? "Proposal not found"}
          </p>
          <Link to={REVIEW_QUEUE_PATH}>Back to queue</Link>
        </PageShell>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <PageShell
        title={proposal ? proposal.proposed_name : "Proposal"}
        subtitle="Platform review actions for a missing-ingredient proposal."
        loading={loading}
        loadingMessage="Loading proposal…"
        actions={<Link to={REVIEW_QUEUE_PATH}>Back to queue</Link>}
      >
        {proposal ? (
          <>
            <p>
              <StatusBadge variant={statusVariant(proposal.resolution_status)}>
                {formatStatus(proposal.resolution_status)}
              </StatusBadge>
            </p>
            <dl className="stack">
              <div>
                <dt>Locale</dt>
                <dd>{proposal.source_locale}</dd>
              </div>
              <div>
                <dt>Description</dt>
                <dd>{proposal.description || "—"}</dd>
              </div>
              <div>
                <dt>Culinary context</dt>
                <dd>{proposal.culinary_context || "—"}</dd>
              </div>
              <div>
                <dt>Suggested food group</dt>
                <dd>{proposal.suggested_food_group_id || "—"}</dd>
              </div>
              <div>
                <dt>Suggested family</dt>
                <dd>{proposal.suggested_family_id || "—"}</dd>
              </div>
              {proposal.review_note ? (
                <div>
                  <dt>Review note</dt>
                  <dd>{proposal.review_note}</dd>
                </div>
              ) : null}
            </dl>

            {error ? (
              <p className="form-error" role="alert">
                {error}
              </p>
            ) : null}
            {optionsError ? (
              <p className="form-error" role="alert">
                {optionsError}
              </p>
            ) : null}
            {success ? (
              <p className="success" role="status">
                {success}
              </p>
            ) : null}

            {proposal.resolution_status === "pending" ||
            proposal.resolution_status === "needs_information" ? (
              <div className="stack">
                <label>
                  Review note
                  <textarea
                    value={reviewNote}
                    onChange={(event) => setReviewNote(event.target.value)}
                    rows={3}
                    placeholder="Required for reject, request information, and mark duplicate"
                  />
                </label>
                <p className="muted">
                  Reject, request information, and mark duplicate require a note explaining why or what to do next.
                </p>
                <div className="stack">
                  <span>Existing ingredient</span>
                  <SearchSelect
                    ariaLabel="Existing ingredient"
                    value={ingredientId}
                    options={ingredientOptions}
                    onChange={setIngredientId}
                    placeholder="Search by display or canonical name…"
                    allowEmptyOption
                    emptyLabel="Select ingredient"
                  />
                </div>
                <form className="row-actions" onSubmit={handleMapExisting}>
                  <Button type="submit" loading={busy}>
                    Map existing
                  </Button>
                </form>
                <form className="stack settings-form" onSubmit={handleAddAlias}>
                  <h2>Add alias</h2>
                  <label>
                    Alias text
                    <input value={aliasText} onChange={(event) => setAliasText(event.target.value)} required />
                  </label>
                  <label>
                    Language / locale
                    <input
                      value={aliasLanguage}
                      onChange={(event) => setAliasLanguage(event.target.value)}
                      maxLength={16}
                      placeholder="e.g. en, es"
                    />
                  </label>
                  <Button type="submit" loading={busy} variant="secondary">
                    Add alias
                  </Button>
                </form>

                <form className="stack settings-form" onSubmit={handleApproveNew}>
                  <h2>Approve new canonical ingredient</h2>
                  <label>
                    Canonical name
                    <input
                      value={canonicalName}
                      onChange={(event) => setCanonicalName(event.target.value)}
                      required
                      pattern="[a-z0-9_]+"
                      title="Lowercase snake_case identifier, e.g. torch_ginger_flower"
                    />
                  </label>
                  <p className="muted">
                    Internal slug. If this already exists, use map-existing or add-alias instead.
                  </p>
                  <label>
                    Display name
                    <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} required />
                  </label>
                  <label>
                    Aliases
                    <textarea
                      value={aliasesText}
                      onChange={(event) => setAliasesText(event.target.value)}
                      rows={3}
                      placeholder="One per line, or comma-separated"
                    />
                  </label>
                  <label>
                    Food group
                    <select
                      value={foodGroup}
                      onChange={(event) => {
                        setFoodGroup(event.target.value);
                        setFamily("");
                      }}
                      required
                    >
                      <option value="">Select food group</option>
                      {foodGroups.map((group) => (
                        <option key={group.id} value={group.id}>
                          {group.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Family
                    <select value={family} onChange={(event) => setFamily(event.target.value)} required>
                      <option value="">Select existing family</option>
                      {families.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <p className="muted">
                    If no suitable family exists, request information or leave pending until taxonomy is extended.
                  </p>
                  <label>
                    Storage class
                    <input value={storageClass} onChange={(event) => setStorageClass(event.target.value)} />
                  </label>
                  <label>
                    Product form
                    <input value={productForm} onChange={(event) => setProductForm(event.target.value)} />
                  </label>
                  <label>
                    Preservation
                    <input value={preservation} onChange={(event) => setPreservation(event.target.value)} />
                  </label>
                  <label>
                    Default unit
                    <select value={defaultUnitId} onChange={(event) => setDefaultUnitId(event.target.value)}>
                      <option value="">None</option>
                      {units.map((unit) => (
                        <option key={unit.id} value={unit.id}>
                          {unit.name} ({unit.symbol})
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Preferred shopping unit
                    <select value={shoppingUnitId} onChange={(event) => setShoppingUnitId(event.target.value)}>
                      <option value="">None</option>
                      {units.map((unit) => (
                        <option key={unit.id} value={unit.id}>
                          {unit.name} ({unit.symbol})
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Conversion notes / hints
                    <textarea
                      value={conversionNotes}
                      onChange={(event) => setConversionNotes(event.target.value)}
                      rows={3}
                      placeholder="e.g. 1 bunch ≈ 150 g; measure by weight when possible"
                    />
                  </label>
                  <Button type="submit" loading={busy}>
                    Approve new canonical
                  </Button>
                </form>

                <div className="row-actions">
                  <Button
                    type="button"
                    variant="secondary"
                    loading={busy}
                    onClick={() => {
                      const note = requireReviewNote();
                      if (!accessToken || !note) {
                        return;
                      }
                      void runAction(() =>
                        proposalsApi.requestIngredientProposalInformation(accessToken, proposalId, note),
                      );
                    }}
                  >
                    Request information
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    loading={busy}
                    onClick={() => {
                      const note = requireReviewNote();
                      if (!accessToken || !note) {
                        return;
                      }
                      void runAction(() =>
                        proposalsApi.markDuplicateIngredientProposal(accessToken, proposalId, {
                          ingredient_id: ingredientId ? Number(ingredientId) : undefined,
                          review_note: note,
                        }),
                      );
                    }}
                  >
                    Mark duplicate
                  </Button>
                  <Button
                    type="button"
                    variant="danger"
                    loading={busy}
                    onClick={() => {
                      const note = requireReviewNote();
                      if (!accessToken || !note) {
                        return;
                      }
                      void runAction(() =>
                        proposalsApi.rejectIngredientProposal(accessToken, proposalId, note),
                      );
                    }}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        ) : null}
      </PageShell>
    </div>
  );
}
