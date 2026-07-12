import { CookingStepTimer } from "./CookingStepTimer";
import type { CookingTimerState } from "./cookingStepTimers";

type Props = {
  timers: CookingTimerState[];
  currentStepId: number | null;
  onStart: (stepId: number) => void;
  onPause: (stepId: number) => void;
  onReset: (stepId: number) => void;
  onDismiss: (stepId: number) => void;
};

export function CookingActiveTimersBar({
  timers,
  currentStepId,
  onStart,
  onPause,
  onReset,
  onDismiss,
}: Props) {
  const backgroundTimers = timers.filter((timer) => timer.stepId !== currentStepId);
  if (backgroundTimers.length === 0) {
    return null;
  }

  return (
    <aside className="cooking-active-timers" aria-label="Active cooking timers">
      <p className="cooking-active-timers-title">Running timers</p>
      {backgroundTimers.map((timer) => (
        <CookingStepTimer
          key={timer.stepId}
          timer={timer}
          compact
          onStart={() => onStart(timer.stepId)}
          onPause={() => onPause(timer.stepId)}
          onReset={() => onReset(timer.stepId)}
          onDismiss={() => onDismiss(timer.stepId)}
        />
      ))}
    </aside>
  );
}
