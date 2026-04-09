<script setup lang="ts">
definePageMeta({
  layout: 'professional',
  middleware: ['auth', 'role'],
  roles: ['professional'],
})

const route = useRoute()
</script>

<template>
  <FeaturePlaceholder
    :description="`Sala de teleconsulta para la cita ${route.params.appointmentId} pendiente de integracion.`"
    title="Teleconsulta"
  />
</template>
