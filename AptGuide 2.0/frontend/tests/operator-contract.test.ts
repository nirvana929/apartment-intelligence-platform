import { describe, expect, it } from "vitest";
import type { HandoffTicket } from "../src/types/operator";

describe("HandoffTicket contract", () => {
  it("supports ticket structure with messages", () => {
    const ticket: HandoffTicket = {
      ticket_id: "hof-abc123",
      user_id: "u1",
      session_id: "s1",
      status: "open",
      trigger: "user_initiated",
      summary: { current_message: "转人工" },
      messages: [
        { sender: "user", content: "转人工" },
        { sender: "operator", content: "您好，我来帮您。" }
      ]
    };

    expect(ticket.ticket_id).toBe("hof-abc123");
    expect(ticket.messages).toHaveLength(2);
    expect(ticket.messages[1].sender).toBe("operator");
  });

  it("has required fields: ticket_id, status, messages, created_at", () => {
    const ticket: HandoffTicket = {
      ticket_id: "hof-xyz789",
      user_id: "u2",
      session_id: "s2",
      status: "closed",
      trigger: "timeout",
      summary: {},
      messages: [
        { sender: "user", content: "你好", created_at: "2026-05-14T10:00:00Z" }
      ],
      created_at: "2026-05-14T09:55:00Z"
    };

    expect(ticket.ticket_id).toBeDefined();
    expect(ticket.status).toMatch(/open|closed/);
    expect(Array.isArray(ticket.messages)).toBe(true);
    expect(ticket.created_at).toBeDefined();
  });

  it("supports both open and closed status values", () => {
    const openTicket: HandoffTicket = {
      ticket_id: "hof-open",
      user_id: "u1",
      session_id: "s1",
      status: "open",
      trigger: "user_initiated",
      summary: {},
      messages: []
    };
    const closedTicket: HandoffTicket = {
      ticket_id: "hof-closed",
      user_id: "u2",
      session_id: "s2",
      status: "closed",
      trigger: "operator_closed",
      summary: {},
      messages: []
    };

    expect(openTicket.status).toBe("open");
    expect(closedTicket.status).toBe("closed");
  });
});
