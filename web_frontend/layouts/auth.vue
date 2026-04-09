<template>
  <v-app>
    <v-main class="bg-grey-lighten-4">
      <v-container class="fill-height d-flex align-center justify-center py-12">
        <div class="w-100" style="max-width: 520px;">
          <slot />
        </div>
      </v-container>
    </v-main>
  </v-app>
</template>
