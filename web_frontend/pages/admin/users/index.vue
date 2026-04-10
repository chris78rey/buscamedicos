<script setup lang="ts">
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'role'],
  roles: ['super_admin'],
})

const { apiFetch } = useApi()

const loading = ref(false)
const saving = ref(false)
const users = ref<any[]>([])
const roles = ref<any[]>([])
const showCreateDialog = ref(false)

const newUser = ref({
  email: '',
  password: '',
  role_code: ''
})

async function loadData() {
  loading.value = true
  try {
    const [usersList, rolesList] = await Promise.all([
      apiFetch('/admin/management/users'),
      apiFetch('/admin/management/roles')
    ])
    users.value = usersList
    roles.value = rolesList
  } catch (e) {
    console.error('Error al cargar staff', e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newUser.value.email || !newUser.value.password || !newUser.value.role_code) return
  
  saving.value = true
  try {
    await apiFetch('/admin/management/users', {
      method: 'POST',
      body: newUser.value
    })
    showCreateDialog.value = false
    newUser.value = { email: '', password: '', role_code: '' }
    await loadData()
  } catch (e) {
    alert('Error al crear usuario. Verifique si el email ya existe.')
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">Gestión de Staff</h1>
        <p class="text-subtitle-1 text-medium-emphasis">Administra las cuentas de tu equipo administrativo.</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-account-plus" rounded="lg" @click="showCreateDialog = true">
        Nuevo Administrador
      </v-btn>
    </div>

    <v-card rounded="xl" elevation="2">
      <v-table>
        <thead>
          <tr>
            <th>Email</th>
            <th>Estado</th>
            <th>Roles Activos</th>
            <th class="text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.email }}</td>
            <td>
              <v-chip size="x-small" :color="user.status === 'active' ? 'success' : 'grey'">
                {{ user.status }}
              </v-chip>
            </td>
            <td>
              <v-chip v-for="role in user.roles" :key="role" size="x-small" variant="outlined" class="mr-1">
                {{ role }}
              </v-chip>
            </td>
            <td class="text-right">
              <v-btn icon="mdi-dots-vertical" variant="text" size="small"></v-btn>
            </td>
          </tr>
          <tr v-if="users.length === 0 && !loading">
            <td colspan="4" class="text-center py-4">No hay usuarios de staff encontrados.</td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- Diálogo de creación -->
    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card rounded="xl" title="Crear Nuevo Administrador">
        <v-card-text>
          <v-text-field v-model="newUser.email" label="Email institucional" variant="outlined" class="mb-2" type="email"></v-text-field>
          <v-text-field v-model="newUser.password" label="Contraseña temporal" type="password" variant="outlined" class="mb-2"></v-text-field>
          <v-select 
            v-model="newUser.role_code" 
            :items="roles" 
            item-title="name" 
            item-value="code"
            label="Rol de acceso" 
            variant="outlined"
          ></v-select>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showCreateDialog = false" rounded="lg">Cancelar</v-btn>
          <v-btn color="primary" :loading="saving" @click="handleCreate" rounded="lg" variant="flat">Crear Cuenta</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
