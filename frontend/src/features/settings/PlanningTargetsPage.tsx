import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  fetchActivePlanningRules,
  updateActivePlanningRules,
  type PlanningRulesConfig,
  type WeeklyTargetSpec,
} from "../../api/planningRules";
import { ApiError } from "../../api/client";
import { Button, ChoiceChip, EmptyState, FormSection, FormStickyActions, NumberStepper, OverflowMenu } from "../../components/ui";
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
  const { accessToken, isHouseholdAdmin, loading: authLoading } = useAuth();
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
    if (!authLoading && !isHouseholdAdmin) {
      navigate("/today");
    }
  }, [isHouseholdAdmin, authLoading, navigate]);

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

  if (authLoading || loading) {
    return (
      <SettingsPageShell
        title="Weekly targets"
        subtitle="The roulette tries to hit these counts each Mon–Sun week. Uses dish tags."
        loading
      >
        {null}
      </SettingsPageShell>
    );
  }

  if (!isHouseholdAdmin) {
    return null;
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
      {notice ? <p className="muted admin-notice">{notice}</p> : null}

      <form onSubmit={(event) => void handleSubmit(event)} className="admin-form">
        <FormSection title="Flexibility">
          <NumberStepper
            ariaLabel="Flexibility"
            label="Flexibility (± meals)"
            min={0}
            max={3}
            value={tolerance}
            onChange={setTolerance}
          />
          <p className="muted admin-field-hint">How far off min/max can the plan be before warnings.</p>
        </FormSection>

        <FormSection title="Targets">
          {rows.length === 0 ? (
            <EmptyState title="No targets yet" description="Add a target below to guide weekly meal variety." />
          ) : null}
          <div className="stack">
            {rows.map((row, index) => (
              <div key={`${row.key}-${index}`} className="target-row">
                <div className="target-row-header">
                  <div className="target-row-heading">
                    <strong className="target-row-label">{targetLabel(row.key) || "New target"}</strong>
                    {targetHint(row.key) ? (
                      <p className="muted target-row-hint">{targetHint(row.key)}</p>
                    ) : null}
                  </div>
                  <OverflowMenu
                    ariaLabel={`Actions for ${targetLabel(row.key)} target`}
                    items={[
                      {
                        id: "remove",
                        label: "Remove",
                        variant: "danger",
                        onClick: () => removeRow(index),
                      },
                    ]}
                  />
                </div>
                <div className="target-row-fields">
                  <NumberStepper
                    ariaLabel={`Minimum ${row.key}`}
                    label="Min"
                    min={0}
                    max={14}
                    value={row.min}
                    onChange={(min) => updateRow(index, { min })}
                  />
                  <NumberStepper
                    ariaLabel={`Maximum ${row.key}`}
                    label="Max"
                    min={0}
                    max={14}
                    value={row.max}
                    onChange={(max) => updateRow(index, { max })}
                  />
                </div>
              </div>
            ))}
          </div>
        </FormSection>

        {availablePresets.length > 0 ? (
          <div className="target-add-row">
            <span className="muted">Add target</span>
            <div className="catalog-filter-bar">
              {availablePresets.map((preset) => (
                <ChoiceChip
                  key={preset}
                  label={targetLabel(preset)}
                  selected={newPreset === preset}
                  onClick={() => setNewPreset(preset)}
                />
              ))}
            </div>
            <Button type="button" variant="secondary" onClick={addPresetRow}>
              Add {targetLabel(newPreset)}
            </Button>
          </div>
        ) : null}

        <FormStickyActions>
          <Button type="submit" loading={saving}>
            Save targets
          </Button>
        </FormStickyActions>
      </form>
    </SettingsPageShell>
  );
}
