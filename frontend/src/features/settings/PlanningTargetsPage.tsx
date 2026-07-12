import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  fetchActivePlanningRules,
  updateActivePlanningRules,
  type PlanningRulesConfig,
  type WeeklyTargetSpec,
} from "../../api/planningRules";
import { ApiError } from "../../api/client";
import { useAuth } from "../auth/AuthContext";
import { SettingsPageShell } from "./SettingsPageShell";
import { TARGET_PRESETS, targetHint, targetLabel } from "./planningTargetLabels";

type TargetRow = {
  key: string;
  min: number;
  max: number;
};

function rulesToRows(rules: PlanningRulesConfig): TargetRow[] {
  return Object.entries(rules.weekly_targets).map(([key, spec]) => ({
    key,
    min: spec.min,
    max: spec.max,
  }));
}

function rowsToTargets(rows: TargetRow[]): Record<string, WeeklyTargetSpec> {
  const targets: Record<string, WeeklyTargetSpec> = {};
  for (const row of rows) {
    const key = row.key.trim();
    if (!key) {
      continue;
    }
    targets[key] = { min: row.min, max: row.max };
  }
  return targets;
}

export function PlanningTargetsPage() {
  const { accessToken, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [baseRules, setBaseRules] = useState<PlanningRulesConfig | null>(null);
  const [rows, setRows] = useState<TargetRow[]>([]);
  const [tolerance, setTolerance] = useState(1);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [newPreset, setNewPreset] = useState<string>(TARGET_PRESETS[0]);

  useEffect(() => {
    if (!isAdmin) {
      navigate("/review");
    }
  }, [isAdmin, navigate]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchActivePlanningRules(accessToken)
      .then((rule) => {
        if (cancelled) {
          return;
        }
        setBaseRules(rule.rules);
        setRows(rulesToRows(rule.rules));
        setTolerance(rule.rules.weekly_target_tolerance);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load targets");
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
  }, [accessToken]);

  const usedKeys = useMemo(() => new Set(rows.map((row) => row.key.trim()).filter(Boolean)), [rows]);
  const availablePresets = TARGET_PRESETS.filter((preset) => !usedKeys.has(preset));

  useEffect(() => {
    if (availablePresets.length === 0) {
      setNewPreset("");
      return;
    }
    if (!availablePresets.includes(newPreset as (typeof TARGET_PRESETS)[number])) {
      setNewPreset(availablePresets[0]);
    }
  }, [availablePresets, newPreset]);

  const updateRow = (index: number, patch: Partial<TargetRow>) => {
    setRows((current) => current.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)));
  };

  const removeRow = (index: number) => {
    setRows((current) => current.filter((_, rowIndex) => rowIndex !== index));
  };

  const addPresetRow = () => {
    const preset = availablePresets.includes(newPreset as (typeof TARGET_PRESETS)[number])
      ? newPreset
      : availablePresets[0];
    if (!preset || usedKeys.has(preset)) {
      return;
    }
    setRows((current) => [...current, { key: preset, min: 1, max: 2 }]);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!accessToken || !baseRules) {
      return;
    }
    const duplicate = rows.map((row) => row.key.trim()).filter((key, index, keys) => key && keys.indexOf(key) !== index);
    if (duplicate.length > 0) {
      setError("Each target name must be unique.");
      return;
    }
    if (rows.some((row) => row.min > row.max)) {
      setError("Min cannot be greater than max.");
      return;
    }

    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateActivePlanningRules(accessToken, {
        ...baseRules,
        weekly_targets: rowsToTargets(rows),
        weekly_target_tolerance: tolerance,
      });
      setBaseRules(updated.rules);
      setRows(rulesToRows(updated.rules));
      setTolerance(updated.rules.weekly_target_tolerance);
      setNotice("Targets saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save targets");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <SettingsPageShell title="Weekly targets" subtitle="Meals per week by food type.">
        <p className="muted">Loading…</p>
      </SettingsPageShell>
    );
  }

  return (
    <SettingsPageShell
      title="Weekly targets"
      subtitle="The roulette tries to hit these counts each Mon–Sun week. Uses dish tags."
    >
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {notice ? <p className="muted">{notice}</p> : null}

      <form onSubmit={(event) => void handleSubmit(event)} className="stack">
        <label>
          Flexibility (± meals)
          <input
            type="number"
            min={0}
            max={3}
            value={tolerance}
            onChange={(event) => setTolerance(Number(event.target.value))}
          />
          <span className="muted">How far off min/max can the plan be before warnings.</span>
        </label>

        <div className="stack">
          <h3 className="section-title">Targets</h3>
          {rows.length === 0 ? <p className="muted">No targets yet. Add one below.</p> : null}
          {rows.map((row, index) => (
            <div key={`${row.key}-${index}`} className="target-row">
              <div className="target-row-header">
                <strong>{targetLabel(row.key) || "New target"}</strong>
                {targetHint(row.key) ? <span className="muted target-row-hint">{targetHint(row.key)}</span> : null}
              </div>
              <div className="target-row-fields">
                <label>
                  Tag key
                  <input
                    value={row.key}
                    onChange={(event) => updateRow(index, { key: event.target.value })}
                    placeholder="fish"
                  />
                </label>
                <label>
                  Min
                  <input
                    type="number"
                    min={0}
                    max={14}
                    value={row.min}
                    onChange={(event) => updateRow(index, { min: Number(event.target.value) })}
                  />
                </label>
                <label>
                  Max
                  <input
                    type="number"
                    min={0}
                    max={14}
                    value={row.max}
                    onChange={(event) => updateRow(index, { max: Number(event.target.value) })}
                  />
                </label>
                <button
                  type="button"
                  className="button button-secondary target-row-remove"
                  onClick={() => removeRow(index)}
                  aria-label={`Remove ${row.key} target`}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        {availablePresets.length > 0 ? (
          <div className="target-add-row">
            <label>
              Add target
              <select value={newPreset} onChange={(event) => setNewPreset(event.target.value)}>
                {availablePresets.map((preset) => (
                  <option key={preset} value={preset}>
                    {targetLabel(preset)}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="button button-secondary" onClick={addPresetRow}>
              Add
            </button>
          </div>
        ) : null}

        <button type="submit" className="button" disabled={saving}>
          {saving ? "Saving…" : "Save targets"}
        </button>
      </form>
    </SettingsPageShell>
  );
}
