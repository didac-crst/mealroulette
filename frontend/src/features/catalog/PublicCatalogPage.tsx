import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/client";
import * as catalogApi from "../../api/publicCatalog";
import type { PublicRecipeMember } from "../../api/publicCatalog";
import { EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

export function PublicCatalogPage() {
  const { accessToken, hasHousehold } = useAuth();
  const [items, setItems] = useState<PublicRecipeMember[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!accessToken || !hasHousehold) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await catalogApi.listPublicRecipes(accessToken);
      setItems(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load public catalog");
    } finally {
      setLoading(false);
    }
  }, [accessToken, hasHousehold]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!hasHousehold) {
    return (
      <div className="catalog-page">
        <PageShell title="Public catalog" subtitle="Browse recipes shared by other households.">
          <EmptyState
            title="Household required"
            description="Join or create a household to browse the public catalog."
          />
        </PageShell>
      </div>
    );
  }

  return (
    <div className="catalog-page">
      <PageShell
        title="Public catalog"
        subtitle="Approved recipes you can adopt into your household."
        loading={loading}
        loadingMessage="Loading catalog…"
      >
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <EmptyState
            title="No public recipes yet"
            description="When platform admins approve publication requests, they appear here."
          />
        ) : null}
        <ul className="catalog-list">
          {items.map((item) => (
            <li key={item.id}>
              <Link to={`/catalog/recipes/${item.id}`} className="catalog-list-link">
                <strong>{item.title}</strong>
                {item.description ? <span className="muted">{item.description}</span> : null}
                <span className="muted">Version {item.current_version.version_number}</span>
              </Link>
            </li>
          ))}
        </ul>
      </PageShell>
    </div>
  );
}
