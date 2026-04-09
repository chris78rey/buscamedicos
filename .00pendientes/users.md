Viewed seed.py:1-657

Para probar todo el flujo, te recomiendo usar estos usuarios que ya están creados en tu base de datos (siempre que hayas corrido el script `seed.py`):

### 1. Para probar la Agenda (Rol Profesional)
Usa cualquiera de estos para ver la página que acabamos de implementar (`/professional/appointments`):
*   **Email**: `prof001@demo.com` (puedes probar del `001` al `030`)
*   **Password**: `Test1234!`
*   **Acción**: Entra y verás su agenda con citas de ejemplo ya confirmadas.

### 2. Para acceso total (Rol Super Admin)
Usa tus credenciales de superusuario:
*   **Email**: `christian19782013@gmail.com`
*   **Password**: `cr19780302`
*   **Acción**: Podrás entrar a `/admin/dashboard` y gestionar privacidad, moderación y pagos.

### 3. Para buscar y reservar (Rol Paciente)
*   **Email**: `patient_demo@example.com`
*   **Password**: `Test1234!`
*   **Acción**: Podrás navegar por la lista de médicos y ver el proceso de reserva desde el punto de vista del cliente.

---

### 💡 Recordatorio de URLs:
*   **Login**: `http://localhost:3000/login`
*   **Dashboard Admin**: `http://localhost:3000/admin/dashboard`
*   **Agenda Médica**: `http://localhost:3000/professional/appointments`

**¡Pruébalo ahora y dime si logras entrar con `prof001@demo.com`!**