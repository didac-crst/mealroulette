import { describe, expect, it } from "vitest";

import {
  canGoNext,
  canGoPrevious,
  formatStepTimerLabel,
  formatTimerDisplay,
  nextStepIndex,
  previousStepIndex,
  sortRecipeSteps,
  stepTimerDurationSeconds,
  timerMinutesFromSeconds,
  timerSecondsFromMinutesInput,
} from "./recipeCooking";

describe("recipeCooking helpers", () => {
  it("sorts steps by step_number", () => {
    const sorted = sortRecipeSteps([
      { id: 2, recipe_id: 1, step_number: 2, instruction: "b", duration_seconds: null, temperature: null, timer_seconds: null, is_thermomix_step: false },
      { id: 1, recipe_id: 1, step_number: 1, instruction: "a", duration_seconds: null, temperature: null, timer_seconds: null, is_thermomix_step: false },
    ]);
    expect(sorted.map((step) => step.step_number)).toEqual([1, 2]);
  });

  it("blocks previous at first step and next at last step", () => {
    expect(canGoPrevious(0)).toBe(false);
    expect(canGoNext(0, 3)).toBe(true);
    expect(canGoNext(2, 3)).toBe(false);
    expect(nextStepIndex(2, 3)).toBe(2);
    expect(previousStepIndex(0)).toBe(0);
  });

  it("resolves timer duration and formats display", () => {
    const step = {
      id: 1,
      recipe_id: 1,
      step_number: 1,
      instruction: "Simmer",
      duration_seconds: 120,
      temperature: null,
      timer_seconds: 300,
      is_thermomix_step: false,
    };
    expect(stepTimerDurationSeconds(step)).toBe(300);
    expect(stepTimerDurationSeconds({ ...step, timer_seconds: null })).toBe(120);
    expect(formatTimerDisplay(125)).toBe("2:05");
    expect(formatStepTimerLabel(300)).toBe("5 min timer");
    expect(timerMinutesFromSeconds(300)).toBe("5");
    expect(timerSecondsFromMinutesInput("5")).toBe(300);
    expect(timerSecondsFromMinutesInput("")).toBeNull();
  });
});
