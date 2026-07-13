import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import {
  cancelCookingTimerAlert,
  cancelCookingTimerAlertForStep,
  scheduleCookingTimerAlert,
} from "../../api/cooking";
import {
  fetchDish,
  fetchIngredients,
  fetchRecipe,
  fetchRecipeIngredients,
  fetchRecipeSteps,
  fetchUnits,
  type Dish,
  type Recipe,
  type RecipeIngredient,
  type RecipeStep,
  type Unit,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { ButtonLink } from "../../components/ButtonLink";
import { Button, PageLoadingState, PageShell } from "../../components/ui";
import { useAuth } from "../auth/AuthContext";
import { CookingActiveTimersBar } from "./CookingActiveTimersBar";
import { CookingStepTimer } from "./CookingStepTimer";
import {
  primeCookingTimerAudio,
  requestCookingTimerNotificationPermission,
  startCookingTimerAlarm,
  stopCookingTimerAlarm,
} from "./cookingTimerAlarm";
import { useCookingStepTimers } from "./cookingStepTimers";
import {
  canGoNext,
  canGoPrevious,
  formatStepTimerLabel,
  nextStepIndex,
  previousStepIndex,
  sortRecipeSteps,
  stepTimerDurationSeconds,
} from "./recipeCooking";

function formatIngredientLine(
  item: RecipeIngredient,
  ingredientNames: Record<number, string>,
  units: Unit[],
): string {
  const name = ingredientNames[item.ingredient_id] ?? `ingredient #${item.ingredient_id}`;
  const unitSymbol = units.find((unit) => unit.id === item.unit_id)?.symbol;
  const quantity =
    item.quantity && unitSymbol ? `${item.quantity} ${unitSymbol}` : item.quantity ?? "";
  const optional = item.optional ? " (optional)" : "";
  return quantity ? `${name} — ${quantity}${optional}` : `${name}${optional}`;
}

export function RecipeCookingPage() {
  const { recipeId } = useParams();
  const recipeIdNum = Number(recipeId);
  const hasValidId = recipeId !== undefined && Number.isFinite(recipeIdNum) && recipeIdNum > 0;
  const { accessToken } = useAuth();

  const [dish, setDish] = useState<Dish | null>(null);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [steps, setSteps] = useState<RecipeStep[]>([]);
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([]);
  const [ingredientNames, setIngredientNames] = useState<Record<number, string>>({});
  const [units, setUnits] = useState<Unit[]>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const alarmStopRef = useRef<(() => void) | null>(null);
  const telegramAlertIdsRef = useRef<Record<number, number>>({});

  const orderedSteps = useMemo(() => sortRecipeSteps(steps), [steps]);
  const currentStep = orderedSteps[stepIndex] ?? null;
  const stepCount = orderedSteps.length;
  const currentStepTimerSeconds = currentStep ? stepTimerDurationSeconds(currentStep) : null;

  const handleTimerFinished = useCallback(
    (stepId: number) => {
      const step = orderedSteps.find((entry) => entry.id === stepId);
      const label = dish && step
        ? `Step ${step.step_number} — ${dish.name}${recipe ? ` (${recipe.variant_name})` : ""}`
        : undefined;
      alarmStopRef.current?.();
      alarmStopRef.current = startCookingTimerAlarm({ label });
    },
    [dish, orderedSteps, recipe],
  );

  const {
    timers,
    activeTimers,
    upsertTimer,
    startTimer,
    pauseTimer,
    resetTimer,
    dismissTimer,
  } = useCookingStepTimers(handleTimerFinished);
  const timersRef = useRef(timers);
  timersRef.current = timers;

  const cancelTelegramForStep = useCallback(
    async (stepId: number) => {
      if (!accessToken) {
        return;
      }
      const alertId = telegramAlertIdsRef.current[stepId];
      try {
        if (alertId) {
          await cancelCookingTimerAlert(accessToken, alertId);
        } else {
          await cancelCookingTimerAlertForStep(accessToken, stepId);
        }
      } catch {
        // Local timer still works when Telegram is unavailable.
      }
      delete telegramAlertIdsRef.current[stepId];
    },
    [accessToken],
  );

  const scheduleTelegramForStep = useCallback(
    async (stepId: number, remainingSeconds: number) => {
      if (!accessToken || !recipe || remainingSeconds < 1) {
        return;
      }
      const step = orderedSteps.find((entry) => entry.id === stepId);
      if (!step) {
        return;
      }
      try {
        await cancelTelegramForStep(stepId);
        const alert = await scheduleCookingTimerAlert(accessToken, {
          recipe_id: recipe.id,
          recipe_step_id: stepId,
          step_number: step.step_number,
          remaining_seconds: remainingSeconds,
        });
        const liveTimer = timersRef.current[stepId];
        const stillRunning =
          liveTimer?.running === true && !liveTimer.finished && !liveTimer.acknowledged;
        if (!stillRunning) {
          if (alert.telegram_scheduled) {
            await cancelCookingTimerAlert(accessToken, alert.id);
          }
          return;
        }
        if (alert.telegram_scheduled) {
          telegramAlertIdsRef.current[stepId] = alert.id;
        }
      } catch {
        // Local timer still works when Telegram is unavailable.
      }
    },
    [accessToken, cancelTelegramForStep, orderedSteps, recipe],
  );

  const handleStartTimer = useCallback(
    (stepId: number) => {
      const timer = timers[stepId];
      if (!timer) {
        return;
      }
      primeCookingTimerAudio();
      void requestCookingTimerNotificationPermission();
      startTimer(stepId);
      void scheduleTelegramForStep(stepId, timer.remainingSeconds);
    },
    [scheduleTelegramForStep, startTimer, timers],
  );

  const handlePauseTimer = useCallback(
    (stepId: number) => {
      pauseTimer(stepId);
      void cancelTelegramForStep(stepId);
    },
    [cancelTelegramForStep, pauseTimer],
  );

  const handleResetTimer = useCallback(
    (stepId: number) => {
      resetTimer(stepId);
      void cancelTelegramForStep(stepId);
    },
    [cancelTelegramForStep, resetTimer],
  );

  const handleDismissTimer = useCallback(
    (stepId: number) => {
      dismissTimer(stepId);
      void cancelTelegramForStep(stepId);
    },
    [cancelTelegramForStep, dismissTimer],
  );

  useEffect(() => {
    const hasFinishedAlarm = Object.values(timers).some((timer) => timer.finished && !timer.acknowledged);
    if (!hasFinishedAlarm) {
      alarmStopRef.current?.();
      alarmStopRef.current = null;
      stopCookingTimerAlarm();
    }
  }, [timers]);

  useEffect(() => {
    return () => {
      stopCookingTimerAlarm();
      const stepIds = Object.keys(telegramAlertIdsRef.current);
      if (!accessToken) {
        return;
      }
      for (const stepId of stepIds) {
        void cancelCookingTimerAlertForStep(accessToken, Number(stepId));
      }
    };
  }, [accessToken]);

  const load = useCallback(async () => {
    if (!accessToken || !hasValidId) {
      return;
    }
    setLoading(true);
    try {
      const recipeData = await fetchRecipe(accessToken, recipeIdNum);
      const [dishData, stepData, ingredientData, unitData, allIngredients] = await Promise.all([
        fetchDish(accessToken, recipeData.dish_id),
        fetchRecipeSteps(accessToken, recipeIdNum),
        fetchRecipeIngredients(accessToken, recipeIdNum),
        fetchUnits(accessToken),
        fetchIngredients(accessToken),
      ]);
      const names: Record<number, string> = {};
      for (const item of allIngredients) {
        names[item.id] = item.display_name;
      }
      setRecipe(recipeData);
      setDish(dishData);
      setSteps(stepData);
      setIngredients(ingredientData);
      setUnits(unitData);
      setIngredientNames(names);
      setStepIndex(0);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load recipe for cooking");
    } finally {
      setLoading(false);
    }
  }, [accessToken, hasValidId, recipeIdNum]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (currentStep && currentStepTimerSeconds) {
      upsertTimer(currentStep, currentStepTimerSeconds);
    }
  }, [currentStep, currentStepTimerSeconds, upsertTimer]);

  const currentTimer =
    currentStep && currentStepTimerSeconds ? (timers[currentStep.id] ?? null) : null;

  if (!hasValidId) {
    return (
      <section className="cooking-mode">
        <p className="error" role="alert">
          Invalid recipe
        </p>
      </section>
    );
  }

  if (loading) {
    return <PageLoadingState message="Loading cooking mode…" />;
  }

  if (error || !recipe || !dish) {
    return (
      <section className="cooking-mode">
        <p className="error" role="alert">
          {error ?? "Recipe not found"}
        </p>
        <ButtonLink to="/dishes" variant="secondary">
          Back to dishes
        </ButtonLink>
      </section>
    );
  }

  const recipeDetailPath = `/dishes/${dish.id}/recipes/${recipe.id}`;

  return (
    <section className="cooking-mode stack">
      <PageShell
        title="Cook"
        subtitle={`${dish.name} · ${recipe.variant_name}`}
        breadcrumbLabels={{ dishId: dish.id, dishName: dish.name }}
        actions={
          <ButtonLink to={recipeDetailPath} variant="secondary" className="cooking-mode-exit">
            Exit
          </ButtonLink>
        }
      />

      <CookingActiveTimersBar
        timers={activeTimers}
        currentStepId={currentStep?.id ?? null}
        onStart={handleStartTimer}
        onPause={handlePauseTimer}
        onReset={handleResetTimer}
        onDismiss={handleDismissTimer}
      />

      <details className="cooking-mode-ingredients">
        <summary>Ingredients ({ingredients.length})</summary>
        {ingredients.length === 0 ? (
          <p className="muted">No ingredients listed.</p>
        ) : (
          <ul className="cooking-mode-ingredient-list">
            {ingredients.map((item) => (
              <li key={item.id}>{formatIngredientLine(item, ingredientNames, units)}</li>
            ))}
          </ul>
        )}
      </details>

      <div className="cooking-mode-step-panel" aria-live="polite">
        {stepCount === 0 ? (
          <>
            <p className="cooking-mode-step-counter">No steps</p>
            <p className="muted">This recipe has no steps yet. Add steps on the recipe detail page.</p>
          </>
        ) : (
          <>
            <p className="cooking-mode-step-counter">
              Step {stepIndex + 1} of {stepCount}
            </p>
            {currentStepTimerSeconds ? (
              <p className="cooking-mode-step-meta muted">{formatStepTimerLabel(currentStepTimerSeconds)}</p>
            ) : null}
            <p className="cooking-mode-instruction">{currentStep?.instruction}</p>
            {currentStep && currentStepTimerSeconds && currentTimer ? (
              <CookingStepTimer
                timer={currentTimer}
                onStart={() => handleStartTimer(currentStep.id)}
                onPause={() => handlePauseTimer(currentStep.id)}
                onReset={() => handleResetTimer(currentStep.id)}
                onDismiss={() => handleDismissTimer(currentStep.id)}
              />
            ) : null}
          </>
        )}
      </div>

      <footer className="cooking-mode-controls">
        <Button
          type="button"
          variant="secondary"
          size="lg"
          disabled={!canGoPrevious(stepIndex)}
          onClick={() => setStepIndex((index) => previousStepIndex(index))}
        >
          Previous
        </Button>
        <Button
          type="button"
          size="lg"
          disabled={!canGoNext(stepIndex, stepCount)}
          onClick={() => setStepIndex((index) => nextStepIndex(index, stepCount))}
        >
          Next step
        </Button>
      </footer>
    </section>
  );
}
