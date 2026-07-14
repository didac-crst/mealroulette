import { useCallback, useEffect, useRef, useState } from "react";

import type { FormSaveStatusState } from "../components/ui/FormSaveStatus";

type UseFormSaveStateOptions = {
  saving: boolean;
  error: string | null;
};

export function useFormSaveState<T>(form: T, { saving, error }: UseFormSaveStateOptions) {
  const baselineRef = useRef<string | null>(null);
  const [savedPulse, setSavedPulse] = useState(false);

  const setBaseline = useCallback((value: T) => {
    baselineRef.current = JSON.stringify(value);
    setSavedPulse(false);
  }, []);

  const markSaved = useCallback((value: T) => {
    baselineRef.current = JSON.stringify(value);
    setSavedPulse(true);
  }, []);

  const isDirty =
    baselineRef.current !== null && JSON.stringify(form) !== baselineRef.current;

  useEffect(() => {
    if (!savedPulse) {
      return;
    }
    const timeout = window.setTimeout(() => setSavedPulse(false), 2500);
    return () => window.clearTimeout(timeout);
  }, [savedPulse]);

  let status: FormSaveStatusState = "idle";
  if (error) {
    status = "error";
  } else if (saving) {
    status = "saving";
  } else if (savedPulse) {
    status = "saved";
  } else if (isDirty) {
    status = "unsaved";
  }

  return { status, setBaseline, markSaved, isDirty };
}
