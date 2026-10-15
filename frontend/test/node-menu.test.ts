import { afterEach, describe, expect, it, vi } from "vitest";
import type { NodeAction } from "../src/data/node-details";
import { makeLocalize } from "../src/localize";
import "../src/views/node-menu";
import type { UitNodeMenu } from "../src/views/node-menu";
import { cleanup, mount } from "./helpers";

const localize = makeLocalize("en");
afterEach(cleanup);

const ALL: NodeAction[] = ["copy_ip", "copy_mac", "open_device", "open_entity"];

const menu = (props: Record<string, unknown> = {}) =>
  mount<UitNodeMenu>("uit-node-menu", {
    localize,
    actions: ALL,
    ...props,
  });
const trigger = (el: UitNodeMenu) =>
  el.shadowRoot!.querySelector<HTMLButtonElement>("button.trigger")!;
const list = (el: UitNodeMenu) =>
  el.shadowRoot!.querySelector<HTMLElement>('[role="menu"]');
const items = (el: UitNodeMenu) => [
  ...el.shadowRoot!.querySelectorAll<HTMLElement>('[role="menuitem"]'),
];
const labels = (el: UitNodeMenu) => items(el).map((i) => i.textContent?.trim());
const focused = (el: UitNodeMenu) => el.shadowRoot!.activeElement;
const press = (target: Element, key: string, init: KeyboardEventInit = {}) => {
  const event = new KeyboardEvent("keydown", {
    key,
    bubbles: true,
    composed: true,
    cancelable: true,
    ...init,
  });
  target.dispatchEvent(event);
  return event;
};
/** Click the trigger and wait for the menu to render and take focus. */
async function open(el: UitNodeMenu): Promise<void> {
  trigger(el).click();
  await el.updateComplete;
  await el.updateComplete;
}

describe("<uit-node-menu> button", () => {
  it("is a labelled menu button while the menu is closed", async () => {
    const el = await menu();
    const button = trigger(el);
    expect(button.getAttribute("aria-label")).toBe("Actions");
    expect(button.getAttribute("aria-haspopup")).toBe("menu");
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(button.getAttribute("aria-controls")).toMatch(/^uit-node-menu-/);
    expect(list(el)).toBeNull();
  });

  it("renders nothing when there is no action", async () => {
    const el = await menu({ actions: [] });
    expect(el.shadowRoot!.querySelector("button")).toBeNull();
  });

  it("opens on click with the first item focused", async () => {
    const el = await menu();
    await open(el);
    const menuEl = list(el)!;
    expect(trigger(el).getAttribute("aria-expanded")).toBe("true");
    expect(trigger(el).getAttribute("aria-controls")).toBe(menuEl.id);
    expect(menuEl.getAttribute("aria-label")).toBe("Actions");
    expect(labels(el)).toEqual([
      "Copy IP address",
      "Copy MAC address",
      "Open device",
      "Open entity",
    ]);
    expect(items(el).map((i) => i.tabIndex)).toEqual([0, -1, -1, -1]);
    expect(focused(el)).toBe(items(el)[0]);
  });

  it("closes on a second click and keeps focus on the button", async () => {
    const el = await menu();
    await open(el);
    trigger(el).focus();
    trigger(el).click();
    await el.updateComplete;
    expect(list(el)).toBeNull();
    expect(trigger(el).getAttribute("aria-expanded")).toBe("false");
    expect(focused(el)).toBe(trigger(el));
  });

  it("opens from the keyboard: ArrowDown on the first item, ArrowUp on the last", async () => {
    const el = await menu();
    const down = press(trigger(el), "ArrowDown");
    await el.updateComplete;
    await el.updateComplete;
    expect(down.defaultPrevented).toBe(true);
    expect(focused(el)).toBe(items(el)[0]);

    press(items(el)[0]!, "Escape");
    await el.updateComplete;
    const up = press(trigger(el), "ArrowUp");
    await el.updateComplete;
    await el.updateComplete;
    expect(up.defaultPrevented).toBe(true);
    expect(focused(el)).toBe(items(el)[3]);
  });

  it("can be opened by its host on the last item", async () => {
    const el = await menu();
    await el.show("last");
    expect(focused(el)).toBe(items(el)[3]);
    el.hide();
    await el.updateComplete;
    expect(list(el)).toBeNull();
  });
});

describe("<uit-node-menu> keyboard", () => {
  it("moves with arrows, wrapping, and jumps with Home and End", async () => {
    const el = await menu();
    await open(el);
    const at = (i: number) => items(el)[i];
    const sequence: [string, number][] = [
      ["ArrowDown", 1],
      ["ArrowDown", 2],
      ["ArrowDown", 3],
      ["ArrowDown", 0],
      ["ArrowUp", 3],
      ["ArrowUp", 2],
      ["Home", 0],
      ["End", 3],
    ];
    for (const [key, expected] of sequence) {
      const event = press(focused(el)!, key);
      expect(event.defaultPrevented).toBe(true);
      expect(focused(el), `${key} -> item ${expected}`).toBe(at(expected));
    }
  });

  it("lets other keys through", async () => {
    const el = await menu();
    await open(el);
    const event = press(focused(el)!, "a");
    expect(event.defaultPrevented).toBe(false);
    expect(list(el)).not.toBeNull();
  });

  it("closes on Escape, returns focus to the button and keeps the key from the dialog and card", async () => {
    const outer = vi.fn();
    const wrapper = document.createElement("div");
    wrapper.addEventListener("keydown", outer);
    document.body.append(wrapper);
    const el = await menu();
    wrapper.append(el);
    await open(el);

    const event = press(focused(el)!, "Escape");
    await el.updateComplete;
    expect(list(el)).toBeNull();
    expect(focused(el)).toBe(trigger(el));
    expect(event.defaultPrevented).toBe(true);
    expect(outer).not.toHaveBeenCalled();
  });

  it("closes on Escape pressed on the button while the menu is open", async () => {
    const outer = vi.fn();
    const wrapper = document.createElement("div");
    wrapper.addEventListener("keydown", outer);
    document.body.append(wrapper);
    const el = await menu();
    wrapper.append(el);
    await open(el);
    trigger(el).focus();
    const event = press(trigger(el), "Escape");
    await el.updateComplete;
    expect(list(el)).toBeNull();
    expect(focused(el)).toBe(trigger(el));
    expect(event.defaultPrevented).toBe(true);
    expect(outer).not.toHaveBeenCalled();
  });

  it("leaves Escape alone while the menu is closed so the dialog can close", async () => {
    const outer = vi.fn();
    const wrapper = document.createElement("div");
    wrapper.addEventListener("keydown", outer);
    document.body.append(wrapper);
    const el = await menu();
    wrapper.append(el);
    const event = press(trigger(el), "Escape");
    expect(outer).toHaveBeenCalledOnce();
    expect(event.defaultPrevented).toBe(false);
  });

  it("closes on Tab without moving focus to the button or trapping the key", async () => {
    const el = await menu();
    await open(el);
    const event = press(focused(el)!, "Tab");
    await new Promise((resolve) => setTimeout(resolve, 0));
    await el.updateComplete;
    expect(list(el)).toBeNull();
    // Native Tab moves to the next control; the trigger never receives focus.
    expect(event.defaultPrevented).toBe(false);
    expect(focused(el)).not.toBe(trigger(el));
  });
});

describe("<uit-node-menu> dismissal and activation", () => {
  const outsidePress = (target: Element, type = "pointerdown") =>
    target.dispatchEvent(new Event(type, { bubbles: true, composed: true }));
  const later = () => new Promise((resolve) => setTimeout(resolve, 5));

  it("closes on a press outside without focusing the button", async () => {
    const outside = document.createElement("div");
    document.body.append(outside);
    const el = await menu();
    await open(el);

    for (const target of [trigger(el), items(el)[1]!]) outsidePress(target);
    await el.updateComplete;
    expect(list(el)).not.toBeNull();

    outsidePress(outside);
    await el.updateComplete;
    expect(list(el)).toBeNull();
    expect(trigger(el).getAttribute("aria-expanded")).toBe("false");
    expect(focused(el)).not.toBe(trigger(el));
  });

  it("does not take focus back for a later, unrelated press after a cancelled one", async () => {
    const outside = document.createElement("p");
    document.body.append(outside);
    const el = await menu();
    await open(el);
    outsidePress(outside);
    await later();
    outsidePress(outside, "pointercancel");
    await later();
    // The user then moves focus away on purpose; a later release must not undo it.
    trigger(el).blur();
    outsidePress(outside, "pointerup");
    await later();
    expect(focused(el)).toBeNull();
  });

  it("leaves focus on the control that the outside press focused", async () => {
    const outside = document.createElement("button");
    const inner = document.createElement("span");
    outside.append(inner);
    document.body.append(outside);
    const el = await menu();
    await open(el);
    // The press lands on a child of the control; the control takes focus.
    outsidePress(inner);
    outside.focus();
    await later();
    expect(document.activeElement).toBe(outside);
    expect(list(el)).toBeNull();
  });

  it("leaves focus on an element that takes focus through its tabindex", async () => {
    // Like a graph node: not a native control, but focusable on press.
    const node = document.createElement("div");
    node.tabIndex = -1;
    document.body.append(node);
    const el = await menu();
    await open(el);
    outsidePress(node);
    node.focus();
    await later();
    expect(document.activeElement).toBe(node);
  });

  it("does not take focus back after the menu was opened again", async () => {
    const outside = document.createElement("p");
    document.body.append(outside);
    const el = await menu();
    await open(el);
    outsidePress(outside);
    trigger(el).blur();
    await open(el);
    const item = focused(el);
    await later();
    expect(focused(el)).toBe(item);
    expect(list(el)).not.toBeNull();
  });

  it("stops listening for outside presses once closed or detached", async () => {
    const add = vi.spyOn(document, "addEventListener");
    const remove = vi.spyOn(document, "removeEventListener");
    try {
      const el = await menu();
      await open(el);
      expect(add).toHaveBeenCalledWith(
        "pointerdown",
        expect.any(Function),
        true,
      );
      press(focused(el)!, "Escape");
      await el.updateComplete;
      expect(remove).toHaveBeenCalledWith(
        "pointerdown",
        expect.any(Function),
        true,
      );
      remove.mockClear();
      await open(el);
      el.remove();
      expect(remove).toHaveBeenCalledWith(
        "pointerdown",
        expect.any(Function),
        true,
      );
    } finally {
      add.mockRestore();
      remove.mockRestore();
    }
  });

  it("fires the chosen action, closes and returns focus to the button", async () => {
    const el = await menu();
    const chosen = vi.fn();
    el.addEventListener("uit-action", (e) => chosen((e as CustomEvent).detail));
    await open(el);
    items(el)[1]!.click();
    await el.updateComplete;
    expect(chosen).toHaveBeenCalledExactlyOnceWith({
      action: "copy_mac",
    });
    expect(list(el)).toBeNull();
    expect(focused(el)).toBe(trigger(el));
  });

  it("closes when the actions go away and stays closed when they return", async () => {
    const el = await menu();
    await open(el);
    el.actions = [];
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector("button")).toBeNull();
    el.actions = ALL;
    await el.updateComplete;
    expect(list(el)).toBeNull();
  });
});

describe("plan v3 menu focus", () => {
  it("does not move focus on an outside press", async () => {
    const el = await menu();
    await open(el);
    const focus = vi.spyOn(trigger(el), "focus");
    document.body.dispatchEvent(
      new Event("pointerdown", { bubbles: true, composed: true }),
    );
    await el.updateComplete;
    expect(list(el)).toBeNull();
    expect(focus).not.toHaveBeenCalled();
  });

  it("does not focus the trigger after Tab", async () => {
    const el = await menu();
    await open(el);
    const focus = vi.spyOn(trigger(el), "focus");
    const event = press(focused(el)!, "Tab");
    await new Promise((resolve) => setTimeout(resolve, 0));
    await el.updateComplete;
    expect(list(el)).toBeNull();
    expect(event.defaultPrevented).toBe(false);
    expect(focus).not.toHaveBeenCalled();
  });
});

it.each(["Enter", " "])(
  "leaves native %s activation unprevented and contains events",
  async (key) => {
    const el = await menu();
    const action = vi.fn();
    const bubbled = vi.fn();
    el.addEventListener("uit-action", action);
    el.addEventListener("keydown", bubbled);
    el.addEventListener("click", bubbled);
    el.addEventListener("pointerdown", bubbled);
    await open(el);
    bubbled.mockClear();
    items(el)[0]!.dispatchEvent(
      new Event("pointerdown", { bubbles: true, composed: true }),
    );
    const event = press(items(el)[0]!, key);
    await el.updateComplete;
    expect(event.defaultPrevented).toBe(false);
    expect(action).not.toHaveBeenCalled();
    expect(bubbled).not.toHaveBeenCalled();
    expect(focused(el)).toBe(items(el)[0]);
  },
);
