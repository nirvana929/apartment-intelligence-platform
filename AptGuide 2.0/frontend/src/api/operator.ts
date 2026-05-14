import { http } from "./client";
import type { HandoffTicket } from "../types/operator";

const headers = { "X-Operator-Token": import.meta.env.VITE_OPERATOR_DEV_TOKEN || "operator-dev-token" };

export async function listTickets(status?: string): Promise<HandoffTicket[]> {
  const params: Record<string, string> = {};
  if (status && status !== "all") {
    params.status = status;
  }
  const response = await http.get<{ tickets: HandoffTicket[] }>("/operator/tickets", { headers, params });
  return response.data.tickets;
}

export async function getTicket(ticketId: string): Promise<HandoffTicket> {
  const response = await http.get<HandoffTicket>(`/operator/tickets/${ticketId}`, { headers });
  return response.data;
}

export async function replyTicket(ticketId: string, content: string): Promise<void> {
  await http.post(`/operator/tickets/${ticketId}/reply`, { content }, { headers });
}

export async function closeTicket(ticketId: string): Promise<void> {
  await http.post(`/operator/tickets/${ticketId}/close`, {}, { headers });
}
