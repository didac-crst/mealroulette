import type { ReactNode } from "react";

import { FormSaveStatus, type FormSaveStatusState } from "./FormSaveStatus";

export type FormStickyActionsProps = {
  children: ReactNode;
  className?: string;
  saveStatus?: FormSaveStatusState;
  saveErrorMessage?: string | null;
};

export function FormStickyActions({
  children,
  className,
  saveStatus,
  saveErrorMessage,
}: FormStickyActionsProps) {
  return (
    <div className={["form-sticky-actions", className].filter(Boolean).join(" ")}>
      <div className="form-sticky-actions-buttons">{children}</div>
      {saveStatus ? <FormSaveStatus status={saveStatus} errorMessage={saveErrorMessage} /> : null}
    </div>
  );
}
