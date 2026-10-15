import { expect, it } from "vitest";
import { ContextGesture, PAN_SLOP_PX } from "../src/views/context-gesture";

it("stationary press allows menu", () => {
  const gesture = new ContextGesture();
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 10,
      clientY: 20,
      pointerId: 1,
      isPrimary: true,
    }),
  );
  expect(gesture.allowsMenu).toBe(true);
});

it("move beyond slop blocks", () => {
  const gesture = new ContextGesture();
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 10,
      clientY: 20,
      pointerId: 1,
      isPrimary: true,
    }),
  );
  gesture.move(
    new PointerEvent("pointermove", {
      clientX: 10 + PAN_SLOP_PX + 1,
      clientY: 20,
      pointerId: 1,
    }),
  );
  expect(gesture.allowsMenu).toBe(false);
});

it("move within slop allows", () => {
  const gesture = new ContextGesture();
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 10,
      clientY: 20,
      pointerId: 1,
      isPrimary: true,
    }),
  );
  gesture.move(
    new PointerEvent("pointermove", {
      clientX: 10 + PAN_SLOP_PX,
      clientY: 20,
      pointerId: 1,
    }),
  );
  expect(gesture.allowsMenu).toBe(true);
});

it("second pointer (pinch) blocks", () => {
  const gesture = new ContextGesture();
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 10,
      clientY: 20,
      pointerId: 1,
      isPrimary: true,
    }),
  );
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 30,
      clientY: 40,
      pointerId: 2,
      isPrimary: false,
    }),
  );
  expect(gesture.allowsMenu).toBe(false);
});

it("pointer end then new primary press resets", () => {
  const gesture = new ContextGesture();
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 10,
      clientY: 20,
      pointerId: 1,
      isPrimary: true,
    }),
  );
  gesture.move(
    new PointerEvent("pointermove", {
      clientX: 50,
      clientY: 50,
      pointerId: 1,
    }),
  );
  expect(gesture.allowsMenu).toBe(false);

  gesture.end(new PointerEvent("pointerup", { pointerId: 1 }));
  gesture.down(
    new PointerEvent("pointerdown", {
      clientX: 100,
      clientY: 100,
      pointerId: 1,
      isPrimary: true,
    }),
  );
  expect(gesture.allowsMenu).toBe(true);
});
