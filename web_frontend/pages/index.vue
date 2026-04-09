<template>
  <v-container class="py-12">
    <v-row align="center" class="mb-10" justify="space-between">
      <v-col cols="12" md="6">
        <div class="mb-6 text-overline text-primary">
          Nuevo frontend web
        </div>
        <h1 class="text-h3 font-weight-bold mb-4">
          BuscaMedicos en Nuxt 4 + Vue 3 + Vuetify
        </h1>
        <p class="text-body-1 text-medium-emphasis mb-6">
          Scaffold inicial para autenticacion, sesion persistente y acceso por rol sin mover logica de negocio fuera de FastAPI.
        </p>
        <div class="d-flex flex-wrap ga-3">
          <v-btn color="primary" size="large" to="/login">
            Iniciar sesion
          </v-btn>
          <v-btn size="large" to="/register" variant="outlined">
            Crear cuenta
          </v-btn>
        </div>
      </v-col>

      <v-col cols="12" md="5">
        <v-card color="primary" rounded="xl" variant="flat">
          <v-card-text class="pa-8 text-white">
            <div class="text-overline mb-3">Phase 1</div>
            <div class="text-h5 font-weight-bold mb-4">Entregables activos</div>
            <v-list bg-color="transparent" density="comfortable">
              <v-list-item prepend-icon="mdi-check-circle" title="Login y registro" />
              <v-list-item prepend-icon="mdi-check-circle" title="Sesion con JWT en cookie" />
              <v-list-item prepend-icon="mdi-check-circle" title="Bootstrap con /auth/me y fallback /users/me" />
              <v-list-item prepend-icon="mdi-check-circle" title="Redireccion por rol" />
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
