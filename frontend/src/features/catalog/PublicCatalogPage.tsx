import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "../../api/client";
import * as catalogApi from "../../api/publicCatalog";
import type { PublicRecipeMember } from "../../api/publicCatalog";
import { ButtonLink } from "../../components/ButtonLink";
import { Card, ChoiceChip, EmptyState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { PublicRecipeCard } from "./PublicRecipeCard";
import {
  PUBLIC_CATALOG_FILTERS,
  filterPublicCatalogBySearch,
  filterPublicCatalogItems,
  normalizePublicCatalogSearch,
  publicCatalogFilterLabel,
  type PublicCatalogFilter,
} from "./publicCatalogDiscovery";

export function PublicCatalogPage() {
  const { accessToken, hasHousehold, isPlatformAdmin, isHouseholdAdmin } = useAuth();
  const [items, setItems] = useState<PublicRecipeMember[]>([]);
  const [search, setSearch] = useState("");
  const [catalogFilter, setCatalogFilter] = useState<PublicCatalogFilter>("all");
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

  const filteredByType = useMemo(
    () => filterPublicCatalogItems(items, catalogFilter),
    [catalogFilter, items],
  );
  const filteredItems = useMemo(
    () => filterPublicCatalogBySearch(filteredByType, search),
    [filteredByType, search],
  );
  const normalizedSearch = normalizePublicCatalogSearch(search);
  const showingFilteredResults = normalizedSearch.length > 0 || catalogFilter !== "all";

  const actions = (
    <div className="catalog-detail-actions">
      {isHouseholdAdmin ? (
        <ButtonLink to="/catalog/requests" variant="secondary">
          Publication requests
        </ButtonLink>
      ) : null}
      {isPlatformAdmin ? (
        <ButtonLink to="/catalog/review" variant="secondary">
          Recipe review
        </ButtonLink>
      ) : null}
    </div>
  );

  if (!hasHousehold) {
    return (
      <div className="catalog-page">
        <PageShell
          title="Public catalog"
          subtitle="Browse recipes shared by other households."
          actions={isPlatformAdmin ? actions : undefined}
        >
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
        actions={isPlatformAdmin || isHouseholdAdmin ? actions : undefined}
      >
        {error ? <p className="form-error">{error}</p> : null}

        {!loading && !error ? (
          <Card density="comfortable" className="catalog-search-card">
            <label className="catalog-search-label">
              Search public recipes
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Title or description"
                autoComplete="off"
              />
            </label>
            <div className="catalog-filter-bar" role="group" aria-label="Filter by dish type">
              {PUBLIC_CATALOG_FILTERS.map((filter) => (
                <ChoiceChip
                  key={filter}
                  label={publicCatalogFilterLabel(filter)}
                  selected={catalogFilter === filter}
                  onClick={() => setCatalogFilter(filter)}
                />
              ))}
            </div>
            <p className="muted catalog-search-meta">
              {showingFilteredResults
                ? `Showing ${filteredItems.length} of ${items.length} recipes`
                : `${items.length} recipe${items.length === 1 ? "" : "s"}`}
            </p>
          </Card>
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <EmptyState
            title="No public recipes yet"
            description="When platform admins approve publication requests, they appear here."
          />
        ) : null}

        {!loading && !error && items.length > 0 && filteredItems.length === 0 ? (
          <EmptyState
            title="No matches"
            description="No public recipes match your search or filters."
          />
        ) : null}

        {filteredItems.length > 0 ? (
          <div className="dish-card-grid">
            {filteredItems.map((item) => (
              <PublicRecipeCard key={item.id} item={item} />
            ))}
          </div>
        ) : null}
      </PageShell>
    </div>
  );
}
