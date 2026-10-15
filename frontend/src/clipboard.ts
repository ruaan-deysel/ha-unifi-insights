/** The element holding focus, looking through open shadow roots. */
function deepActiveElement(): HTMLElement | null {
  let active = document.activeElement;
  while (active?.shadowRoot?.activeElement)
    active = active.shadowRoot.activeElement;
  return active instanceof HTMLElement ? active : null;
}

/**
 * The textarea way: select a hidden field and run the copy command. `host`
 * must sit inside an open modal dialog when there is one, because everything
 * outside a modal dialog is inert and cannot take focus or a selection.
 */
function copyWithSelection(text: string, host: ParentNode): boolean {
  const previous = deepActiveElement();
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.setAttribute("aria-hidden", "true");
  area.style.cssText =
    "position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;pointer-events:none";
  host.append(area);
  try {
    area.focus();
    area.select();
    return (
      typeof document.execCommand === "function" && document.execCommand("copy")
    );
  } catch {
    return false;
  } finally {
    area.remove();
    previous?.focus();
  }
}

/**
 * Copy text to the clipboard. Uses the async clipboard API when available
 * and a temporary textarea otherwise, or when the API refuses.
 * Resolves to whether the text was copied; it never rejects.
 */
export async function copyText(
  text: string,
  host: ParentNode = document.body,
): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Denied (for instance a document without focus): try the fallback.
    }
  }
  return copyWithSelection(text, host);
}
