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

test.describe("topology detail panel overflow", () => {
    test("desktop card contains and scrolls the full switch detail", async ({
        page,
    }) => {
        // Reduced motion makes zoom instant, so each transform can be compared.
        await page.emulateMedia({ reducedMotion: "reduce" });
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFixture(page, { width: 800, height: 360 });
        await expectContained(page);
        await scrollToAction(page);

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
        await expectContained(page);

        // Shrink across the 600px breakpoint into the narrow bottom sheet.
        await page.locator("#frame").evaluate((frame) => {
            frame.style.width = "560px";
            frame.style.height = "300px";
        });
        await expect(page.locator(panelHost)).toHaveAttribute("narrow", "");
        await expectContained(page);

        await scrollToAction(page);

        await page.getByRole("button", { name: "Close", exact: true }).click();
        await expect(page.locator(panel)).toBeHidden();
    });

    test("narrow card keeps the bottom sheet and actions reachable", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await openFixture(page, { width: 360, height: 320 });
        await expectContained(page);
        await scrollToAction(page);

        await page.keyboard.press("Escape");
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
        await expectContained(page, { overflows: false });
        await expectActionInView(page);
    });

    test("Sections fixed-height card contains the scrolling panel", async ({
        page,
    }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        // Five rows is the shortest size that still leaves the panel room for
        // its final action below the toolbar; the long details still overflow.
        await openFixture(page, {
            width: 800,
            height: sectionsHeight(5),
            layout: "grid",
        });
        await expectContained(page);
        await scrollToAction(page);
    });
});

declare global {
    interface Window {
        fixtureCard: HTMLElement;
        fixtureReady: boolean;
    }
}
