<script setup lang="ts">
definePageMeta({
  layout: 'default',
  middleware: ['auth', 'role'],
  roles: ['privacy_auditor'],
})
</script>

<template>
  <v-container class="py-10">
    <FeaturePlaceholder
      description="Pantalla inicial para auditoria de accesos disponible para usuarios con rol privacy_auditor."
      title="Auditoria de accesos"
    />
  </v-container>
</template>
