import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import * as catalogApi from "../../api/publicCatalog";
import type { PublicRecipeHousehold } from "../../api/publicCatalog";
import { Button, EmptyState, PageShell, StatusBadge } from "../../components/ui";
import type { StatusBadgeVariant } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

function statusVariant(status: PublicRecipeHousehold["status"]): StatusBadgeVariant {
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

export function HouseholdPublicationRequestsPage() {
  const { accessToken, isHouseholdAdmin } = useAuth();
  const [items, setItems] = useState<PublicRecipeHousehold[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [withdrawingId, setWithdrawingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken || !isHouseholdAdmin) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await catalogApi.listHouseholdPublicationRequests(accessToken);
      setItems(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load publication requests");
    } finally {
      setLoading(false);
    }
  }, [accessToken, isHouseholdAdmin]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleWithdraw(id: string) {
    if (!accessToken) {
      return;
    }
    setWithdrawingId(id);
    setError(null);
    try {
      await catalogApi.withdrawPublicationRequest(accessToken, id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to withdraw request");
    } finally {
      setWithdrawingId(null);
    }
  }

  return (
    <div className="catalog-page">
      <PageShell
        title="Publication requests"
        subtitle="Recipes your household has submitted to the public catalog."
        loading={loading}
        loadingMessage="Loading requests…"
      >
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && !error && items.length === 0 ? (
          <EmptyState
            title="No publication requests"
            description="Submit a recipe from its detail page to request public catalog publication."
          />
        ) : null}
        <ul className="catalog-list">
          {items.map((item) => (
            <li key={item.id} className="catalog-list-row">
              <div>
                <strong>{item.title}</strong>
                <div className="muted">
                  <StatusBadge variant={statusVariant(item.status)}>{item.status}</StatusBadge>
                  {item.latest_version
                    ? ` · Version ${item.latest_version.version_number}`
                    : null}
                </div>
                {item.review_note ? <p className="muted">Review note: {item.review_note}</p> : null}
                <Link to={`/dishes/${item.originating_dish_id}/recipes/${item.originating_recipe_id}`}>
                  Open source recipe
                </Link>
              </div>
              {item.status === "submitted" ? (
                <Button
                  variant="secondary"
                  disabled={withdrawingId === item.id}
                  onClick={() => void handleWithdraw(item.id)}
                >
                  {withdrawingId === item.id ? "Withdrawing…" : "Withdraw"}
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      </PageShell>
    </div>
  );
}
