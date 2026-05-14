<script setup lang="ts">
import AppointmentCard from "./cards/AppointmentCard.vue";
import ConfirmationCard from "./cards/ConfirmationCard.vue";
import HandoffCard from "./cards/HandoffCard.vue";
import LeaseCard from "./cards/LeaseCard.vue";
import MemoryCard from "./cards/MemoryCard.vue";
import RoomCard from "./cards/RoomCard.vue";

defineProps<{ card: Record<string, unknown> }>();
</script>

<template>
  <RoomCard v-if="card.type === 'room'" :card="card" />
  <LeaseCard v-else-if="card.type === 'lease_record'" :card="card" />
  <AppointmentCard v-else-if="card.type === 'appointment_record'" :card="card" />
  <ConfirmationCard v-else-if="String(card.type).includes('confirmation')" :card="card" />
  <MemoryCard v-else-if="String(card.type).startsWith('memory')" :card="card" />
  <HandoffCard v-else-if="card.type === 'handoff'" :card="card" />
  <pre v-else class="raw-card">{{ card }}</pre>
</template>
