export type CookingTimerAlarmOptions = {
  label?: string;
};

let audioContext: AudioContext | null = null;
let activeAlarmStop: (() => void) | null = null;

export function primeCookingTimerAudio(): void {
  if (typeof window === "undefined") {
    return;
  }
  if (!audioContext) {
    const AudioContextClass = window.AudioContext ?? (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) {
      return;
    }
    audioContext = new AudioContextClass();
  }
  void audioContext.resume();
}

export async function requestCookingTimerNotificationPermission(): Promise<void> {
  if (typeof window === "undefined" || typeof Notification === "undefined") {
    return;
  }
  if (Notification.permission === "default") {
    try {
      await Notification.requestPermission();
    } catch {
      // Ignore denied or unsupported notification permission.
    }
  }
}

function playTone(
  frequency: number,
  durationMs: number,
  peakVolume: number,
  delayMs: number,
): void {
  if (!audioContext) {
    return;
  }
  window.setTimeout(() => {
    if (!audioContext) {
      return;
    }
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    oscillator.connect(gain);
    gain.connect(audioContext.destination);

    const startAt = audioContext.currentTime;
    const durationSec = durationMs / 1000;
    gain.gain.setValueAtTime(0.001, startAt);
    gain.gain.exponentialRampToValueAtTime(peakVolume, startAt + 0.04);
    gain.gain.exponentialRampToValueAtTime(0.001, startAt + durationSec);

    oscillator.start(startAt);
    oscillator.stop(startAt + durationSec + 0.05);
  }, delayMs);
}

/** Gentle ascending chime — C5 → E5 → G5 */
function playChime(): void {
  playTone(523.25, 420, 0.28, 0);
  playTone(659.25, 420, 0.24, 180);
  playTone(783.99, 560, 0.2, 360);
}

function vibrateBurst(): void {
  if (typeof navigator !== "undefined" && navigator.vibrate) {
    navigator.vibrate([180, 80, 180]);
  }
}

function showNotification(label: string | undefined): void {
  if (typeof window === "undefined" || typeof Notification === "undefined") {
    return;
  }
  if (Notification.permission !== "granted") {
    return;
  }
  const body = label ?? "Your step timer is ready.";
  new Notification("Timer ready", { body, tag: "mealroulette-cooking-timer" });
}

export function stopCookingTimerAlarm(): void {
  activeAlarmStop?.();
  activeAlarmStop = null;
}

export function startCookingTimerAlarm(options: CookingTimerAlarmOptions = {}): () => void {
  stopCookingTimerAlarm();
  primeCookingTimerAudio();
  playChime();
  vibrateBurst();
  showNotification(options.label);

  let cancelled = false;
  const intervalId = window.setInterval(() => {
    if (cancelled) {
      return;
    }
    playChime();
    vibrateBurst();
  }, 4000);

  const stop = () => {
    if (cancelled) {
      return;
    }
    cancelled = true;
    window.clearInterval(intervalId);
    if (activeAlarmStop === stop) {
      activeAlarmStop = null;
    }
  };

  activeAlarmStop = stop;
  return stop;
}
