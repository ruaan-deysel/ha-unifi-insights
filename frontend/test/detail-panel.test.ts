import { afterEach, expect, it, vi } from "vitest";
import { makeLocalize } from "../src/localize";
import { UitDetailPanel } from "../src/views/detail-panel";
import { cleanup, fixtureModel, mount } from "./helpers";

const localize = makeLocalize("en");
afterEach(cleanup);

const panel = (selectedId: string | undefined) =>
    mount<UitDetailPanel>("uit-detail-panel", {
        model: fixtureModel(),
        localize,
        selectedId,
    });
const rows = (el: UitDetailPanel) =>
    Object.fromEntries(
        [...el.shadowRoot!.querySelectorAll(".row")].map((r) => [
            r.querySelector("dt")!.textContent,
            r.querySelector("dd")!.textContent,
        ]),
    );

it("shows a device with its uplink and an Open device link", async () => {
    const el = await panel("dev:uuid-core");
    expect(el.shadowRoot!.querySelector("h3")!.textContent).toBe("Core 24");
    expect(rows(el)).toMatchObject({
        Type: "Switch",
        Model: "USW Pro Max 24",
        State: "Online",
        "Connected to": "Gateway",
        Port: "11 → 26",
        Speed: "10G",
        Link: "Wired",
    });
    el.shadowRoot!.querySelector<HTMLButtonElement>("button.action")!.click();
    expect(location.pathname).toBe("/config/devices/device/reg-core");
});

it("shows PoE draw on a powered link", async () => {
    expect(rows(await panel("dev:uuid-ap"))).toMatchObject({ PoE: "12.3 W" });
});

it("shows a client hidden inside a collapsed group", async () => {
    const el = await panel("cli:cli-tv");
    expect(rows(el)).toMatchObject({
        Connection: "Wired",
        VLAN: "3",
        Network: "Media",
        "Connected to": "Ultra A",
        Port: "4",
    });
    expect(el.shadowRoot!.querySelector("button.action")).toBeNull();
});

it("lists and searches group members, selecting one on click", async () => {
    const el = await panel("group:dev:uuid-u1");
    const selected = vi.fn();
    el.addEventListener("uit-select", (e) =>
        selected((e as CustomEvent).detail),
    );
    el.shadowRoot!.querySelector<HTMLButtonElement>("button.member")!.click();
    expect(selected).toHaveBeenCalledWith({ id: "cli:cli-tv" });
    const search = el.shadowRoot!.querySelector<HTMLInputElement>("input")!;
    search.value = "zzz";
    search.dispatchEvent(new Event("input"));
    await el.updateComplete;
    expect(el.shadowRoot!.querySelectorAll("button.member")).toHaveLength(0);
});

it("closes on request and renders nothing without a selection", async () => {
    const el = await panel("dev:uuid-gw");
    const closed = vi.fn();
    el.addEventListener("uit-close", closed);
    el.shadowRoot!.querySelector<HTMLButtonElement>("button.close")!.click();
    expect(closed).toHaveBeenCalledOnce();
    const empty = await panel("dev:gone");
    expect(empty.shadowRoot!.querySelector("section")).toBeNull();
});

it("shows details in a modal dialog that closes the panel", async () => {
    // jsdom has no dialog methods or layout, so stub them and force the mode.
    // Browsers fire "close" in a later task, so the stub defers it too.
    const proto = HTMLDialogElement.prototype;
    proto.showModal = vi.fn(function (this: HTMLDialogElement) {
        this.open = true;
    });
    proto.close = vi.fn(function (this: HTMLDialogElement) {
        this.open = false;
        queueMicrotask(() => this.dispatchEvent(new Event("close")));
    });
    const settle = () => new Promise((resolve) => setTimeout(resolve));
    try {
        const el = await panel("dev:uuid-core");
        el.modal = true;
        await el.updateComplete;
        const dialog = el.shadowRoot!.querySelector("dialog")!;
        expect(dialog.open).toBe(true);
        expect(dialog.getAttribute("aria-labelledby")).toBe("title");
        expect(dialog.querySelector("section")!.hasAttribute("role")).toBe(
            false,
        );
        expect(dialog.querySelector("#title")!.textContent).toBe("Core 24");
        const closed = vi.fn();
        el.addEventListener("uit-close", closed);

        // A click inside the panel, or a drag from it onto the backdrop,
        // keeps the dialog open.
        const dl = dialog.querySelector<HTMLElement>("dl")!;
        dl.click();
        dl.dispatchEvent(new Event("pointerdown", { bubbles: true }));
        dialog.click();
        await settle();
        expect(closed).not.toHaveBeenCalled();

        // A press and release on the backdrop closes it.
        dialog.dispatchEvent(new Event("pointerdown"));
        dialog.click();
        await settle();
        expect(closed).toHaveBeenCalledOnce();

        // Escape and Close go through the dialog, not straight to uit-close.
        for (const close of [
            () =>
                dialog.dispatchEvent(
                    new KeyboardEvent("keydown", {
                        key: "Escape",
                        bubbles: true,
                    }),
                ),
            () =>
                dialog
                    .querySelector<HTMLButtonElement>("button.close")!
                    .click(),
        ]) {
            dialog.open = true;
            closed.mockClear();
            close();
            expect(dialog.open).toBe(false);
            await settle();
            expect(closed).toHaveBeenCalledOnce();
        }

        dialog.open = true;
        dialog.querySelector<HTMLButtonElement>("button.action")!.click();
        expect(dialog.open).toBe(false);
        expect(location.pathname).toBe("/config/devices/device/reg-core");

        // Detaching the panel (HA suspending the view) closes the dialog.
        dialog.open = true;
        el.remove();
        expect(dialog.open).toBe(false);
        document.body.append(el);

        el.selectedId = undefined;
        await el.updateComplete;
        expect(el.modal).toBe(false);
    } finally {
        delete (proto as Partial<HTMLDialogElement>).showModal;
        delete (proto as Partial<HTMLDialogElement>).close;
    }
});

it("constrains .panel as a shrinkable flex child with a sticky header so narrow panels fit or scroll cleanly", () => {
    // jsdom does not compute layout, so verify the CSS contract directly.
    const cssText = UitDetailPanel.styles.map((s) => s.cssText).join("\n");
    expect(cssText).toMatch(
        /:host\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;/s,
    );
    expect(cssText).toMatch(
        /:host\(\[narrow\]\)\s*\{[^}]*max-height:\s*calc\(100%\s*-\s*8px\);/s,
    );
    expect(cssText).toMatch(
        /\.panel\s*\{[^}]*flex:\s*1 1 auto;[^}]*min-height:\s*0;[^}]*overflow:\s*auto;/s,
    );
    expect(cssText).toMatch(
        /header\s*\{[^}]*position:\s*sticky;[^}]*top:\s*0;/s,
    );
    expect(cssText).not.toMatch(/\.panel\s*\{[^}]*height:\s*100%;/s);
});
