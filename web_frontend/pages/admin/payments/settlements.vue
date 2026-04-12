<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin', 'admin_support'],
})

const cards = [
  {
    title: 'Lotes pendientes',
    value: '0',
    subtitle: 'A la espera de generación',
    icon: 'mdi-cash-clock',
  },
  {
    title: 'Lotes pagados',
    value: '0',
    subtitle: 'Historial disponible luego',
    icon: 'mdi-cash-check',
  },
  {
    title: 'Total neto',
    value: '$0.00',
    subtitle: 'Valor referencial placeholder',
    icon: 'mdi-currency-usd',
  },
]
</script>

<template>
  <v-container>
    <div class="d-flex align-center justify-space-between flex-wrap ga-4 mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-2">Liquidaciones</h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          Base mínima para conciliación y pagos a profesionales.
        </p>
      </div>

      <v-chip color="warning" variant="flat">
        Placeholder funcional
      </v-chip>
    </div>

    <v-row>
      <v-col
        v-for="card in cards"
        :key="card.title"
        cols="12"
        md="4"
      >
        <v-card rounded="xl" elevation="2" class="h-100">
          <v-card-item>
            <template #prepend>
              <v-avatar color="primary" variant="tonal">
                <v-icon>{{ card.icon }}</v-icon>
              </v-avatar>
            </template>
            <v-card-title>{{ card.title }}</v-card-title>
            <v-card-subtitle>{{ card.subtitle }}</v-card-subtitle>
          </v-card-item>

          <v-card-text class="text-h4 font-weight-bold">
            {{ card.value }}
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card rounded="xl" elevation="2" class="mt-6">
      <v-card-title>Alcance pendiente</v-card-title>
      <v-card-text>
        Esta vista debe enlazarse después con generación de lotes, consulta de ítems,
        confirmación de pago y trazabilidad de estados.
      </v-card-text>
    </v-card>
  </v-container>
</template>
