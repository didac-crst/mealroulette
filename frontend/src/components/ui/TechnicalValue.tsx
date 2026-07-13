import { useId, useState } from "react";

import { copyTextToClipboard } from "../../lib/copyTextToClipboard";

export type TechnicalValueProps = {
  label: string;
  value: string;
  className?: string;
  copyLabel?: string;
};

export function TechnicalValue({ label, value, className, copyLabel = "Copy" }: TechnicalValueProps) {
  const id = useId();
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  async function handleCopy() {
    const copied = await copyTextToClipboard(value);
    setCopyState(copied ? "copied" : "failed");
    window.setTimeout(() => setCopyState("idle"), copied ? 1200 : 1800);
  }

  const copyButtonLabel = copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : copyLabel;

  return (
    <div className={["technical-value", className].filter(Boolean).join(" ")}>
      <span className="technical-value-label" id={id}>
        {label}
      </span>
      <div className="technical-value-field" role="group" aria-labelledby={id}>
        <code className="technical-value-code">{value}</code>
        <button
          type="button"
          className={`technical-value-copy${copyState === "failed" ? " technical-value-copy-failed" : ""}`}
          onClick={() => void handleCopy()}
          aria-label={`Copy ${label}`}
        >
          {copyButtonLabel}
        </button>
      </div>
    </div>
  );
}

