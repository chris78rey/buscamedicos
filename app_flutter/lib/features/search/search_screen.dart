import 'package:flutter/material.dart';
import 'services/api_service.dart';

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
  String? _selectedSpecialty;

  Future<void> _search() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.searchProfessionals(
        widget.token,
        city: _selectedCity,
        specialty: _selectedSpecialty,
      );
      if (mounted)
        setState(() {
          _results = data ?? [];
          _loading = false;
        });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
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
      appBar: AppBar(title: const Text('Buscar Profesionales')),
      body: Column(
        children: [
          DropdownButton<String>(
            hint: const Text('Ciudad'),
            value: _selectedCity,
            onChanged: (v) => setState(() => _selectedCity = v),
            items: const [
              DropdownMenuItem(value: 'Quito', child: Text('Quito')),
              DropdownMenuItem(value: 'Guayaquil', child: Text('Guayaquil')),
            ],
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: _results.length,
                    itemBuilder: (_, i) => ListTile(
                      title: Text(_results[i]['public_display_name'] ?? ''),
                      subtitle: Text(_results[i]['public_title'] ?? ''),
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ProfessionalDetailScreen(
                            token: widget.token,
                            professionalId: _results[i]['professional_id'],
                          ),
                        ),
                      ),
                    ),
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
  const ProfessionalDetailScreen({
    super.key,
    required this.token,
    required this.professionalId,
  });

  @override
  State<ProfessionalDetailScreen> createState() =>
      _ProfessionalDetailScreenState();
}

class _ProfessionalDetailScreenState extends State<ProfessionalDetailScreen> {
  Map<String, dynamic>? _profile;
  List<dynamic>? _slots;
  bool _loading = true;

  Future<void> _loadProfile() async {
    try {
      final profile = await ApiService.getPublicProfessional(
        widget.token,
        widget.professionalId,
      );
      final slots = await ApiService.getSlots(
        widget.token,
        widget.professionalId,
        '2024-06-10',
        'in_person_consultorio',
      );
      if (mounted)
        setState(() {
          _profile = profile;
          _slots = slots;
          _loading = false;
        });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _bookSlot(DateTime start) async {
    try {
      await ApiService.createAppointment(
        widget.token,
        professionalId: widget.professionalId,
        modalityCode: 'in_person_consultorio',
        scheduledStart: start,
      );
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Cita reservada con éxito')),
        );
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_profile?['public_display_name'] ?? 'Perfil')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _profile?['public_title'] ?? '',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(_profile?['public_bio'] ?? ''),
                  const SizedBox(height: 16),
                  Text('Ciudad: ${_profile?['city'] ?? ''}'),
                  Text(
                    'Precio: \$${_profile?['consultation_price'] ?? 'No disponible'}',
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Horarios disponibles:',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  if (_slots != null) ...[
                    for (var slot in _slots!)
                      if (slot['is_available'] == true)
                        ListTile(
                          title: Text(slot['start']),
                          trailing: ElevatedButton(
                            onPressed: () =>
                                _bookSlot(DateTime.parse(slot['start'])),
                            child: const Text('Reservar'),
                          ),
                        ),
                  ],
                ],
              ),
            ),
    );
  }
}

class MyAppointmentsScreen extends StatelessWidget {
  final String token;
  const MyAppointmentsScreen({super.key, required this.token});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mis Citas')),
      body: FutureBuilder(
        future: ApiService.getMyAppointments(token),
        builder: (_, snapshot) {
          if (!snapshot.hasData)
            return const Center(child: CircularProgressIndicator());
          final appointments = snapshot.data as List;
          return ListView.builder(
            itemCount: appointments.length,
            itemBuilder: (_, i) => ListTile(
              title: Text('Cita: ${appointments[i]['public_code']}'),
              subtitle: Text('Estado: ${appointments[i]['status']}'),
            ),
          );
        },
      ),
    );
  }
}
