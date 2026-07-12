import type { RecipeStep } from "../../api/catalog";

export function sortRecipeSteps(steps: RecipeStep[]): RecipeStep[] {
  return [...steps].sort((left, right) => left.step_number - right.step_number);
}

export function canGoPrevious(stepIndex: number): boolean {
  return stepIndex > 0;
}

export function canGoNext(stepIndex: number, stepCount: number): boolean {
  return stepCount > 0 && stepIndex < stepCount - 1;
}

export function previousStepIndex(stepIndex: number): number {
  return canGoPrevious(stepIndex) ? stepIndex - 1 : stepIndex;
}

export function nextStepIndex(stepIndex: number, stepCount: number): number {
  return canGoNext(stepIndex, stepCount) ? stepIndex + 1 : stepIndex;
}

/** Prefer explicit timer; fall back to duration (same rule as Telegram recipe formatting). */
export function stepTimerDurationSeconds(step: RecipeStep): number | null {
  if (step.timer_seconds != null && step.timer_seconds > 0) {
    return step.timer_seconds;
  }
  if (step.duration_seconds != null && step.duration_seconds > 0) {
    return step.duration_seconds;
  }
  return null;
}

export function formatTimerDisplay(totalSeconds: number): string {
  const clamped = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(clamped / 60);
  const seconds = clamped % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function formatStepTimerLabel(totalSeconds: number): string {
  const minutes = Math.max(1, Math.round(totalSeconds / 60));
  return `${minutes} min timer`;
}

export function timerMinutesFromSeconds(seconds: number | null): string {
  if (seconds == null || seconds <= 0) {
    return "";
  }
  return String(Math.round(seconds / 60));
}

export function timerSecondsFromMinutesInput(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const minutes = Number(trimmed);
  if (!Number.isFinite(minutes) || minutes <= 0) {
    return null;
  }
  return Math.round(minutes * 60);
}
