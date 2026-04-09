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

  static Future<List<dynamic>> getProfessionalAppointments(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/professionals/me/appointments'),
      headers: _authHeaders(token),
    );

    if (response.statusCode == 200) {
      return List<dynamic>.from(_decodeBody(response) as List);
    }

    throw _httpException('Get professional appointments', response);
  }

  static Future<Map<String, dynamic>> confirmAppointment(
    String token,
    String appointmentId,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/professionals/me/appointments/$appointmentId/confirm'),
      headers: _authHeaders(token, json: true),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Confirm appointment', response);
  }

  static Future<Map<String, dynamic>> cancelAppointment(
    String token,
    String appointmentId, {
    String? reason,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/professionals/me/appointments/$appointmentId/cancel'),
      headers: _authHeaders(token, json: true),
      body: reason != null ? jsonEncode({'reason': reason}) : null,
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Cancel appointment', response);
  }

  static Future<Map<String, dynamic>> completeAppointment(
    String token,
    String appointmentId,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/professionals/me/appointments/$appointmentId/complete'),
      headers: _authHeaders(token, json: true),
    );

    if (response.statusCode == 200) {
      return Map<String, dynamic>.from(_decodeBody(response) as Map);
    }

    throw _httpException('Complete appointment', response);
  }
}