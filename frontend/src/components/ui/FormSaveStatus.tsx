export type FormSaveStatusState = "idle" | "unsaved" | "saving" | "saved" | "error";

export type FormSaveStatusProps = {
  status: FormSaveStatusState;
  errorMessage?: string | null;
  className?: string;
};

const STATUS_LABEL: Record<Exclude<FormSaveStatusState, "idle" | "error">, string> = {
  unsaved: "Unsaved changes",
  saving: "Saving…",
  saved: "Saved",
};

export function FormSaveStatus({ status, errorMessage, className }: FormSaveStatusProps) {
  if (status === "idle") {
    return null;
  }

  const label = status === "error" ? (errorMessage ?? "Could not save") : STATUS_LABEL[status];

  return (
    <p
      className={["form-save-status", `form-save-status-${status}`, className].filter(Boolean).join(" ")}
      role={status === "error" ? "alert" : "status"}
      aria-live={status === "error" ? undefined : "polite"}
    >
      {label}
    </p>
  );
}
