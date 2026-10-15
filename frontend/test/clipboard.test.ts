import { afterEach, describe, expect, it, vi } from "vitest";
import { copyText } from "../src/clipboard";

type Doc = { execCommand?: unknown };

function stub(
  options: {
    secure?: boolean;
    writeText?: (text: string) => Promise<void>;
    exec?: (command: string) => boolean;
  } = {},
) {
  Object.defineProperty(window, "isSecureContext", {
    configurable: true,
    value: options.secure ?? true,
  });
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: options.writeText ? { writeText: options.writeText } : undefined,
  });
  if (options.exec) (document as Doc).execCommand = options.exec;
}

afterEach(() => {
  delete (window as { isSecureContext?: boolean }).isSecureContext;
  delete (navigator as { clipboard?: unknown }).clipboard;
  delete (document as Doc).execCommand;
  document.body.replaceChildren();
});

const textareas = (root: ParentNode = document) =>
  root.querySelectorAll("textarea");

describe("copyText", () => {
  it("uses the async clipboard in a secure context", async () => {
    const writeText = vi.fn(async () => undefined);
    const exec = vi.fn(() => true);
    stub({ writeText, exec });
    expect(await copyText("192.0.2.10")).toBe(true);
    expect(writeText).toHaveBeenCalledExactlyOnceWith("192.0.2.10");
    expect(exec).not.toHaveBeenCalled();
    expect(textareas()).toHaveLength(0);
  });

  it("selects a temporary textarea when the async clipboard is missing", async () => {
    let during: {
      value: string;
      selected: string;
      focused: boolean;
    } | null = null;
    const exec = vi.fn((command: string) => {
      const area = document.querySelector("textarea")!;
      during = {
        value: area.value,
        selected: area.value.slice(area.selectionStart, area.selectionEnd),
        focused: document.activeElement === area,
      };
      expect(command).toBe("copy");
      return true;
    });
    stub({ exec });
    expect(await copyText("aa:bb:cc:dd:ee:ff")).toBe(true);
    expect(during).toEqual({
      value: "aa:bb:cc:dd:ee:ff",
      selected: "aa:bb:cc:dd:ee:ff",
      focused: true,
    });
    expect(exec).toHaveBeenCalledOnce();
    expect(textareas()).toHaveLength(0);
  });

  it("uses writeText whenever the API exists", async () => {
    const writeText = vi.fn(async () => undefined);
    stub({ secure: false, writeText, exec: () => true });
    expect(await copyText("x")).toBe(true);
    expect(writeText).toHaveBeenCalledExactlyOnceWith("x");
  });

  it("falls back when the async clipboard rejects", async () => {
    const writeText = vi.fn(async () => {
      throw new DOMException("denied", "NotAllowedError");
    });
    const exec = vi.fn(() => true);
    stub({ writeText, exec });
    expect(await copyText("192.0.2.10")).toBe(true);
    expect(writeText).toHaveBeenCalledOnce();
    expect(exec).toHaveBeenCalledOnce();
    expect(textareas()).toHaveLength(0);
  });

  it("reports failure when both ways fail", async () => {
    const rejects = async () => {
      throw new Error("denied");
    };
    stub({ writeText: rejects, exec: () => false });
    expect(await copyText("x")).toBe(false);
    expect(textareas()).toHaveLength(0);
  });

  it("reports failure when the fallback throws or does not exist", async () => {
    stub({
      exec: () => {
        throw new Error("blocked");
      },
    });
    expect(await copyText("x")).toBe(false);
    expect(textareas()).toHaveLength(0);
    // jsdom (like a locked-down embedder) has no execCommand at all.
    stub();
    expect(await copyText("x")).toBe(false);
    expect(textareas()).toHaveLength(0);
  });

  it("puts the textarea inside the given host, which a modal dialog needs", async () => {
    const host = document.createElement("div");
    document.body.append(host);
    let inside = false;
    stub({
      exec: () => {
        inside = textareas(host).length === 1;
        return true;
      },
    });
    expect(await copyText("x", host)).toBe(true);
    expect(inside).toBe(true);
    expect(textareas()).toHaveLength(0);
  });

  it("gives focus back to a control inside a shadow root", async () => {
    const host = document.createElement("div");
    const inner = host.attachShadow({ mode: "open" });
    const button = document.createElement("button");
    inner.append(button);
    document.body.append(host);
    button.focus();
    expect(inner.activeElement).toBe(button);
    stub({ exec: () => true });
    await copyText("x", inner);
    expect(inner.activeElement).toBe(button);
  });

  it("gives focus back to the control that had it", async () => {
    const button = document.createElement("button");
    document.body.append(button);
    button.focus();
    stub({ exec: () => true });
    await copyText("x");
    expect(document.activeElement).toBe(button);
  });
});
