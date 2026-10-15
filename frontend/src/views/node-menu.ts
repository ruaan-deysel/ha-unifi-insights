import {
  LitElement,
  html,
  nothing,
  type PropertyValues,
  type TemplateResult,
} from "lit";
import { repeat } from "lit/directives/repeat.js";
import type { NodeAction } from "../data/node-details";
import { defineOnce } from "../define";
import { fireEvent } from "../ha-types";
import {
  iconTemplate,
  mdiContentCopy,
  mdiDotsVertical,
  mdiInformationOutline,
  mdiOpenInNew,
} from "../icons";
import type { LocalizeFunc, LocalizeKey } from "../localize";
import { controlStyles, menuStyles, themeTokens } from "../styles";

const ACTION_KEYS: Record<NodeAction, LocalizeKey> = {
  copy_ip: "menu.copy_ip",
  copy_mac: "menu.copy_mac",
  open_device: "detail.open_device",
  open_entity: "menu.open_entity",
};

const ACTION_ICONS: Record<NodeAction, string> = {
  copy_ip: mdiContentCopy,
  copy_mac: mdiContentCopy,
  open_device: mdiOpenInNew,
  open_entity: mdiInformationOutline,
};

let menuCount = 0;

/**
 * A button that opens a keyboard-operable menu of node actions.
 *
 * It lives inline in the detail panel, not in a popover or portal, so that it
 * also works inside the panel's native modal dialog (everything outside a modal
 * dialog is inert). The component only chooses; the host performs the action
 * when it hears `uit-action`.
 */
export class UitNodeMenu extends LitElement {
  static override properties = {
    actions: { attribute: false },
    localize: { attribute: false },
    open: { state: true },
  };

  declare actions: NodeAction[];
  declare localize?: LocalizeFunc;
  declare open: boolean;

  private readonly menuId = `uit-node-menu-${++menuCount}`;
  private listening = false;
  private tabClose: ReturnType<typeof setTimeout> | undefined;

  constructor() {
    super();
    this.actions = [];
    this.open = false;
  }

  private get trigger(): HTMLButtonElement | null {
    return this.renderRoot.querySelector<HTMLButtonElement>("button.trigger");
  }

  private get menu(): HTMLElement | null {
    return this.renderRoot.querySelector<HTMLElement>('[role="menu"]');
  }

  private get items(): HTMLElement[] {
    return [
      ...this.renderRoot.querySelectorAll<HTMLElement>('[role="menuitem"]'),
    ];
  }

  private get focusedItem(): HTMLElement | null {
    const active = (this.renderRoot as ShadowRoot).activeElement;
    return active instanceof HTMLElement && this.menu?.contains(active)
      ? active
      : null;
  }

  private get hasContent(): boolean {
    return this.actions.length > 0;
  }

  override connectedCallback(): void {
    super.connectedCallback();
    this.listenOutside(this.open);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.hide(false);
    this.listenOutside(false);
  }

  /** Open the menu and focus its first or last item. */
  async show(where: "first" | "last" = "first"): Promise<void> {
    if (!this.hasContent) return;
    clearTimeout(this.tabClose);
    this.open = true;
    await this.updateComplete;
    const items = this.items;
    const target = items[where === "first" ? 0 : items.length - 1];
    for (const item of items) item.tabIndex = item === target ? 0 : -1;
    target?.focus();
  }

  /** Restore focus for Escape and actions; outside presses and Tab keep their focus flow. */
  hide(restoreFocus = true): void {
    clearTimeout(this.tabClose);
    this.tabClose = undefined;
    if (!this.open) return;
    this.open = false;
    if (restoreFocus) this.trigger?.focus();
  }

  protected override willUpdate(): void {
    if (!this.hasContent) this.open = false;
  }

  protected override updated(changed: PropertyValues<this>): void {
    if (changed.has("open")) this.listenOutside(this.open);
  }

  private listenOutside(on: boolean): void {
    if (on === this.listening) return;
    this.listening = on;
    if (on) document.addEventListener("pointerdown", this.onOutsidePress, true);
    else document.removeEventListener("pointerdown", this.onOutsidePress, true);
  }

  private readonly onOutsidePress = (e: Event): void => {
    const path = e.composedPath();
    if (path.includes(this)) return;
    this.hide(false);
  };

  private onTriggerKeydown(e: KeyboardEvent): void {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      void this.show(e.key === "ArrowDown" ? "first" : "last");
    } else if (e.key === "Escape" && this.open) {
      this.swallow(e);
      this.hide();
    }
  }

  /** Keep a key from the dialog and the card, whose Escape would close the details. */
  private swallow(e: KeyboardEvent): void {
    e.preventDefault();
    e.stopPropagation();
  }

  private onMenuKeydown(e: KeyboardEvent): void {
    e.stopPropagation();
    const items = this.items;
    const at = this.focusedItem ? items.indexOf(this.focusedItem) : -1;
    let target: number | undefined;
    switch (e.key) {
      case "ArrowDown":
        target = (at + 1) % items.length;
        break;
      case "ArrowUp":
        target = at <= 0 ? items.length - 1 : at - 1;
        break;
      case "Home":
        target = 0;
        break;
      case "End":
        target = items.length - 1;
        break;
      case "Escape":
        this.swallow(e);
        this.hide();
        return;
      case "Tab":
        // Keep the focused item in the DOM until native Tab has moved
        // focus. Removing it in Lit's microtask loses the tab origin.
        this.tabClose = setTimeout(() => this.hide(false), 0);
        return;
      default:
        return;
    }
    e.preventDefault();
    for (const item of items) item.tabIndex = item === items[target] ? 0 : -1;
    items[target]?.focus();
  }

  private choose(action: NodeAction): void {
    this.hide();
    fireEvent(this, "uit-action", { action });
  }

  protected override render(): TemplateResult | typeof nothing {
    const { localize } = this;
    if (!localize || !this.hasContent) return nothing;
    const label = localize("menu.label");
    return html`<button
        class="trigger"
        type="button"
        aria-haspopup="menu"
        aria-expanded=${String(this.open)}
        aria-controls=${this.menuId}
        aria-label=${label}
        title=${label}
        @click=${(e: Event) => {
          e.stopPropagation();
          if (this.open) this.hide();
          else void this.show();
        }}
        @keydown=${(e: KeyboardEvent) => this.onTriggerKeydown(e)}
      >
        ${iconTemplate(mdiDotsVertical)}<span>${label}</span>
      </button>
      ${this.open
        ? html`<div
            id=${this.menuId}
            class="menu"
            role="menu"
            aria-label=${label}
            @click=${(e: Event) => e.stopPropagation()}
            @pointerdown=${(e: Event) => e.stopPropagation()}
            @contextmenu=${(e: Event) => e.stopPropagation()}
            @keydown=${(e: KeyboardEvent) => this.onMenuKeydown(e)}
          >
            ${repeat(
              this.actions,
              (action) => action,
              (action) =>
                html`<button
                  type="button"
                  role="menuitem"
                  tabindex="-1"
                  data-action=${action}
                  @click=${() => this.choose(action)}
                >
                  ${iconTemplate(ACTION_ICONS[action])}<span
                    >${localize(ACTION_KEYS[action])}</span
                  >
                </button>`,
            )}
          </div>`
        : nothing}`;
  }

  static override styles = [themeTokens, controlStyles, menuStyles];
}

defineOnce("uit-node-menu", UitNodeMenu);

declare global {
  interface HTMLElementTagNameMap {
    "uit-node-menu": UitNodeMenu;
  }
}
