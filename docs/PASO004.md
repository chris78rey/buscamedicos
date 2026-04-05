# Paso 4: Teleconsulta + Receta + Indicaciones

## Nuevas tablas

- `teleconsultation_sessions` - sesiones de videollamada externa
- `clinical_notes_simple` - nota clínica simple por cita
- `clinical_note_versions` - versionado de nota clínica
- `prescriptions` - recetas digitales
- `prescription_items` - items de receta
- `care_instructions` - indicaciones de cuidado
- `clinical_files` - archivos clínicos por cita
- `clinical_access_audit` - auditoría de acceso clínico

## Endpoints nuevos

### Professional
- `POST /api/v1/professionals/me/appointments/{id}/teleconsultation` - crear sesión
- `GET /api/v1/professionals/me/appointments/{id}/teleconsultation` - ver sesión
- `POST /api/v1/professionals/me/appointments/{id}/teleconsultation/start` - iniciar
- `POST /api/v1/professionals/me/appointments/{id}/teleconsultation/end` - finalizar
- `POST /api/v1/professionals/me/appointments/{id}/teleconsultation/cancel` - cancelar
- `GET/PUT /api/v1/professionals/me/appointments/{id}/clinical-note` - nota clínica
- `POST /api/v1/professionals/me/appointments/{id}/clinical-note/sign-simple` - firmar
- `GET/POST/PUT /api/v1/professionals/me/appointments/{id}/prescription` - recetas
- `POST /api/v1/professionals/me/appointments/{id}/prescription/{id}/issue` - emitir
- `POST /api/v1/professionals/me/appointments/{id}/prescription/{id}/revoke` - revocar
- `GET/PUT /api/v1/professionals/me/appointments/{id}/care-instructions`
- `POST /api/v1/professionals/me/appointments/{id}/care-instructions/issue`
- `POST/GET/DELETE /api/v1/professionals/me/appointments/{id}/clinical-files`

### Patient
- `GET /api/v1/patient/appointments/{id}/teleconsultation`
- `POST /api/v1/patient/appointments/{id}/teleconsultation/join-log`
- `GET /api/v1/patient/appointments/{id}/clinical-note`
- `GET /api/v1/patient/appointments/{id}/prescription`
- `GET /api/v1/patient/appointments/{id}/care-instructions`
- `GET /api/v1/patient/appointments/{id}/clinical-files`

### Admin
- `GET /api/v1/admin/appointments/{id}/teleconsultation-meta`
- `GET /api/v1/admin/clinical-access-audit`

## Reglas clave

- Solo citas pagadas con modalidad teleconsulta pueden crear teleconsulta
- Solo el profesional de la cita puede crear/editar contenido clínico
- Admin no puede ver contenido clínico
- Toda lectura clínica genera `clinical_access_audit`
- Toda escritura clínica genera `clinical_access_audit` + `audit_event`
- `private_professional_note` nunca es visible al paciente
- Nota clínica versiona automáticamente en cada actualización
