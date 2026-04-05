import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  static Future<Map<String, dynamic>?> login(
    String email,
    String password,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Login failed: ${response.body}');
  }

  static Future<Map<String, dynamic>?> register({
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
      return jsonDecode(response.body);
    }
    throw Exception('Registration failed: ${response.body}');
  }

  static Future<Map<String, dynamic>?> getCurrentUser(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get user: ${response.body}');
  }

  static Future<Map<String, dynamic>?> getTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/patient/appointments/$appointmentId/teleconsultation',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get teleconsultation: ${response.body}');
  }

  static Future<Map<String, dynamic>?> getClinicalNote(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/patient/appointments/$appointmentId/clinical-note'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get clinical note: ${response.body}');
  }

  static Future<Map<String, dynamic>?> getPrescription(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse('$baseUrl/patient/appointments/$appointmentId/prescription'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get prescription: ${response.body}');
  }

  static Future<Map<String, dynamic>?> getCareInstructions(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/patient/appointments/$appointmentId/care-instructions',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get care instructions: ${response.body}');
  }

  static Future<Map<String, dynamic>?> getProfessionalTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/teleconsultation',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed: ${response.body}');
  }

  static Future<void> startTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/teleconsultation/start',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
  }

  static Future<void> endTeleconsultation(
    String token,
    String appointmentId,
  ) async {
    await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/teleconsultation/end',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
  }

  static Future<Map<String, dynamic>?> getProfessionalClinicalNote(
    String token,
    String appointmentId,
  ) async {
    final response = await http.get(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/clinical-note',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed: ${response.body}');
  }

  static Future<void> updateClinicalNote(
    String token,
    String appointmentId,
    Map<String, dynamic> data,
  ) async {
    await http.put(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/clinical-note',
      ),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(data),
    );
  }

  static Future<Map<String, dynamic>?> createPrescription(
    String token,
    String appointmentId,
    Map<String, dynamic> data,
  ) async {
    final response = await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/prescription',
      ),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(data),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed: ${response.body}');
  }

  static Future<void> issuePrescription(
    String token,
    String appointmentId,
    String prescriptionId,
  ) async {
    await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/prescription/$prescriptionId/issue',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
  }

  static Future<void> updateCareInstructions(
    String token,
    String appointmentId,
    Map<String, dynamic> data,
  ) async {
    await http.put(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/care-instructions',
      ),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(data),
    );
  }

  static Future<void> issueCareInstructions(
    String token,
    String appointmentId,
  ) async {
    await http.post(
      Uri.parse(
        '$baseUrl/professionals/me/appointments/$appointmentId/care-instructions/issue',
      ),
      headers: {'Authorization': 'Bearer $token'},
    );
  }
}
