import { afterEach, describe, expect, it, vi } from "vitest";

import { copyTextToClipboard } from "./copyTextToClipboard";

describe("copyTextToClipboard", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns false for empty text", async () => {
    await expect(copyTextToClipboard("")).resolves.toBe(false);
  });

  it("uses navigator.clipboard in secure contexts", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    vi.stubGlobal("window", { isSecureContext: true });

    await expect(copyTextToClipboard("abc-123")).resolves.toBe(true);
    expect(writeText).toHaveBeenCalledWith("abc-123");
  });

  it("prefers execCommand before clipboard API", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(true);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    vi.stubGlobal("window", { isSecureContext: true });
    vi.stubGlobal("document", {
      body: {
        appendChild: vi.fn(),
        removeChild: vi.fn(),
      },
      createElement: vi.fn(() => ({
        value: "",
        style: {},
        focus: vi.fn(),
        select: vi.fn(),
        setSelectionRange: vi.fn(),
        setAttribute: vi.fn(),
      })),
      execCommand,
      getSelection: vi.fn(() => null),
    });

    await expect(copyTextToClipboard("abc-123")).resolves.toBe(true);
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(writeText).not.toHaveBeenCalled();
  });

  it("falls back to clipboard API when execCommand fails", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const execCommand = vi.fn().mockReturnValue(false);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    vi.stubGlobal("window", { isSecureContext: true });
    vi.stubGlobal("document", {
      body: {
        appendChild: vi.fn(),
        removeChild: vi.fn(),
      },
      createElement: vi.fn(() => ({
        value: "",
        style: {},
        focus: vi.fn(),
        select: vi.fn(),
        setSelectionRange: vi.fn(),
        setAttribute: vi.fn(),
      })),
      execCommand,
      getSelection: vi.fn(() => null),
    });

    await expect(copyTextToClipboard("abc-123")).resolves.toBe(true);
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(writeText).toHaveBeenCalledWith("abc-123");
  });
});
