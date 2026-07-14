import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  classifyIngredientCandidate,
  fetchFamilyIngredients,
  fetchFoodGroupFamilies,
  fetchFoodGroups,
  fetchIngredientTaxonomyOverview,
  resolveIngredientV2,
  type ClassifyCandidateResponse,
  type FoodGroup,
  type IngredientFamily,
  type IngredientResolveV2Response,
  type IngredientTaxonomyOverview,
  type IngredientTaxonomySummary,
} from "../../api/taxonomy";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, Card, FormSection, FormStickyActions, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";

export function IngredientTaxonomyPage() {
  const { accessToken } = useAuth();
  const [overview, setOverview] = useState<IngredientTaxonomyOverview | null>(null);
  const [foodGroups, setFoodGroups] = useState<FoodGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [families, setFamilies] = useState<IngredientFamily[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<string | null>(null);
  const [ingredients, setIngredients] = useState<IngredientTaxonomySummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [resolverInput, setResolverInput] = useState("");
  const [resolverContext, setResolverContext] = useState("");
  const [resolveResult, setResolveResult] = useState<IngredientResolveV2Response | null>(null);
  const [classifyResult, setClassifyResult] = useState<ClassifyCandidateResponse | null>(null);
  const [resolverBusy, setResolverBusy] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    Promise.all([fetchIngredientTaxonomyOverview(accessToken), fetchFoodGroups(accessToken)])
      .then(([overviewData, groupData]) => {
        setOverview(overviewData);
        setFoodGroups(groupData);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load taxonomy");
      })
      .finally(() => setLoading(false));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken || !selectedGroupId) {
      setFamilies([]);
      return;
    }
    fetchFoodGroupFamilies(accessToken, selectedGroupId)
      .then(setFamilies)
      .catch((err) => {
        setFamilies([]);
        setError(err instanceof ApiError ? err.message : "Failed to load families");
      });
  }, [accessToken, selectedGroupId]);

  useEffect(() => {
    if (!accessToken || !selectedFamilyId) {
      setIngredients([]);
      return;
    }
    fetchFamilyIngredients(accessToken, selectedFamilyId)
      .then(setIngredients)
      .catch((err) => {
        setIngredients([]);
        setError(err instanceof ApiError ? err.message : "Failed to load ingredients");
      });
  }, [accessToken, selectedFamilyId]);

  async function handleResolve(event: FormEvent) {
    event.preventDefault();
    if (!accessToken || !resolverInput.trim()) {
      return;
    }
    setResolverBusy(true);
    try {
      const [resolved, classified] = await Promise.all([
        resolveIngredientV2(accessToken, resolverInput.trim()),
        classifyIngredientCandidate(accessToken, {
          name: resolverInput.trim(),
          context: resolverContext.trim() || undefined,
        }),
      ]);
      setResolveResult(resolved);
      setClassifyResult(classified);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Resolver failed");
    } finally {
      setResolverBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="admin-page">
        <PageShell title="Ingredient taxonomy" loading loadingMessage="Loading taxonomy…" />
      </div>
    );
  }

  return (
    <div className="admin-page">
      <PageShell
        title="Ingredient taxonomy"
        subtitle="Browse food groups, families, and ingredients. Test name resolution."
        actions={
          <ButtonLink to="/ingredients" variant="secondary">
            Ingredient list
          </ButtonLink>
        }
      />

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {overview ? (
        <div className="admin-stats-grid">
          <div className="admin-stat-card">
            <span className="admin-stat-label">Food groups</span>
            <span className="admin-stat-value">{overview.totals.food_groups}</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-label">Families</span>
            <span className="admin-stat-value">{overview.totals.families}</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-label">Ingredients</span>
            <span className="admin-stat-value">{overview.totals.ingredients}</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-label">Aliases</span>
            <span className="admin-stat-value">{overview.totals.aliases}</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-label">Approved conversions</span>
            <span className="admin-stat-value">{overview.totals.approved_conversions}</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-label">Unapproved conversions</span>
            <span className="admin-stat-value">{overview.totals.unapproved_conversions}</span>
          </div>
        </div>
      ) : null}

      <div className="taxonomy-browser">
        <Card density="comfortable" className="stack">
          <h2 className="catalog-section-title">Food groups</h2>
          <ul className="taxonomy-pill-list">
            {foodGroups.map((group) => (
              <li key={group.id}>
                <Button
                  type="button"
                  variant={selectedGroupId === group.id ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => {
                    setSelectedGroupId(group.id);
                    setSelectedFamilyId(null);
                  }}
                >
                  {group.label}
                </Button>
              </li>
            ))}
          </ul>
          {selectedGroupId ? (
            <>
              <h2 className="catalog-section-title">Families</h2>
              <ul className="taxonomy-pill-list">
                {families.map((family) => (
                  <li key={family.id}>
                    <Button
                      type="button"
                      variant={selectedFamilyId === family.id ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => setSelectedFamilyId(family.id)}
                    >
                      {family.label}
                    </Button>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </Card>

        <Card density="comfortable">
          <h2 className="catalog-section-title">Ingredients</h2>
          {!selectedFamilyId ? (
            <p className="muted">Select a food group and family to browse catalog ingredients.</p>
          ) : (
            <ul className="taxonomy-ingredient-list">
              {ingredients.map((ingredient) => (
                <li key={ingredient.id} className="taxonomy-ingredient-item">
                  <Link to={`/ingredients/${ingredient.id}/edit`}>{ingredient.display_name}</Link>
                  <span className="muted">
                    {" "}
                    · {ingredient.food_group ?? "—"} · aliases {ingredient.alias_count}
                    {ingredient.missing_family ? " · missing family" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <form className="admin-form" onSubmit={(event) => void handleResolve(event)}>
        <FormSection title="Resolver">
          <label>
            Ingredient text
            <input
              value={resolverInput}
              onChange={(event) => setResolverInput(event.target.value)}
              placeholder="e.g. tomate cerise"
            />
          </label>
          <label>
            Context (optional)
            <input
              value={resolverContext}
              onChange={(event) => setResolverContext(event.target.value)}
              placeholder="Usage context for classification"
            />
          </label>
        </FormSection>
        <FormStickyActions>
          <Button type="submit" loading={resolverBusy}>
            Resolve
          </Button>
        </FormStickyActions>
      </form>

      {resolveResult ? (
        <Card density="comfortable" className="stack">
          <h2 className="catalog-section-title">Resolve result</h2>
          <p>
            Status: <strong>{resolveResult.status}</strong>
            {resolveResult.matched_on ? ` · matched on ${resolveResult.matched_on}` : ""}
          </p>
          {resolveResult.ingredient ? (
            <p>
              {resolveResult.ingredient.display_name} ({resolveResult.ingredient.canonical_name})
            </p>
          ) : null}
          {resolveResult.suggestions && resolveResult.suggestions.length > 0 ? (
            <ul className="bulleted-list">
              {resolveResult.suggestions.map((item) => (
                <li key={item.canonical_name}>
                  {item.display_name} — score {item.score?.toFixed(2)}
                </li>
              ))}
            </ul>
          ) : null}
        </Card>
      ) : null}

      {classifyResult ? (
        <Card density="comfortable" className="stack">
          <h2 className="catalog-section-title">Classification</h2>
          <p>Status: {classifyResult.status}</p>
          {classifyResult.families.length > 0 ? (
            <>
              <p className="muted">Suggested families</p>
              <ul className="bulleted-list">
                {classifyResult.families.map((family) => (
                  <li key={family.id}>
                    {family.id}: {family.reason}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
          {classifyResult.ingredients.length > 0 ? (
            <>
              <p className="muted">Suggested ingredients</p>
              <ul className="bulleted-list">
                {classifyResult.ingredients.map((item) => (
                  <li key={item.canonical_name}>
                    {item.display_name} ({item.canonical_name})
                  </li>
                ))}
              </ul>
            </>
          ) : null}
          {classifyResult.draft ? (
            <pre>{JSON.stringify(classifyResult.draft, null, 2)}</pre>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
