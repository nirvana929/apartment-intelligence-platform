export type ChatAction = {
  type: string;
  label?: string;
  confirmation_id?: string;
  payload?: Record<string, unknown>;
};

export type PendingAction = {
  type: string;
  confirmation_id: string;
  status: string;
  payload: Record<string, unknown>;
  expires_at?: number;
};

export type ChatCard = {
  type: string;
  [key: string]: unknown;
};

export type ChatResponse = {
  session_id: string | null;
  request_id: string;
  trace_id: string;
  task: string;
  message: string;
  phase: string;
  cards: ChatCard[];
  rooms: unknown[];
  kb_sources: unknown[];
  is_confident: boolean;
  actions: ChatAction[];
  pending_action: PendingAction | null;
  metadata: Record<string, unknown>;
};

export type ChatRequest = {
  message: string;
  session_id?: string;
  user_id?: string;
  action?: Record<string, unknown>;
  client_context?: Record<string, unknown>;
};
