<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_moderation'],
})

const items = [
  {
    title: 'Listado de casos',
    description: 'Mostrará los casos abiertos, en revisión, resueltos y descartados.',
    status: 'Pendiente de endpoint final',
    icon: 'mdi-clipboard-search-outline',
  },
  {
    title: 'Detalle de caso',
    description: 'Permitirá revisar origen, objetivo, prioridad, historial y resultado.',
    status: 'Pendiente de endpoint final',
    icon: 'mdi-file-document-search-outline',
  },
  {
    title: 'Acciones del moderador',
    description: 'Asignar, agregar nota, resolver, descartar y aplicar acciones preventivas.',
    status: 'Pendiente de endpoint final',
    icon: 'mdi-shield-account-outline',
  },
]
</script>

<template>
  <v-container>
    <div class="d-flex align-center justify-space-between flex-wrap ga-4 mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-2">Casos de moderación</h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          Pantalla base mínima. La lógica final debe conectarse a los endpoints de moderación ya existentes.
        </p>
      </div>

      <v-chip color="warning" variant="flat">
        Placeholder funcional
      </v-chip>
    </div>

    <v-row>
      <v-col
        v-for="item in items"
        :key="item.title"
        cols="12"
        md="4"
      >
        <v-card rounded="xl" elevation="2" class="h-100">
          <v-card-item>
            <template #prepend>
              <v-avatar color="primary" variant="tonal">
                <v-icon>{{ item.icon }}</v-icon>
              </v-avatar>
            </template>
            <v-card-title>{{ item.title }}</v-card-title>
            <v-card-subtitle>{{ item.status }}</v-card-subtitle>
          </v-card-item>

          <v-card-text class="text-medium-emphasis">
            {{ item.description }}
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card rounded="xl" elevation="2" class="mt-6">
      <v-card-title>Contrato esperado</v-card-title>
      <v-card-text>
        Esta vista debe terminar conectándose con:
        <strong>listar casos</strong>, <strong>ver detalle</strong>,
        <strong>agregar nota</strong>, <strong>resolver</strong> y
        <strong>descartar</strong>.
      </v-card-text>
    </v-card>
  </v-container>
</template>
