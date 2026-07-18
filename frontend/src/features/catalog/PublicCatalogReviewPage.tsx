import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import * as catalogApi from "../../api/publicCatalog";
import type { PublicRecipePlatform } from "../../api/publicCatalog";
import { Button, EmptyState, PageShell, StatusBadge } from "../../components/ui";
import type { StatusBadgeVariant } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

const REVIEW_QUEUE_PATH = "/catalog/review";

function statusVariant(status: PublicRecipePlatform["status"]): StatusBadgeVariant {
  switch (status) {
    case "public":
      return "success";
    case "rejected":
    case "withdrawn":
    case "delisted":
      return "danger";
    case "submitted":
      return "warning";
    default:
      return "default";
  }
}

export function PublicCatalogReviewQueuePage() {
  const { accessToken } = useAuth();
  const [items, setItems] = useState<PublicRecipePlatform[]>([]);
  const [statusFilter, setStatusFilter] = useState("submitted");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    catalogApi
      .listPlatformPublicRecipes(accessToken, statusFilter || undefined)
      .then((data) => {
        if (!cancelled) {
          setItems(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setItems([]);
          setError(err instanceof ApiError ? err.message : "Failed to load review queue");
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
    <div className="catalog-page">
      <PageShell
        title="Public catalog review"
        subtitle="Approve, reject, or delist publication requests."
        loading={loading}
        loadingMessage="Loading queue…"
      >
        <label className="form-field">
          <span>Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="submitted">Submitted</option>
            <option value="public">Public</option>
            <option value="rejected">Rejected</option>
            <option value="withdrawn">Withdrawn</option>
            <option value="delisted">Delisted</option>
            <option value="">All</option>
          </select>
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <EmptyState title="No items" description="No publication requests match this filter." />
        ) : null}
        <ul className="catalog-list">
          {items.map((item) => (
            <li key={item.id}>
              <Link to={`${REVIEW_QUEUE_PATH}/${item.id}`} className="catalog-list-link">
                <strong>{item.title}</strong>
                <StatusBadge variant={statusVariant(item.status)}>{item.status}</StatusBadge>
                {item.description ? <span className="muted">{item.description}</span> : null}
              </Link>
            </li>
          ))}
        </ul>
      </PageShell>
    </div>
  );
}

export function PublicCatalogReviewDetailPage() {
  const { publicRecipeId } = useParams();
  const { accessToken } = useAuth();
  const [item, setItem] = useState<PublicRecipePlatform | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewNote, setReviewNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !publicRecipeId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await catalogApi.getPlatformPublicRecipe(accessToken, publicRecipeId);
      setItem(data);
      setError(null);
    } catch (err) {
      setItem(null);
      setError(err instanceof ApiError ? err.message : "Failed to load publication request");
    } finally {
      setLoading(false);
    }
  }, [accessToken, publicRecipeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(action: "approve" | "reject" | "delist") {
    if (!accessToken || !publicRecipeId) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (action === "approve") {
        await catalogApi.approvePublicRecipe(accessToken, publicRecipeId, reviewNote || undefined);
      } else if (action === "reject") {
        await catalogApi.rejectPublicRecipe(accessToken, publicRecipeId, reviewNote);
      } else {
        await catalogApi.delistPublicRecipe(accessToken, publicRecipeId, reviewNote);
      }
      setReviewNote("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Review action failed");
    } finally {
      setSubmitting(false);
    }
  }

  function onApprove(event: FormEvent) {
    event.preventDefault();
    void runAction("approve");
  }

  if (loading) {
    return (
      <div className="catalog-page">
        <PageShell title="Publication review" loading loadingMessage="Loading…" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="catalog-page">
        <EmptyState
          title="Not found"
          description={error ?? "Publication request not found."}
          action={
            <Link to={REVIEW_QUEUE_PATH} className="button button-secondary">
              Back to queue
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="catalog-page">
      <PageShell
        title={item.title}
        subtitle={`Status: ${item.status}`}
        actions={
          <Link to={REVIEW_QUEUE_PATH} className="button button-secondary">
            Back to queue
          </Link>
        }
      >
        {error ? <p className="form-error">{error}</p> : null}
        <p className="muted">
          Household {item.originating_household_id} · dish {item.originating_dish_id} · recipe{" "}
          {item.originating_recipe_id}
        </p>
        {item.description ? <p>{item.description}</p> : null}
        {item.review_note ? <p className="muted">Previous note: {item.review_note}</p> : null}
        {item.latest_version ? (
          <p className="muted">Latest version {item.latest_version.version_number}</p>
        ) : null}

        <label className="form-field">
          <span>Review note</span>
          <textarea
            value={reviewNote}
            onChange={(event) => setReviewNote(event.target.value)}
            rows={4}
            placeholder="Required for reject and delist"
          />
        </label>

        <div className="catalog-detail-actions">
          {item.status === "submitted" ? (
            <>
              <Button disabled={submitting} onClick={onApprove}>
                Approve
              </Button>
              <Button
                variant="secondary"
                disabled={submitting || !reviewNote.trim()}
                onClick={() => void runAction("reject")}
              >
                Reject
              </Button>
            </>
          ) : null}
          {item.status === "public" ? (
            <Button
              variant="secondary"
              disabled={submitting || !reviewNote.trim()}
              onClick={() => void runAction("delist")}
            >
              Delist
            </Button>
          ) : null}
        </div>
      </PageShell>
    </div>
  );
}
