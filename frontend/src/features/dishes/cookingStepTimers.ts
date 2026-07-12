import { useCallback, useEffect, useRef, useState } from "react";

import type { RecipeStep } from "../../api/catalog";

export type CookingTimerState = {
  stepId: number;
  stepNumber: number;
  durationSeconds: number;
  remainingSeconds: number;
  running: boolean;
  finished: boolean;
  acknowledged: boolean;
};

export function createCookingTimerState(step: RecipeStep, durationSeconds: number): CookingTimerState {
  return {
    stepId: step.id,
    stepNumber: step.step_number,
    durationSeconds,
    remainingSeconds: durationSeconds,
    running: false,
    finished: false,
    acknowledged: false,
  };
}

export type CookingTimerPhase = "idle" | "running" | "paused" | "ready" | "acknowledged";

export function cookingTimerPhase(timer: CookingTimerState): CookingTimerPhase {
  if (timer.acknowledged) {
    return "acknowledged";
  }
  if (timer.finished) {
    return "ready";
  }
  if (timer.running) {
    return "running";
  }
  if (timer.remainingSeconds < timer.durationSeconds) {
    return "paused";
  }
  return "idle";
}

export function tickCookingTimers(
  timers: Record<number, CookingTimerState>,
): { timers: Record<number, CookingTimerState>; finishedStepIds: number[] } | null {
  let changed = false;
  const finishedStepIds: number[] = [];
  const next: Record<number, CookingTimerState> = { ...timers };
  for (const [key, timer] of Object.entries(timers)) {
    if (!timer.running || timer.finished) {
      continue;
    }
    changed = true;
    const stepId = Number(key);
    if (timer.remainingSeconds <= 1) {
      next[stepId] = { ...timer, remainingSeconds: 0, running: false, finished: true };
      finishedStepIds.push(stepId);
    } else {
      next[stepId] = { ...timer, remainingSeconds: timer.remainingSeconds - 1 };
    }
  }
  if (!changed) {
    return null;
  }
  return { timers: next, finishedStepIds };
}

export function visibleActiveTimers(timers: Record<number, CookingTimerState>): CookingTimerState[] {
  return Object.values(timers)
    .filter(
      (timer) =>
        !timer.acknowledged &&
        (timer.running || timer.finished || timer.remainingSeconds < timer.durationSeconds),
    )
    .sort((left, right) => left.stepNumber - right.stepNumber);
}

export function hasRunningCookingTimers(timers: Record<number, CookingTimerState>): boolean {
  return Object.values(timers).some((timer) => timer.running && !timer.finished);
}

export function useCookingStepTimers(onTimerFinished?: (stepId: number) => void) {
  const [timers, setTimers] = useState<Record<number, CookingTimerState>>({});
  const timersRef = useRef(timers);
  timersRef.current = timers;
  const onTimerFinishedRef = useRef(onTimerFinished);
  onTimerFinishedRef.current = onTimerFinished;

  useEffect(() => {
    const timerId = window.setInterval(() => {
      if (!hasRunningCookingTimers(timersRef.current)) {
        return;
      }
      const ticked = tickCookingTimers(timersRef.current);
      if (!ticked) {
        return;
      }
      timersRef.current = ticked.timers;
      setTimers(ticked.timers);
      for (const stepId of ticked.finishedStepIds) {
        onTimerFinishedRef.current?.(stepId);
      }
    }, 1000);
    return () => window.clearInterval(timerId);
  }, []);

  const upsertTimer = useCallback((step: RecipeStep, durationSeconds: number) => {
    setTimers((current) => {
      if (current[step.id]) {
        return current;
      }
      return { ...current, [step.id]: createCookingTimerState(step, durationSeconds) };
    });
  }, []);

  const startTimer = useCallback((stepId: number) => {
    setTimers((current) => {
      const timer = current[stepId];
      if (!timer || timer.finished || timer.acknowledged) {
        return current;
      }
      return { ...current, [stepId]: { ...timer, running: true } };
    });
  }, []);

  const pauseTimer = useCallback((stepId: number) => {
    setTimers((current) => {
      const timer = current[stepId];
      if (!timer) {
        return current;
      }
      return { ...current, [stepId]: { ...timer, running: false } };
    });
  }, []);

  const resetTimer = useCallback((stepId: number) => {
    setTimers((current) => {
      const timer = current[stepId];
      if (!timer) {
        return current;
      }
      return {
        ...current,
        [stepId]: {
          ...timer,
          remainingSeconds: timer.durationSeconds,
          running: false,
          finished: false,
          acknowledged: false,
        },
      };
    });
  }, []);

  const dismissTimer = useCallback((stepId: number) => {
    setTimers((current) => {
      const timer = current[stepId];
      if (!timer || timer.acknowledged) {
        return current;
      }
      if (!timer.finished && timer.remainingSeconds > 0) {
        return current;
      }
      return {
        ...current,
        [stepId]: {
          ...timer,
          running: false,
          finished: false,
          acknowledged: true,
          remainingSeconds: 0,
        },
      };
    });
  }, []);

  const getTimer = useCallback(
    (stepId: number | undefined) => (stepId != null ? timers[stepId] ?? null : null),
    [timers],
  );

  return {
    timers,
    activeTimers: visibleActiveTimers(timers),
    upsertTimer,
    startTimer,
    pauseTimer,
    resetTimer,
    dismissTimer,
    getTimer,
  };
}
