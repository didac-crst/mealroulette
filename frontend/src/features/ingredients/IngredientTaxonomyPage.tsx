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
      <section className="card">
        <p className="muted">Loading taxonomy…</p>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between">
        <div>
          <h2>Ingredient taxonomy</h2>
          <p className="muted">Browse food groups, families, and ingredients. Test name resolution.</p>
        </div>
        <ButtonLink to="/ingredients" variant="secondary">
          Ingredient list
        </ButtonLink>
      </div>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {overview ? (
        <div className="grid-2">
          <p>Food groups: {overview.totals.food_groups}</p>
          <p>Families: {overview.totals.families}</p>
          <p>Ingredients: {overview.totals.ingredients}</p>
          <p>Aliases: {overview.totals.aliases}</p>
          <p>Approved conversions: {overview.totals.approved_conversions}</p>
          <p>Unapproved conversions: {overview.totals.unapproved_conversions}</p>
        </div>
      ) : null}

      <div className="grid-2">
        <div className="stack">
          <h3>Food groups</h3>
          <ul className="bulleted-list">
            {foodGroups.map((group) => (
              <li key={group.id}>
                <button
                  type="button"
                  className={selectedGroupId === group.id ? "button" : "button button-secondary"}
                  onClick={() => {
                    setSelectedGroupId(group.id);
                    setSelectedFamilyId(null);
                  }}
                >
                  {group.label}
                </button>
              </li>
            ))}
          </ul>
          {selectedGroupId ? (
            <>
              <h3>Families</h3>
              <ul className="bulleted-list">
                {families.map((family) => (
                  <li key={family.id}>
                    <button
                      type="button"
                      className={selectedFamilyId === family.id ? "button" : "button button-secondary"}
                      onClick={() => setSelectedFamilyId(family.id)}
                    >
                      {family.label}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>

        <div className="stack">
          <h3>Ingredients</h3>
          {!selectedFamilyId ? (
            <p className="muted">Select a food group and family to browse catalog ingredients.</p>
          ) : (
            <ul className="bulleted-list">
              {ingredients.map((ingredient) => (
                <li key={ingredient.id}>
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
        </div>
      </div>

      <form className="stack" onSubmit={(event) => void handleResolve(event)}>
        <h3>Resolver</h3>
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
        <button type="submit" className="button" disabled={resolverBusy}>
          {resolverBusy ? "Resolving…" : "Resolve"}
        </button>
      </form>

      {resolveResult ? (
        <div className="stack">
          <h4>Resolve result</h4>
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
        </div>
      ) : null}

      {classifyResult ? (
        <div className="stack">
          <h4>Classification</h4>
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
        </div>
      ) : null}
    </section>
  );
}
