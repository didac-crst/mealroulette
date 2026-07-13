import type { ReactNode } from "react";

import { useDialogA11y } from "../../lib/useDialogA11y";

export type BottomSheetProps = {
  open: boolean;
  titleId: string;
  onClose: () => void;
  children: ReactNode;
  className?: string;
};

export function BottomSheet({ open, titleId, onClose, children, className }: BottomSheetProps) {
  const dialogRef = useDialogA11y(open, onClose);

  if (!open) {
    return null;
  }

  return (
    <div className="bottom-sheet-backdrop" role="presentation" onClick={onClose}>
      <div
        ref={dialogRef}
        className={["bottom-sheet", className].filter(Boolean).join(" ")}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="bottom-sheet-handle" aria-hidden />
        {children}
      </div>
    </div>
  );
}
