/** Pointer travel in CSS px beyond which a press is a pan, not a press-and-hold. */
export const PAN_SLOP_PX = 8;

export class ContextGesture {
  private pointers = new Set<number>();
  private origin = { x: 0, y: 0, moved: false };

  down(e: PointerEvent): void {
    if (e.isPrimary) {
      this.pointers = new Set([e.pointerId]);
      this.origin = { x: e.clientX, y: e.clientY, moved: false };
    } else {
      // A second finger: this is a pinch.
      this.pointers.add(e.pointerId);
      this.origin.moved = true;
    }
  }

  move(e: PointerEvent): void {
    if (
      !this.origin.moved &&
      this.pointers.has(e.pointerId) &&
      Math.hypot(e.clientX - this.origin.x, e.clientY - this.origin.y) >
        PAN_SLOP_PX
    )
      this.origin.moved = true;
  }

  end(e: PointerEvent): void {
    this.pointers.delete(e.pointerId);
  }

  /**
   * Whether a context click or a long press on a node asks the card for its
   * action menu. The browser's own menu never shows. After a pan or a pinch
   * the press is not a long press, so the node menu stays shut.
   */
  get allowsMenu(): boolean {
    return !this.origin.moved && this.pointers.size <= 1;
  }
}
