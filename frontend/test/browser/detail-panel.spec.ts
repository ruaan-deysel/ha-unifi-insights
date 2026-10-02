import { expect, test, type Locator, type Page } from "@playwright/test";

interface Geometry {
    bottom: number;
    clientHeight: number;
    clientLeft: number;
    clientTop: number;
    clientWidth: number;
    left: number;
    right: number;
    scrollHeight: number;
    scrollTop: number;
    top: number;
}

const card = "unifi-insights-topology-card";
const panelHost = `${card} uit-detail-panel`;
const panel = `${panelHost} .panel`;

// Lovelace Sections grid cells are 56px rows separated by 8px gaps.
function sectionsHeight(rows: number): number {
    return rows * 56 + (rows - 1) * 8;
}

async function openFixture(
    page: Page,
    dimensions: {
        width: number;
        height: number;
        layout?: string;
        unresolved?: number;
    },
): Promise<void> {
    page.on("pageerror", (error) => console.error(`Fixture error: ${error}`));
    const query = new URLSearchParams({
        width: String(dimensions.width),
        height: String(dimensions.height),
    });
    if (dimensions.layout) query.set("layout", dimensions.layout);
    if (dimensions.unresolved !== undefined)
        query.set("unresolved", String(dimensions.unresolved));
    await page.goto(`/test/browser/fixture.html?${query}`);
    await page.waitForFunction(() => window.fixtureReady === true);
    await page.locator(`${card} [data-id="dev:uuid-core"]`).click();
    await expect(page.locator(panel)).toBeVisible();
}

async function geometry(locator: Locator): Promise<Geometry> {
    return locator.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        return {
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            left: rect.left,
            clientHeight: element.clientHeight,
            clientLeft: element.clientLeft,
            clientTop: element.clientTop,
            clientWidth: element.clientWidth,
            scrollHeight: element.scrollHeight,
            scrollTop: element.scrollTop,
        };
    });
}

function expectWithin(
    inner: Geometry,
    outer: Pick<Geometry, "left" | "top" | "right" | "bottom">,
): void {
    expect(inner.left).toBeGreaterThanOrEqual(outer.left - 2);
    expect(inner.top).toBeGreaterThanOrEqual(outer.top - 2);
    expect(inner.right).toBeLessThanOrEqual(outer.right + 2);
    expect(inner.bottom).toBeLessThanOrEqual(outer.bottom + 2);
}

async function expectContained(
    page: Page,
    { overflows = true } = {},
): Promise<void> {
    const frame = await geometry(page.locator("#frame"));
    const outer = await geometry(page.locator(`${card} .card`));
    const body = await geometry(page.locator(`${card} .body`));
    const inner = await geometry(page.locator(panelHost));
    const visibleBody = {
        left: Math.max(outer.left, frame.left, body.left),
        top: Math.max(outer.top, frame.top, body.top),
        right: Math.min(outer.right, frame.right, body.right),
        bottom: Math.min(outer.bottom, frame.bottom, body.bottom),
    };
    expectWithin(inner, visibleBody);
    const scrolling = await geometry(page.locator(panel));
    expectWithin(scrolling, inner);
    expectWithin(scrolling, visibleBody);
    if (overflows)
        expect(scrolling.scrollHeight).toBeGreaterThan(scrolling.clientHeight);
    else
        expect(scrolling.scrollHeight).toBeLessThanOrEqual(
            scrolling.clientHeight,
        );
}

async function scrollToAction(page: Page): Promise<void> {
    const scrollingPanel = page.locator(panel);
    await scrollingPanel.hover();
    await page.mouse.wheel(0, 2000);
    await expect
        .poll(async () => {
            const box = await geometry(scrollingPanel);
            return Math.abs(
                box.scrollHeight - box.clientHeight - box.scrollTop,
            );
        })
        .toBeLessThanOrEqual(2);
    await expectActionInView(page);
}

async function expectActionInView(page: Page): Promise<void> {
    const action = page.getByRole("button", { name: "Open device" });
    await expect(action).toBeVisible();
    const box = await geometry(page.locator(panel));
    expectWithin(await geometry(action), {
        left: box.left + box.clientLeft,
        top: box.top + box.clientTop,
        right: box.left + box.clientLeft + box.clientWidth,
        bottom: box.top + box.clientTop + box.clientHeight,
    });
    await action.focus();
    await expect(action).toBeFocused();
}

const dialog = `${panelHost} dialog`;

// A card too short for the details shows them in a modal dialog instead.
async function expectDialogShowsEverything(page: Page): Promise<void> {
    const modal = page.locator(dialog);
    await expect(modal).toBeVisible();
    expect(await modal.evaluate((element) => element.matches(":modal"))).toBe(
        true,
    );
    const viewport = page.viewportSize()!;
    const box = await geometry(modal);
    expectWithin(box, {
        left: 0,
        top: 0,
        right: viewport.width,
        bottom: viewport.height,
    });
    const scrolling = await geometry(page.locator(panel));
    // The panel fills the dialog exactly: no browser-default frame around it.
    for (const side of ["left", "top", "right", "bottom"] as const)
        expect(Math.abs(scrolling[side] - box[side])).toBeLessThanOrEqual(1);
    expect(box.right - box.left).toBeLessThanOrEqual(400);
    expect(scrolling.scrollHeight).toBeLessThanOrEqual(scrolling.clientHeight);
    await expectActionInView(page);
}

const node = `${card} [data-id="dev:uuid-core"]`;

async function expectInCard(page: Page): Promise<void> {
    await expect(page.locator(dialog)).toHaveCount(0);
    await expectContained(page, { overflows: false });
    expect((await geometry(page.locator(panel))).scrollTop).toBe(0);
    await expectActionInView(page);
}

test.describe("topology detail panel overflow", () => {
    test("desktop card with room keeps the details beside the graph", async ({
        page,
    }) => {
        // Reduced motion makes zoom instant, so each transform can be compared.
        await page.emulateMedia({ reducedMotion: "reduce" });
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 620 });
        await expect(page.locator(panelHost)).not.toHaveAttribute("narrow");
        await expectInCard(page);

        const viewport = page.locator(`${card} uit-graph-view g.viewport`);
        const fitted = await viewport.getAttribute("transform");
        await page.getByRole("button", { name: "Zoom in" }).click();
        await expect(viewport).not.toHaveAttribute("transform", fitted!);
        const zoomed = await viewport.getAttribute("transform");
        const canvas = page.locator(`${card} uit-graph-view svg.canvas`);
        const canvasBox = await canvas.boundingBox();
        expect(canvasBox).not.toBeNull();
        await page.mouse.move(canvasBox!.x + 120, canvasBox!.y + 100);
        await page.mouse.down();
        await page.mouse.move(canvasBox!.x + 180, canvasBox!.y + 130);
        await page.mouse.up();
        await expect(viewport).not.toHaveAttribute("transform", zoomed!);
        await expectContained(page, { overflows: false });

        // Shrink across the 600px breakpoint into the narrow bottom sheet.
        await page.locator("#frame").evaluate((frame) => {
            frame.style.width = "560px";
        });
        await expect(page.locator(panelHost)).toHaveAttribute("narrow", "");
        await expectContained(page, { overflows: false });

        await page.getByRole("button", { name: "Close", exact: true }).click();
        await expect(page.locator(panel)).toBeHidden();
    });

    test("narrow card with room shows the full switch detail unscrolled", async ({
        page,
    }) => {
        // The #186 reporter's card after the first fix: the bottom sheet was
        // capped at 60% of the canvas, so details still needed scrolling.
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 560, height: 620, unresolved: 93 });
        await expect(page.locator(panelHost)).toHaveAttribute("narrow", "");
        await expect(page.locator(`${card} .notices`)).toBeVisible();
        await expectInCard(page);
    });

    test("eight-row narrow Sections card shows full details unscrolled", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, {
            width: 500,
            height: sectionsHeight(8),
            layout: "grid",
        });
        await expect(page.locator(panelHost)).toHaveAttribute("narrow", "");
        await expectInCard(page);
    });

    test("short desktop card opens the full details in a dialog", async ({
        page,
    }) => {
        // #186 on 2026.10.0: a short card cut the details off, and reaching
        // Open device needed a scroll inside the card.
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 360 });
        await expectDialogShowsEverything(page);

        await page.keyboard.press("Escape");
        await expect(page.locator(panel)).toBeHidden();
        await expect(page.locator(dialog)).toHaveCount(0);
        await expect(page.locator(node)).toBeFocused();
    });

    test("short narrow card opens the full details in a dialog", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await openFixture(page, { width: 360, height: 320 });
        await expectDialogShowsEverything(page);

        await page.getByRole("button", { name: "Close", exact: true }).click();
        await expect(page.locator(dialog)).toHaveCount(0);
        await expect(page.locator(node)).toBeFocused();
    });

    test("five-row Sections card dialog closes from the backdrop", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, {
            width: 800,
            height: sectionsHeight(5),
            layout: "grid",
        });
        await expectDialogShowsEverything(page);

        await page.mouse.click(4, 4);
        await expect(page.locator(dialog)).toHaveCount(0);
        await expect(page.locator(panel)).toBeHidden();
    });

    test("Open device leaves no dialog behind", async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 360 });
        await expectDialogShowsEverything(page);

        await page.getByRole("button", { name: "Open device" }).click();
        await expect(page).toHaveURL(/\/config\/devices\/device\//);
        await expect(page.locator(dialog)).toHaveCount(0);
    });

    test("dragging a text selection onto the backdrop keeps the dialog", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 360 });
        await expectDialogShowsEverything(page);

        const value = await page.locator(`${panel} dd`).first().boundingBox();
        expect(value).not.toBeNull();
        await page.mouse.move(value!.x + 2, value!.y + value!.height / 2);
        await page.mouse.down();
        await page.mouse.move(4, 4, { steps: 5 });
        await page.mouse.up();
        await expect(page.locator(dialog)).toBeVisible();
    });

    test("detaching the card closes the dialog instead of leaving it in the card", async ({
        page,
    }) => {
        // HA detaches hidden and cached panels and later re-attaches them.
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 360 });
        await expectDialogShowsEverything(page);

        await page.evaluate(async () => {
            const element = window.fixtureCard;
            const parent = element.parentElement!;
            element.remove();
            await new Promise((resolve) => setTimeout(resolve, 50));
            parent.append(element);
        });
        await expect(page.locator(dialog)).toHaveCount(0);
        await expect(page.locator(panel)).toBeHidden();

        await page.locator(node).click();
        await expectDialogShowsEverything(page);
    });

    test("card shrunk after opening keeps the panel in the card and scrollable", async ({
        page,
    }) => {
        // Only opening a panel (or crossing the narrow breakpoint) can turn
        // it into a dialog; a resize alone leaves the scrolling panel.
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 620 });
        await expectInCard(page);

        await page.locator("#frame").evaluate((frame) => {
            frame.style.height = "360px";
        });
        await expect(page.locator(panelHost)).not.toHaveAttribute("narrow");
        await expectContained(page);
        await expect(page.locator(dialog)).toHaveCount(0);
        // Nor does the next live update.
        await page.evaluate(() => window.fixtureUpdate());
        await page.evaluate(
            () => new Promise((resolve) => requestAnimationFrame(resolve)),
        );
        await expect(page.locator(dialog)).toHaveCount(0);
        await scrollToAction(page);
    });

    test("dialog scrolls when the screen itself is too short", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 1280, height: 320 });
        await openFixture(page, { width: 800, height: 300 });
        const modal = page.locator(dialog);
        await expect(modal).toBeVisible();
        expectWithin(await geometry(modal), {
            left: 0,
            top: 0,
            right: 1280,
            bottom: 320,
        });
        const scrolling = await geometry(page.locator(panel));
        expect(scrolling.scrollHeight).toBeGreaterThan(scrolling.clientHeight);
        await scrollToAction(page);
    });
});

declare global {
    interface Window {
        fixtureCard: HTMLElement;
        fixtureReady: boolean;
        fixtureUpdate: () => void;
    }
}
