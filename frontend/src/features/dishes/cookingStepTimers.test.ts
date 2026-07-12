import { describe, expect, it } from "vitest";

import {
  cookingTimerPhase,
  createCookingTimerState,
  tickCookingTimers,
  visibleActiveTimers,
} from "./cookingStepTimers";

const step = {
  id: 10,
  recipe_id: 1,
  step_number: 2,
  instruction: "Simmer",
  duration_seconds: null,
  temperature: null,
  timer_seconds: 120,
  is_thermomix_step: false,
};

describe("cookingStepTimers", () => {
  it("ticks running timers to finished", () => {
    const timers = {
      10: { ...createCookingTimerState(step, 120), running: true, remainingSeconds: 1 },
    };
    const next = tickCookingTimers(timers);
    expect(next?.finishedStepIds).toEqual([10]);
    expect(next?.timers[10].finished).toBe(true);
  });

  it("shows started timers in the active list", () => {
    const fresh = createCookingTimerState(step, 120);
    expect(visibleActiveTimers({ 10: fresh })).toEqual([]);
    expect(
      visibleActiveTimers({
        10: { ...fresh, running: true, remainingSeconds: 90 },
      }),
    ).toHaveLength(1);
  });

  it("hides acknowledged timers from the active bar", () => {
    const fresh = createCookingTimerState(step, 120);
    expect(
      visibleActiveTimers({
        10: { ...fresh, finished: true, acknowledged: true, remainingSeconds: 0 },
      }),
    ).toEqual([]);
  });

  it("derives timer phases for button states", () => {
    const fresh = createCookingTimerState(step, 120);
    expect(cookingTimerPhase(fresh)).toBe("idle");
    expect(cookingTimerPhase({ ...fresh, running: true })).toBe("running");
    expect(cookingTimerPhase({ ...fresh, remainingSeconds: 90 })).toBe("paused");
    expect(cookingTimerPhase({ ...fresh, finished: true, remainingSeconds: 0 })).toBe("ready");
    expect(
      cookingTimerPhase({ ...fresh, finished: true, acknowledged: true, remainingSeconds: 0 }),
    ).toBe("acknowledged");
  });
});
