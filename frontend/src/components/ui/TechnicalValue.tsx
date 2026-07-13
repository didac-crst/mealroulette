import { useId, useState } from "react";

export type TechnicalValueProps = {
  label: string;
  value: string;
  className?: string;
  copyLabel?: string;
};

export function TechnicalValue({ label, value, className, copyLabel = "Copy" }: TechnicalValueProps) {
  const id = useId();
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className={["technical-value", className].filter(Boolean).join(" ")}>
      <span className="technical-value-label" id={id}>
        {label}
      </span>
      <div className="technical-value-field" role="group" aria-labelledby={id}>
        <code className="technical-value-code">{value}</code>
        <button type="button" className="technical-value-copy" onClick={() => void handleCopy()} aria-label={`Copy ${label}`}>
          {copied ? "Copied" : copyLabel}
        </button>
      </div>
    </div>
  );
}

