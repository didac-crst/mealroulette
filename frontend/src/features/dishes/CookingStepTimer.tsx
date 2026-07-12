import { cookingTimerPhase } from "./cookingStepTimers";
import type { CookingTimerState } from "./cookingStepTimers";
import { formatTimerDisplay } from "./recipeCooking";

type Props = {
  timer: CookingTimerState;
  compact?: boolean;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onDismiss?: () => void;
};

export function CookingStepTimer({
  timer,
  compact = false,
  onStart,
  onPause,
  onReset,
  onDismiss,
}: Props) {
  const phase = cookingTimerPhase(timer);
  const showReady = phase === "ready";
  const showAcknowledged = phase === "acknowledged";
  const showReset = phase !== "idle";

  if (compact) {
    return (
      <div
        className={`cooking-active-timer-row${showReady ? " cooking-mode-timer-finished" : ""}${showAcknowledged ? " cooking-mode-timer-acknowledged" : ""}`}
      >
        <div>
          <p className="cooking-active-timer-label">Step {timer.stepNumber}</p>
          <p className="cooking-active-timer-time">{formatTimerDisplay(timer.remainingSeconds)}</p>
          {showReady ? <p className="cooking-mode-timer-done">Ready!</p> : null}
        </div>
        <div className="cooking-mode-timer-actions">
          {phase === "running" ? (
            <button type="button" className="button button-secondary" onClick={onPause}>
              Pause
            </button>
          ) : null}
          {phase === "paused" ? (
            <button type="button" className="button button-secondary" onClick={onStart}>
              Resume
            </button>
          ) : null}
          {showReset ? (
            <button type="button" className="button button-secondary" onClick={onReset}>
              Reset
            </button>
          ) : null}
          {showReady && onDismiss ? (
            <button type="button" className="button button-secondary" onClick={onDismiss}>
              Dismiss
            </button>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`cooking-mode-timer${showReady ? " cooking-mode-timer-finished" : ""}${showAcknowledged ? " cooking-mode-timer-acknowledged" : ""}`}
      aria-live="assertive"
    >
      <p className="cooking-mode-timer-display">{formatTimerDisplay(timer.remainingSeconds)}</p>
      {showReady ? <p className="cooking-mode-timer-done">Ready!</p> : null}
      <div className="cooking-mode-timer-actions">
        {phase === "idle" ? (
          <button type="button" className="button" onClick={onStart}>
            Start timer
          </button>
        ) : null}
        {phase === "running" ? (
          <button type="button" className="button button-secondary" onClick={onPause}>
            Pause
          </button>
        ) : null}
        {phase === "paused" ? (
          <button type="button" className="button button-secondary" onClick={onStart}>
            Resume
          </button>
        ) : null}
        {showReset ? (
          <button type="button" className="button button-secondary" onClick={onReset}>
            Reset
          </button>
        ) : null}
        {showReady && onDismiss ? (
          <button type="button" className="button button-secondary" onClick={onDismiss}>
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}
