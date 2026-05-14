import { describe, expect, it } from "vitest";
import type { ChatResponse } from "../src/types/chat";

describe("ChatResponse contract", () => {
  it("supports cards, actions, pending action, and trace ids", () => {
    const response: ChatResponse = {
      session_id: "s1",
      request_id: "r1",
      trace_id: "t1",
      task: "appointment",
      message: "请确认预约",
      phase: "confirmation_required",
      cards: [{ type: "confirmation", confirmation_id: "c1" }],
      rooms: [],
      kb_sources: [],
      is_confident: true,
      actions: [{ type: "confirm", confirmation_id: "c1" }],
      pending_action: { type: "appointment.create", confirmation_id: "c1", status: "pending", payload: {} },
      metadata: {}
    };

    expect(response.cards[0].type).toBe("confirmation");
    expect(response.actions[0].confirmation_id).toBe("c1");
  });

  it("has request_id matching r- prefix, trace_id matching t- prefix, and truthy task/phase", () => {
    const response: ChatResponse = {
      session_id: "s1",
      request_id: "r-abc123",
      trace_id: "t-xyz789",
      task: "appointment",
      message: "ok",
      phase: "confirmation_required",
      cards: [],
      rooms: [],
      kb_sources: [],
      is_confident: true,
      actions: [],
      pending_action: null,
      metadata: {}
    };

    expect(response.request_id).toMatch(/^r-/);
    expect(response.trace_id).toMatch(/^t-/);
    expect(response.task).toBeTruthy();
    expect(response.phase).toBeTruthy();
  });
});
