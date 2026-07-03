import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createIngredient,
  createIngredientAlias,
  createIngredientConversion,
  deleteIngredient,
  deleteIngredientAlias,
  deleteIngredientConversion,
  fetchIngredient,
  fetchUnits,
  updateIngredient,
  updateIngredientConversion,
  type IngredientDetail,
  type IngredientInput,
  type Unit,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { useAuth } from "../auth/AuthContext";

const AGGREGATION_STRATEGIES = [
  { value: "", label: "Default" },
  { value: "strict_same_dimension", label: "Strict same dimension" },
  { value: "prefer_mass", label: "Prefer mass" },
  { value: "prefer_volume", label: "Prefer volume" },
  { value: "prefer_count", label: "Prefer count" },
  { value: "allow_approximate_conversion", label: "Allow approximate conversion" },
  { value: "never_convert_count", label: "Never convert count" },
] as const;

const CONFIDENCE_OPTIONS = ["exact", "high", "medium", "low", "not_recommended", "approximate", "measured"] as const;

const emptyForm: IngredientInput = {
  canonical_name: "",
  display_name: "",
  category: "",
  family: "",
  default_unit_id: null,
  preferred_shopping_unit_id: null,
  aggregation_unit_id: null,
  aggregation_strategy: null,
  pantry_item: false,
  season_start_month: null,
  season_end_month: null,
  notes: "",
  aliases: [],
};

function ingredientToForm(ingredient: IngredientDetail): IngredientInput {
  return {
    display_name: ingredient.display_name,
    category: ingredient.category,
    family: ingredient.family,
    default_unit_id: ingredient.default_unit_id,
    preferred_shopping_unit_id: ingredient.preferred_shopping_unit_id,
    aggregation_unit_id: ingredient.aggregation_unit_id,
    aggregation_strategy: ingredient.aggregation_strategy,
    pantry_item: ingredient.pantry_item,
    season_start_month: ingredient.season_start_month,
    season_end_month: ingredient.season_end_month,
    notes: ingredient.notes,
  };
}

function unitOptions(units: Unit[]): Unit[] {
  return [...units].sort((left, right) => left.symbol.localeCompare(right.symbol));
}

export function IngredientEditPage() {
  const { ingredientId } = useParams();
  const isNew = !ingredientId;
  const navigate = useNavigate();
  const { accessToken, isAdmin } = useAuth();

  const [form, setForm] = useState<IngredientInput>(emptyForm);
  const [detail, setDetail] = useState<IngredientDetail | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [newAliases, setNewAliases] = useState("");
  const [aliasLanguage, setAliasLanguage] = useState("");
  const [conversionForm, setConversionForm] = useState({
    from_unit_id: "",
    to_unit_id: "",
    factor: "",
    confidence: "medium",
    notes: "",
    approved: false,
  });
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) {
      navigate("/ingredients");
    }
  }, [isAdmin, navigate]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    fetchUnits(accessToken)
      .then(setUnits)
      .catch(() => setUnits([]));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken || isNew) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchIngredient(accessToken, Number(ingredientId))
      .then((data) => {
        if (!cancelled) {
          setDetail(data);
          setForm(ingredientToForm(data));
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load ingredient");
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
  }, [accessToken, ingredientId, isNew]);

  const sortedUnits = useMemo(() => unitOptions(units), [units]);

  const reloadDetail = async () => {
    if (!accessToken || isNew || !ingredientId) {
      return;
    }
    const data = await fetchIngredient(accessToken, Number(ingredientId));
    setDetail(data);
    setForm(ingredientToForm(data));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const aliases = newAliases
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      if (isNew) {
        const created = await createIngredient(accessToken, {
          ...form,
          canonical_name: form.canonical_name?.trim() || form.display_name.trim(),
          aliases,
        });
        navigate(`/ingredients/${created.id}/edit`, { replace: true });
        return;
      }
      await updateIngredient(accessToken, Number(ingredientId), form);
      await reloadDetail();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save ingredient");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!accessToken || isNew || !ingredientId) {
      return;
    }
    if (!window.confirm("Delete this ingredient? This fails if recipes still reference it.")) {
      return;
    }
    try {
      await deleteIngredient(accessToken, Number(ingredientId));
      navigate("/ingredients");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete ingredient");
    }
  };

  const handleAddAlias = async () => {
    if (!accessToken || isNew || !ingredientId) {
      return;
    }
    const alias = newAliases
      .split("\n")
      .map((line) => line.trim())
      .find(Boolean);
    if (!alias) {
      return;
    }
    try {
      await createIngredientAlias(accessToken, Number(ingredientId), {
        alias,
        language: aliasLanguage.trim() || null,
      });
      setNewAliases("");
      setAliasLanguage("");
      await reloadDetail();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add alias");
    }
  };

  const handleAddConversion = async () => {
    if (!accessToken || isNew || !ingredientId) {
      return;
    }
    if (!conversionForm.from_unit_id || !conversionForm.to_unit_id || !conversionForm.factor) {
      return;
    }
    try {
      await createIngredientConversion(accessToken, Number(ingredientId), {
        from_unit_id: Number(conversionForm.from_unit_id),
        to_unit_id: Number(conversionForm.to_unit_id),
        factor: conversionForm.factor,
        confidence: conversionForm.confidence,
        notes: conversionForm.notes || null,
        approved: conversionForm.approved,
        source: "manual",
      });
      setConversionForm({
        from_unit_id: "",
        to_unit_id: "",
        factor: "",
        confidence: "medium",
        notes: "",
        approved: false,
      });
      await reloadDetail();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add conversion");
    }
  };

  if (loading) {
    return (
      <section className="card">
        <p className="muted">Loading ingredient…</p>
      </section>
    );
  }

  return (
    <section className="card stack">
      <div className="row-between">
        <h2>{isNew ? "New ingredient" : `Edit ${detail?.display_name ?? "ingredient"}`}</h2>
        <ButtonLink to="/ingredients" variant="secondary">
          Back to list
        </ButtonLink>
      </div>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      <form onSubmit={(event) => void handleSubmit(event)} className="stack">
        <fieldset>
          <legend>Basic info</legend>
          <div className="stack">
            {isNew ? (
              <label>
                Canonical name
                <input
                  value={form.canonical_name ?? ""}
                  onChange={(event) => setForm({ ...form, canonical_name: event.target.value })}
                  placeholder="e.g. cherry_tomato"
                  required
                />
              </label>
            ) : (
              <p className="muted">
                Canonical name: <strong>{detail?.canonical_name}</strong>
              </p>
            )}
            <label>
              Display name
              <input
                value={form.display_name}
                onChange={(event) => setForm({ ...form, display_name: event.target.value })}
                required
              />
            </label>
            <label>
              Description / notes
              <textarea
                value={form.notes ?? ""}
                onChange={(event) => setForm({ ...form, notes: event.target.value })}
                rows={3}
              />
            </label>
            <div className="grid-2">
              <label>
                Category
                <input
                  value={form.category ?? ""}
                  onChange={(event) => setForm({ ...form, category: event.target.value })}
                />
              </label>
              <label>
                Family
                <input
                  value={form.family ?? ""}
                  onChange={(event) => setForm({ ...form, family: event.target.value })}
                  placeholder="e.g. tomato_family"
                />
              </label>
            </div>
            <label className="checkbox-pill">
              <input
                type="checkbox"
                checked={Boolean(form.pantry_item)}
                onChange={(event) => setForm({ ...form, pantry_item: event.target.checked })}
              />
              Pantry item (exclude from shopping lists by default)
            </label>
            <div className="grid-2">
              <label>
                Season start month
                <input
                  type="number"
                  min={1}
                  max={12}
                  value={form.season_start_month ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      season_start_month: event.target.value ? Number(event.target.value) : null,
                    })
                  }
                />
              </label>
              <label>
                Season end month
                <input
                  type="number"
                  min={1}
                  max={12}
                  value={form.season_end_month ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      season_end_month: event.target.value ? Number(event.target.value) : null,
                    })
                  }
                />
              </label>
            </div>
            {isNew ? (
              <label>
                Initial aliases (one per line)
                <textarea value={newAliases} onChange={(event) => setNewAliases(event.target.value)} rows={4} />
              </label>
            ) : null}
          </div>
        </fieldset>

        <fieldset>
          <legend>Unit behavior</legend>
          <div className="stack">
            <div className="grid-2">
              <label>
                Default recipe unit
                <select
                  value={form.default_unit_id ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      default_unit_id: event.target.value ? Number(event.target.value) : null,
                    })
                  }
                >
                  <option value="">—</option>
                  {sortedUnits.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.symbol} ({unit.dimension})
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Preferred shopping unit
                <select
                  value={form.preferred_shopping_unit_id ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      preferred_shopping_unit_id: event.target.value ? Number(event.target.value) : null,
                    })
                  }
                >
                  <option value="">—</option>
                  {sortedUnits.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.symbol} ({unit.dimension})
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid-2">
              <label>
                Aggregation unit
                <select
                  value={form.aggregation_unit_id ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      aggregation_unit_id: event.target.value ? Number(event.target.value) : null,
                    })
                  }
                >
                  <option value="">—</option>
                  {sortedUnits.map((unit) => (
                    <option key={unit.id} value={unit.id}>
                      {unit.symbol} ({unit.dimension})
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Aggregation strategy
                <select
                  value={form.aggregation_strategy ?? ""}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      aggregation_strategy: (event.target.value || null) as IngredientInput["aggregation_strategy"],
                    })
                  }
                >
                  {AGGREGATION_STRATEGIES.map((option) => (
                    <option key={option.value || "default"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>
        </fieldset>

        <div className="row-between">
          <button type="submit" className="button" disabled={saving}>
            {saving ? "Saving…" : isNew ? "Create ingredient" : "Save changes"}
          </button>
          {!isNew ? (
            <button type="button" className="button button-danger" onClick={() => void handleDelete()}>
              Delete
            </button>
          ) : null}
        </div>
      </form>

      {!isNew && detail ? (
        <>
          <fieldset>
            <legend>Aliases</legend>
            <ul className="shopping-bulleted-list">
              {detail.aliases.map((alias) => (
                <li key={alias.id} className="row-between ingredient-alias-row">
                  <span>
                    {alias.alias}
                    {alias.language ? <span className="muted"> ({alias.language})</span> : null}
                  </span>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() =>
                      void deleteIngredientAlias(accessToken!, alias.id)
                        .then(() => reloadDetail())
                        .catch((err) =>
                          setError(err instanceof ApiError ? err.message : "Failed to delete alias"),
                        )
                    }
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
            <div className="stack">
              <label>
                New alias
                <input value={newAliases} onChange={(event) => setNewAliases(event.target.value)} />
              </label>
              <label>
                Language code (optional)
                <input
                  value={aliasLanguage}
                  onChange={(event) => setAliasLanguage(event.target.value)}
                  placeholder="fr, en, es…"
                />
              </label>
              <button type="button" className="button button-secondary" onClick={() => void handleAddAlias()}>
                Add alias
              </button>
            </div>
          </fieldset>

          <fieldset>
            <legend>Unit conversions</legend>
            <p className="muted">
              Only approved conversions are used when aggregating shopping lists across incompatible units.
            </p>
            <div className="ingredient-conversion-table stack">
              {detail.unit_conversions.map((conversion) => (
                <div key={conversion.id} className="ingredient-conversion-row card stack">
                  <div className="row-between">
                    <strong>
                      1 {conversion.from_unit_symbol} ≈ {conversion.factor} {conversion.to_unit_symbol}
                    </strong>
                    <label className="checkbox-pill">
                      <input
                        type="checkbox"
                        checked={conversion.approved}
                        onChange={(event) =>
                          void updateIngredientConversion(accessToken!, conversion.id, {
                            approved: event.target.checked,
                          })
                            .then(() => reloadDetail())
                            .catch((err) =>
                              setError(err instanceof ApiError ? err.message : "Failed to update conversion"),
                            )
                        }
                      />
                      Approved
                    </label>
                  </div>
                  <p className="muted">
                    {conversion.confidence}
                    {conversion.notes ? ` · ${conversion.notes}` : ""}
                    {conversion.source ? ` · ${conversion.source}` : ""}
                  </p>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() =>
                      void deleteIngredientConversion(accessToken!, conversion.id)
                        .then(() => reloadDetail())
                        .catch((err) =>
                          setError(err instanceof ApiError ? err.message : "Failed to delete conversion"),
                        )
                    }
                  >
                    Delete conversion
                  </button>
                </div>
              ))}
            </div>
            <div className="stack">
              <div className="grid-2">
                <label>
                  From unit
                  <select
                    value={conversionForm.from_unit_id}
                    onChange={(event) => setConversionForm({ ...conversionForm, from_unit_id: event.target.value })}
                  >
                    <option value="">—</option>
                    {sortedUnits.map((unit) => (
                      <option key={unit.id} value={unit.id}>
                        {unit.symbol}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  To unit
                  <select
                    value={conversionForm.to_unit_id}
                    onChange={(event) => setConversionForm({ ...conversionForm, to_unit_id: event.target.value })}
                  >
                    <option value="">—</option>
                    {sortedUnits.map((unit) => (
                      <option key={unit.id} value={unit.id}>
                        {unit.symbol}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="grid-2">
                <label>
                  Factor
                  <input
                    value={conversionForm.factor}
                    onChange={(event) => setConversionForm({ ...conversionForm, factor: event.target.value })}
                    placeholder="e.g. 80"
                  />
                </label>
                <label>
                  Confidence
                  <select
                    value={conversionForm.confidence}
                    onChange={(event) => setConversionForm({ ...conversionForm, confidence: event.target.value })}
                  >
                    {CONFIDENCE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label>
                Basis / notes
                <input
                  value={conversionForm.notes}
                  onChange={(event) => setConversionForm({ ...conversionForm, notes: event.target.value })}
                  placeholder="one medium carrot"
                />
              </label>
              <label className="checkbox-pill">
                <input
                  type="checkbox"
                  checked={conversionForm.approved}
                  onChange={(event) => setConversionForm({ ...conversionForm, approved: event.target.checked })}
                />
                Approved for shopping aggregation
              </label>
              <button type="button" className="button button-secondary" onClick={() => void handleAddConversion()}>
                Add conversion
              </button>
            </div>
          </fieldset>
        </>
      ) : null}
    </section>
  );
}
