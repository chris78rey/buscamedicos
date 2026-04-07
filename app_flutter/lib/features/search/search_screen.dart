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
                          final specialties = (item['specialties'] as List?)
                              ?.map((s) => (s as Map?)?['name'] ?? s)
                              .where((s) => s.toString().trim().isNotEmpty)
                              .join(', ');
                          return ListTile(
                            title: Text(item['public_display_name'] ?? 'Sin nombre'),
                            subtitle: Text(
                              [
                                item['public_title'] ?? '',
                                specialties ?? '',
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
    final specialties = (_profile?['specialties'] as List?)
        ?.map((s) => (s as Map?)?['name'] ?? s)
        .where((s) => s.toString().trim().isNotEmpty)
        .join(', ');

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
                  if (specialties != null && specialties.isNotEmpty)
                    Text('Especialidades: $specialties'),
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