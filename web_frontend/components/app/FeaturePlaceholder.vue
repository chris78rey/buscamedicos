<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <v-card rounded="xl">
    <v-card-item>
      <v-card-title>{{ title }}</v-card-title>
      <v-card-subtitle>Scaffold Phase 1</v-card-subtitle>
    </v-card-item>
    <v-card-text>
      <p class="text-body-1 mb-0">
        {{ description }}
      </p>
    </v-card-text>
  </v-card>
</template>
