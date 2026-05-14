import { defineStore } from "pinia";
import { listTickets, getTicket, replyTicket, closeTicket } from "../api/operator";
import type { HandoffTicket } from "../types/operator";

export const useOperatorStore = defineStore("operator", {
  state: () => ({
    tickets: [] as HandoffTicket[],
    selectedTicket: null as HandoffTicket | null,
    loading: false,
    error: null as string | null,
    statusFilter: "open" as "open" | "closed" | "all"
  }),
  actions: {
    async refresh() {
      this.loading = true;
      this.error = null;
      try {
        this.tickets = await listTickets(this.statusFilter);
      } catch (e: unknown) {
        this.error = e instanceof Error ? e.message : "加载工单失败";
      } finally {
        this.loading = false;
      }
    },
    setStatusFilter(status: "open" | "closed" | "all") {
      this.statusFilter = status;
      this.refresh();
    },
    async select(ticketId: string) {
      this.selectedTicket = await getTicket(ticketId);
    },
    async reply(content: string) {
      if (!this.selectedTicket) return;
      await replyTicket(this.selectedTicket.ticket_id, content);
      await this.select(this.selectedTicket.ticket_id);
    },
    async close() {
      if (!this.selectedTicket) return;
      await closeTicket(this.selectedTicket.ticket_id);
      this.selectedTicket = null;
      await this.refresh();
    }
  }
});
