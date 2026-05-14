export type HandoffTicket = {
  ticket_id: string;
  user_id: string;
  session_id: string;
  status: string;
  trigger: string;
  summary: Record<string, unknown>;
  messages: Array<{ sender: string; content: string; created_at?: string }>;
  created_at?: string;
};
