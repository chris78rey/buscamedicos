Sí. Se deja el paquete mínimo para que el programador implemente **dashboard por rol + búsqueda pública + detalle + slots + reserva + mis citas**. El backend ya tiene montados `users`, `public` y `patient` bajo `/api/v1/users`, `/api/v1/public` y `/api/v1/patient`; además ya existen la búsqueda pública, el detalle/slots y la creación/listado de citas del paciente. Lo que falta para que Flutter lo use bien es devolver roles en `/users/me` y conectar la UI.

Se deja en 4 archivos. El flujo completo que queda funcional es el de **paciente**; profesional y superadmin quedan con dashboard base, que es lo correcto para esta etapa.

## 1) Reemplazar `backend_api/app/routers/users.py`

```python
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class UserMeResponse(BaseModel):
    id: str
    email: str
    is_email_verified: bool
    status: str
    role_codes: List[str]
    primary_role: Optional[str] = None
    actor_type: str

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    await current_user.awaitable_attrs.roles
    role_codes = sorted([role.code for role in current_user.roles])

    primary_role = None
    for candidate in [
        "super_admin",
        "patient",
        "professional",
        "admin_validation",
        "admin_support",
    ]:
        if candidate in role_codes:
            primary_role = candidate
            break

    actor_type = "unknown"
    if any(code in role_codes for code in ["super_admin", "admin_validation", "admin_support"]):
        actor_type = "admin"
    elif "patient" in role_codes:
        actor_type = "patient"
    elif "professional" in role_codes:
        actor_type = "professional"

    return UserMeResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_email_verified=bool(current_user.is_email_verified),
        status=str(current_user.status),
        role_codes=role_codes,
        primary_role=primary_role,
        actor_type=actor_type,
    )


@router.patch("/me")
async def update_me(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for key, value in data.items():
        if hasattr(current_user, key) and key not in ["id", "email", "password_hash"]:
            setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user
```

Con esto, el frontend ya podrá decidir si debe abrir dashboard de paciente, profesional o admin. Hoy `GET /users/me` solo devuelve `id`, `email`, `is_email_verified` y `status`, por eso todavía no alcanza para orquestar por rol. 

---

## 2) Reemplazar `app_flutter/lib/services/api_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  static Map<String, String> _authHeaders(
    String token, {
    bool json = false,
  }) {
    final headers = <String, String>{
      'Authorization': 'Bearer $token',
    };
    if (json) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  static dynamic _decodeBody(http.Response response) {
    if (response.body.isEmpty) return null;
    return jsonDecode(response.body);
  }

  static Exception _httpException(String action, http.Response response) {
    return Exception('$action failed (${response.statusCode}): ${response.body}');
  }

  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Login', response);
  }

  static Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String nationalId,
    required String phone,
    required bool isPatient,
  }) async {
    final endpoint = isPatient
        ? '/auth/register/patient'
        : '/auth/register/professional';

    final response = await http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'national_id': nationalId,
        'phone': phone,
        if (!isPatient) 'professional_type': 'general',
      }),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Registration', response);
  }

  static Future<Map<String, dynamic>> getCurrentUser(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/users/me'),
      headers: _authHeaders(token),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Get current user', response);
  }

  static Future<List<dynamic>> searchProfessionals(
    String token, {
    String? city,
    String? specialty,
    String? modality,
    String? availableDate,
  }) async {
    final query = <String, String>{};

    if (city != null && city.trim().isNotEmpty) {
      query['city'] = city.trim();
    }
    if (specialty != null && specialty.trim().isNotEmpty) {
      query['specialty'] = specialty.trim();
    }
    if (modality != null && modality.trim().isNotEmpty) {
      query['modality'] = modality.trim();
    }
    if (availableDate != null && availableDate.trim().isNotEmpty) {
      query['available_date'] = availableDate.trim();
    }

    final uri = Uri.parse('$baseUrl/public/professionals').replace(
      queryParameters: query.isEmpty ? null : query,
    );

    final response = await http.get(
      uri,
      headers: token.isEmpty ? {} : _authHeaders(token),
    );

    if (response.statusCode == 200) {
      return List<dynamic>.from(_decodeBody(response) as List);
    }

    throw _httpException('Search professionals', response);
  }

  static Future<Map<String, dynamic>> getPublicProfessional(
    String token,
    String identifier,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/public/professionals/$identifier'),
      headers: token.isEmpty ? {} : _authHeaders(token),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Get public professional', response);
  }

  static Future<List<dynamic>> getSlots(
    String token,
    String professionalId,
    String date,
    String modality,
  ) async {
    final uri = Uri.parse('$baseUrl/public/professionals/$professionalId/slots')
        .replace(
      queryParameters: {
        'date': date,
        'modality': modality,
      },
    );

    final response = await http.get(
      uri,
      headers: token.isEmpty ? {} : _authHeaders(token),
    );

    if (response.statusCode == 200) {
      return List<dynamic>.from(_decodeBody(response) as List);
    }

    throw _httpException('Get slots', response);
  }

  static Future<Map<String, dynamic>> createAppointment(
    String token, {
    required String professionalId,
    required String modalityCode,
    required DateTime scheduledStart,
    String? patientNote,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/patient/appointments'),
      headers: _authHeaders(token, json: true),
      body: jsonEncode({
        'professional_id': professionalId,
        'modality_code': modalityCode,
        'scheduled_start': scheduledStart.toIso8601String(),
        if (patientNote != null && patientNote.trim().isNotEmpty)
          'patient_note': patientNote.trim(),
      }),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Create appointment', response);
  }

  static Future<List<dynamic>> getMyAppointments(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/patient/appointments'),
      headers: _authHeaders(token),
    );

    if (response.statusCode == 200) {
      return List<dynamic>.from(_decodeBody(response) as List);
    }

    throw _httpException('Get my appointments', response);
  }

  // ====== BLOQUE CLÍNICO YA EXISTENTE ======

  static Future<Map<String, dynamic>> getTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/patient/appointments/$appointmentId/teleconsultation',
      ),
      headers: _authHeaders(token),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Get teleconsultation', response);
  }

  static Future<Map<String, dynamic>> getClinicalNote(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/patient/appointments/$appointmentId/clinical-note'),
      headers: _authHeaders(token),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Get clinical note', response);
  }

  static Future<Map<String, dynamic>> getPrescription(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/patient/appointments/$appointmentId/prescription'),
      headers: _authHeaders(token),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Get prescription', response);
  }

  static Future<Map<String, dynamic>> getCareInstructions(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/patient/appointments/$appointmentId/care-instructions',
      ),
      headers: _authHeaders(token),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Get care instructions', response);
  }

  static Future<Map<String, dynamic>> getProfessionalTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/teleconsultation',
      ),
      headers: _authHeaders(token),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Get professional teleconsultation', response);
  }

  static Future<void> startTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/teleconsultation/start',
      ),
      headers: _authHeaders(token),
    );

    if (response.statusCode != 200) {
      throw _httpException('Start teleconsultation', response);
    }
  }

  static Future<void> endTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/teleconsultation/end',
      ),
      headers: _authHeaders(token),
    );

    if (response.statusCode != 200) {
      throw _httpException('End teleconsultation', response);
    }
  }

  static Future<Map<String, dynamic>> getProfessionalClinicalNote(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/clinical-note',
      ),
      headers: _authHeaders(token),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Get professional clinical note', response);
  }

  static Future<void> updateClinicalNote(
    String token,
    String appointmentId,
    Map<String, dynamic> data,
  ) async {
    final response = await http.put(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/clinical-note',
      ),
      headers: _authHeaders(token, json: true),
      body: jsonEncode(data),
    );

    if (response.statusCode != 200) {
      throw _httpException('Update clinical note', response);
    }
  }

  static Future<Map<String, dynamic>> createPrescription(
    String token,
    String appointmentId,
    Map<String, dynamic> data,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/prescription',
      ),
      headers: _authHeaders(token, json: true),
      body: jsonEncode(data),
    );
    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }
    throw _httpException('Create prescription', response);
  }

  static Future<void> issuePrescription(
    String token,
    String appointmentId,
    String prescriptionId,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/prescription/$prescriptionId/issue',
      ),
      headers: _authHeaders(token),
    );

    if (response.statusCode != 200) {
      throw _httpException('Issue prescription', response);
    }
  }

  static Future<void> updateCareInstructions(
    String token,
    String appointmentId,
    Map<String, dynamic> data,
  ) async {
    final response = await http.put(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/care-instructions',
      ),
      headers: _authHeaders(token, json: true),
      body: jsonEncode(data),
    );

    if (response.statusCode != 200) {
      throw _httpException('Update care instructions', response);
    }
  }

  static Future<void> issueCareInstructions(
    String token,
    String appointmentId,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/care-instructions/issue',
      ),
      headers: _authHeaders(token),
    );

    if (response.statusCode != 200) {
      throw _httpException('Issue care instructions', response);
    }
  }
}
```

Aquí se corrige además el consumo de usuario actual para usar **`/users/me`**, porque el router `users` está montado bajo `/api/v1/users` en `main.py`.

---

## 3) Reemplazar `app_flutter/lib/features/search/search_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class SearchScreen extends StatefulWidget {
  final String token;

  const SearchScreen({super.key, required this.token});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  List<dynamic> _results = [];
  bool _loading = false;
  String? _selectedCity;
  String _selectedModality = 'in_person_consultorio';
  final _specialtyController = TextEditingController();
  DateTime? _selectedDate;

  @override
  void dispose() {
    _specialtyController.dispose();
    super.dispose();
  }

  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? now.add(const Duration(days: 1)),
      firstDate: now,
      lastDate: now.add(const Duration(days: 180)),
    );

    if (picked != null) {
      setState(() => _selectedDate = picked);
    }
  }

  Future<void> _search() async {
    FocusScope.of(context).unfocus();
    setState(() => _loading = true);

    try {
      final data = await ApiService.searchProfessionals(
        widget.token,
        city: _selectedCity,
        specialty: _specialtyController.text.trim(),
        modality: _selectedModality,
        availableDate: _selectedDate != null ? _formatDate(_selectedDate!) : null,
      );

      if (!mounted) return;
      setState(() {
        _results = data;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error buscando profesionales: $e')),
      );
    }
  }

  @override
  void initState() {
    super.initState();
    _search();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Buscar profesionales'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: 220,
                  child: DropdownButtonFormField<String>(
                    value: _selectedCity,
                    decoration: const InputDecoration(
                      labelText: 'Ciudad',
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(value: null, child: Text('Todas')),
                      DropdownMenuItem(value: 'Quito', child: Text('Quito')),
                      DropdownMenuItem(
                        value: 'Guayaquil',
                        child: Text('Guayaquil'),
                      ),
                      DropdownMenuItem(value: 'Cuenca', child: Text('Cuenca')),
                    ],
                    onChanged: (value) => setState(() => _selectedCity = value),
                  ),
                ),
                SizedBox(
                  width: 220,
                  child: DropdownButtonFormField<String>(
                    value: _selectedModality,
                    decoration: const InputDecoration(
                      labelText: 'Modalidad',
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'in_person_consultorio',
                        child: Text('Consultorio'),
                      ),
                      DropdownMenuItem(
                        value: 'teleconsulta',
                        child: Text('Teleconsulta'),
                      ),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setState(() => _selectedModality = value);
                      }
                    },
                  ),
                ),
                SizedBox(
                  width: 220,
                  child: TextField(
                    controller: _specialtyController,
                    decoration: const InputDecoration(
                      labelText: 'Especialidad',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                SizedBox(
                  width: 220,
                  child: OutlinedButton(
                    onPressed: _pickDate,
                    child: Text(
                      _selectedDate == null
                          ? 'Fecha opcional'
                          : 'Fecha: ${_formatDate(_selectedDate!)}',
                    ),
                  ),
                ),
                SizedBox(
                  width: 180,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _search,
                    child: _loading
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Buscar'),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _results.isEmpty
                    ? const Center(
                        child: Text('No existen profesionales disponibles'),
                      )
                    : ListView.separated(
                        itemCount: _results.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (_, i) {
                          final item = _results[i] as Map<String, dynamic>;
                          return ListTile(
                            title: Text(item['public_display_name'] ?? 'Sin nombre'),
                            subtitle: Text(
                              [
                                item['public_title'] ?? '',
                                item['city'] ?? '',
                                item['consultation_price'] != null
                                    ? '\$${item['consultation_price']}'
                                    : '',
                              ].where((e) => e.toString().trim().isNotEmpty).join(' • '),
                            ),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () {
                              final identifier =
                                  (item['public_slug'] ?? item['professional_id']).toString();
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => ProfessionalDetailScreen(
                                    token: widget.token,
                                    professionalId: item['professional_id'].toString(),
                                    professionalIdentifier: identifier,
                                  ),
                                ),
                              );
                            },
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

class ProfessionalDetailScreen extends StatefulWidget {
  final String token;
  final String professionalId;
  final String professionalIdentifier;

  const ProfessionalDetailScreen({
    super.key,
    required this.token,
    required this.professionalId,
    required this.professionalIdentifier,
  });

  @override
  State<ProfessionalDetailScreen> createState() =>
      _ProfessionalDetailScreenState();
}

class _ProfessionalDetailScreenState extends State<ProfessionalDetailScreen> {
  Map<String, dynamic>? _profile;
  List<dynamic> _slots = [];
  bool _loadingProfile = true;
  bool _loadingSlots = true;
  DateTime _selectedDate = DateTime.now().add(const Duration(days: 1));
  String _selectedModality = 'in_person_consultorio';

  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }

  String _formatDateTime(String raw) {
    final dt = DateTime.tryParse(raw);
    if (dt == null) return raw;
    final y = dt.year.toString().padLeft(4, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final d = dt.day.toString().padLeft(2, '0');
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    return '$y-$m-$d $hh:$mm';
  }

  Future<void> _loadProfile() async {
    try {
      final profile = await ApiService.getPublicProfessional(
        widget.token,
        widget.professionalIdentifier,
      );
      if (!mounted) return;
      setState(() {
        _profile = profile;
        _loadingProfile = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loadingProfile = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error cargando perfil: $e')),
      );
    }
  }

  Future<void> _loadSlots() async {
    setState(() => _loadingSlots = true);
    try {
      final slots = await ApiService.getSlots(
        widget.token,
        widget.professionalId,
        _formatDate(_selectedDate),
        _selectedModality,
      );
      if (!mounted) return;
      setState(() {
        _slots = slots;
        _loadingSlots = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loadingSlots = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error cargando horarios: $e')),
      );
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 180)),
    );

    if (picked != null) {
      setState(() => _selectedDate = picked);
      await _loadSlots();
    }
  }

  Future<void> _bookSlot(String rawStart) async {
    final start = DateTime.parse(rawStart);

    final accepted = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Confirmar reserva'),
        content: Text('Reservar el horario ${_formatDateTime(rawStart)} ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('No'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Sí'),
          ),
        ],
      ),
    );

    if (accepted != true) return;

    try {
      final result = await ApiService.createAppointment(
        widget.token,
        professionalId: widget.professionalId,
        modalityCode: _selectedModality,
        scheduledStart: start,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Cita creada: ${result['public_code'] ?? result['id'] ?? ''}',
          ),
        ),
      );
      await _loadSlots();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error reservando cita: $e')),
      );
    }
  }

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _loadSlots();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_profile?['public_display_name'] ?? 'Perfil profesional'),
      ),
      body: _loadingProfile
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async {
                await _loadProfile();
                await _loadSlots();
              },
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Text(
                    _profile?['public_title'] ?? '',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(_profile?['public_bio'] ?? 'Sin biografía pública'),
                  const SizedBox(height: 16),
                  Text('Ciudad: ${_profile?['city'] ?? ''}'),
                  Text('Provincia: ${_profile?['province'] ?? ''}'),
                  Text('Precio: ${_profile?['consultation_price'] ?? 'No definido'}'),
                  const SizedBox(height: 24),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      OutlinedButton(
                        onPressed: _pickDate,
                        child: Text('Fecha: ${_formatDate(_selectedDate)}'),
                      ),
                      SizedBox(
                        width: 220,
                        child: DropdownButtonFormField<String>(
                          value: _selectedModality,
                          decoration: const InputDecoration(
                            labelText: 'Modalidad',
                            border: OutlineInputBorder(),
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'in_person_consultorio',
                              child: Text('Consultorio'),
                            ),
                            DropdownMenuItem(
                              value: 'teleconsulta',
                              child: Text('Teleconsulta'),
                            ),
                          ],
                          onChanged: (value) async {
                            if (value != null) {
                              setState(() => _selectedModality = value);
                              await _loadSlots();
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Horarios disponibles',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  if (_loadingSlots)
                    const Center(child: CircularProgressIndicator())
                  else if (_slots.isEmpty)
                    const Text('No hay horarios disponibles para la selección actual')
                  else
                    ..._slots
                        .where((slot) => slot['is_available'] == true)
                        .map(
                          (slot) => Card(
                            child: ListTile(
                              title: Text(_formatDateTime(slot['start'].toString())),
                              subtitle: Text('Fin: ${_formatDateTime(slot['end'].toString())}'),
                              trailing: ElevatedButton(
                                onPressed: () => _bookSlot(slot['start'].toString()),
                                child: const Text('Reservar'),
                              ),
                            ),
                          ),
                        ),
                ],
              ),
            ),
    );
  }
}

class MyAppointmentsScreen extends StatefulWidget {
  final String token;

  const MyAppointmentsScreen({super.key, required this.token});

  @override
  State<MyAppointmentsScreen> createState() => _MyAppointmentsScreenState();
}

class _MyAppointmentsScreenState extends State<MyAppointmentsScreen> {
  bool _loading = true;
  List<dynamic> _appointments = [];

  String _formatDateTime(dynamic raw) {
    final dt = DateTime.tryParse(raw?.toString() ?? '');
    if (dt == null) return raw?.toString() ?? '';
    final y = dt.year.toString().padLeft(4, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final d = dt.day.toString().padLeft(2, '0');
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    return '$y-$m-$d $hh:$mm';
  }

  Future<void> _load() async {
    setState(() => _loading = true);

    try {
      final items = await ApiService.getMyAppointments(widget.token);
      if (!mounted) return;
      setState(() {
        _appointments = items;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error cargando citas: $e')),
      );
    }
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis citas'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: _appointments.isEmpty
                  ? ListView(
                      children: const [
                        SizedBox(height: 120),
                        Center(child: Text('No existen citas registradas')),
                      ],
                    )
                  : ListView.separated(
                      itemCount: _appointments.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (_, i) {
                        final item = _appointments[i] as Map<String, dynamic>;
                        return ListTile(
                          title: Text('Cita ${item['public_code'] ?? item['id'] ?? ''}'),
                          subtitle: Text(
                            'Estado: ${item['status'] ?? ''}\n'
                            'Inicio: ${_formatDateTime(item['scheduled_start'])}',
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}
```

El backend ya contempla este recorrido mínimo: listado público, detalle público, slots y creación/listado de citas del paciente.

---

## 4) Reemplazar `app_flutter/lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'features/search/search_screen.dart';
import 'services/api_service.dart';

void main() => runApp(const BuscaMedicosApp());

class BuscaMedicosApp extends StatelessWidget {
  const BuscaMedicosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BuscaMedicos',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const AppBootstrapScreen(),
    );
  }
}

class AppBootstrapScreen extends StatefulWidget {
  const AppBootstrapScreen({super.key});

  @override
  State<AppBootstrapScreen> createState() => _AppBootstrapScreenState();
}

class _AppBootstrapScreenState extends State<AppBootstrapScreen> {
  bool _isLoading = true;
  String? _token;

  @override
  void initState() {
    super.initState();
    _loadToken();
  }

  Future<void> _loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');

    if (!mounted) return;
    setState(() {
      _token = token;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_token != null && _token!.isNotEmpty) {
      return HomeScreen(token: _token!);
    }

    return const LoginScreen();
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    FocusScope.of(context).unfocus();
    setState(() => _isLoading = true);

    try {
      final result = await ApiService.login(
        _emailController.text.trim(),
        _passwordController.text,
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', result['access_token'].toString());

      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => HomeScreen(token: result['access_token'].toString()),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error de login: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BuscaMedicos')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Iniciar sesión',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _isLoading ? null : _login(),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _login,
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Login'),
                  ),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: _isLoading
                      ? null
                      : () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const RegisterScreen(),
                            ),
                          ),
                  child: const Text('Crear cuenta'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _nationalIdController = TextEditingController();
  final _phoneController = TextEditingController();

  bool _isPatient = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _nationalIdController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    FocusScope.of(context).unfocus();
    setState(() => _isLoading = true);

    try {
      final result = await ApiService.register(
        email: _emailController.text.trim(),
        password: _passwordController.text,
        firstName: _firstNameController.text.trim(),
        lastName: _lastNameController.text.trim(),
        nationalId: _nationalIdController.text.trim(),
        phone: _phoneController.text.trim(),
        isPatient: _isPatient,
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', result['access_token'].toString());

      if (!mounted) return;
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(
          builder: (_) => HomeScreen(token: result['access_token'].toString()),
        ),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error de registro: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Registro')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                TextField(
                  controller: _firstNameController,
                  decoration: const InputDecoration(
                    labelText: 'Nombres',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _lastNameController,
                  decoration: const InputDecoration(
                    labelText: 'Apellidos',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _nationalIdController,
                  decoration: const InputDecoration(
                    labelText: 'Cédula',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _phoneController,
                  decoration: const InputDecoration(
                    labelText: 'Teléfono',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                SwitchListTile(
                  title: const Text('Registrarse como paciente'),
                  value: _isPatient,
                  onChanged: _isLoading
                      ? null
                      : (v) => setState(() => _isPatient = v),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _register,
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Registrarse'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  final String token;

  const HomeScreen({super.key, required this.token});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic>? _userData;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    try {
      final data = await ApiService.getCurrentUser(widget.token);
      if (!mounted) return;
      setState(() {
        _userData = data;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error cargando usuario: $e')),
      );
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');

    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  Widget _buildBody() {
    final user = _userData ?? {};
    final actorType = (user['actor_type'] ?? '').toString();
    final roles = List<String>.from(user['role_codes'] ?? const []);

    if (actorType == 'patient' || roles.contains('patient')) {
      return PatientDashboard(
        token: widget.token,
        userData: user,
      );
    }

    if (actorType == 'professional' || roles.contains('professional')) {
      return ProfessionalDashboard(userData: user);
    }

    if (actorType == 'admin' ||
        roles.contains('super_admin') ||
        roles.contains('admin_validation') ||
        roles.contains('admin_support')) {
      return AdminDashboard(userData: user);
    }

    return UnknownDashboard(userData: user);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BuscaMedicos'),
        actions: [
          TextButton(
            onPressed: _logout,
            child: const Text('Logout'),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _buildBody(),
    );
  }
}

class PatientDashboard extends StatelessWidget {
  final String token;
  final Map<String, dynamic> userData;

  const PatientDashboard({
    super.key,
    required this.token,
    required this.userData,
  });

  @override
  Widget build(BuildContext context) {
    final email = userData['email']?.toString() ?? '';

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Panel de paciente',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text('Usuario: $email'),
        const SizedBox(height: 24),
        Card(
          child: ListTile(
            title: const Text('Buscar profesionales'),
            subtitle: const Text(
              'Permite listar perfiles públicos y revisar horarios',
            ),
            trailing: const Icon(Icons.search),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => SearchScreen(token: token),
                ),
              );
            },
          ),
        ),
        Card(
          child: ListTile(
            title: const Text('Mis citas'),
            subtitle: const Text(
              'Permite revisar las reservas realizadas',
            ),
            trailing: const Icon(Icons.calendar_month),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => MyAppointmentsScreen(token: token),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class ProfessionalDashboard extends StatelessWidget {
  final Map<String, dynamic> userData;

  const ProfessionalDashboard({
    super.key,
    required this.userData,
  });

  @override
  Widget build(BuildContext context) {
    final email = userData['email']?.toString() ?? '';

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Panel profesional',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text('Usuario: $email'),
        const SizedBox(height: 24),
        const Card(
          child: ListTile(
            title: Text('Dashboard base habilitado'),
            subtitle: Text(
              'El siguiente bloque para profesional será perfil público, disponibilidad y gestión de citas.',
            ),
          ),
        ),
      ],
    );
  }
}

class AdminDashboard extends StatelessWidget {
  final Map<String, dynamic> userData;

  const AdminDashboard({
    super.key,
    required this.userData,
  });

  @override
  Widget build(BuildContext context) {
    final email = userData['email']?.toString() ?? '';

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Panel administrativo',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text('Usuario: $email'),
        const SizedBox(height: 24),
        const Card(
          child: ListTile(
            title: Text('Dashboard base habilitado'),
            subtitle: Text(
              'El siguiente bloque para admin será operaciones simples, auditoría y seguimiento.',
            ),
          ),
        ),
      ],
    );
  }
}

class UnknownDashboard extends StatelessWidget {
  final Map<String, dynamic> userData;

  const UnknownDashboard({
    super.key,
    required this.userData,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'No fue posible resolver el rol del usuario.\n\nRespuesta actual: $userData',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
```

---

## Validación que debe pasar

1. Registro o login.
2. `HomeScreen` consulta `GET /api/v1/users/me`.
3. Si el rol es `patient`, abre el panel de paciente.
4. Desde ahí se puede:

   * buscar profesionales,
   * abrir detalle,
   * consultar slots,
   * reservar,
   * revisar “Mis citas”.
5. Si el rol es `professional` o `super_admin`, abre dashboard base.

El detalle importante es que la búsqueda pública solo mostrará profesionales **activos**, **aprobados** y con perfil **público**. Si no aparecen resultados, casi siempre será porque todavía no existe un profesional con `status = active`, `onboarding_status = approved` e `is_public = true`.

## Comandos para probar

```powershell
cd G:\codex_projects\buscamedicos\app_flutter
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000/api/v1
```

## Texto corto para pasarle al programador

Se debe implementar el siguiente paso real de producto con cambios mínimos y coherentes: 1) devolver `role_codes`, `primary_role` y `actor_type` desde `GET /api/v1/users/me`, 2) corregir Flutter para consumir `/api/v1/users/me`, 3) reemplazar `ApiService` para incluir búsqueda pública, detalle público, slots, reserva y mis citas, y 4) reemplazar `main.dart` para que haga dashboard por rol. El flujo funcional prioritario debe quedar del lado paciente: login → dashboard paciente → búsqueda → detalle → slots → reserva → mis citas.
