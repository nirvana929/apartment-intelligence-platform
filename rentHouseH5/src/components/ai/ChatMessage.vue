<script setup lang="ts">
interface Card {
  title: string;
  subtitle?: string;
  image?: string;
  tags?: string[];
  price?: string;
}

defineProps<{
  role: "user" | "assistant";
  content: string;
  cards?: Card[];
}>();
</script>

<template>
  <div class="chat-message" :class="[role]">
    <div class="bubble">
      <div class="text">{{ content }}</div>
      <div v-if="cards && cards.length" class="cards">
        <div v-for="(card, index) in cards" :key="index" class="card">
          <img v-if="card.image" :src="card.image" class="card-image" />
          <div class="card-body">
            <div class="card-title">{{ card.title }}</div>
            <div v-if="card.subtitle" class="card-subtitle">
              {{ card.subtitle }}
            </div>
            <div v-if="card.price" class="card-price">{{ card.price }}</div>
            <div v-if="card.tags?.length" class="card-tags">
              <span v-for="tag in card.tags" :key="tag" class="tag">{{
                tag
              }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.chat-message {
  display: flex;
  margin-bottom: 12px;
  padding: 0 12px;

  &.user {
    justify-content: flex-end;

    .bubble {
      background-color: #1989fa;
      color: #fff;
      border-radius: 12px 12px 2px 12px;
    }
  }

  &.assistant {
    justify-content: flex-start;

    .bubble {
      background-color: #f5f5f5;
      color: #333;
      border-radius: 12px 12px 12px 2px;
    }
  }
}

.bubble {
  max-width: 80%;
  padding: 10px 14px;
  word-break: break-word;
  line-height: 1.5;
  font-size: 14px;
}

.cards {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  color: #333;

  .card-image {
    width: 100%;
    height: 120px;
    object-fit: cover;
  }

  .card-body {
    padding: 8px 10px;
  }

  .card-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .card-subtitle {
    font-size: 12px;
    color: #999;
    margin-bottom: 4px;
  }

  .card-price {
    font-size: 16px;
    color: #ff6b35;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .card-tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;

    .tag {
      font-size: 11px;
      background: #e8f4ff;
      color: #1989fa;
      padding: 2px 6px;
      border-radius: 4px;
    }
  }
}
</style>
