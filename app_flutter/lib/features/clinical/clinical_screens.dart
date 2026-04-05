import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class PatientTeleconsultDetailScreen extends StatefulWidget {
  final String token;
  final String appointmentId;
  const PatientTeleconsultDetailScreen({
    super.key,
    required this.token,
    required this.appointmentId,
  });
  @override
  State<PatientTeleconsultDetailScreen> createState() =>
      _PatientTeleconsultDetailScreenState();
}

class _PatientTeleconsultDetailScreenState
    extends State<PatientTeleconsultDetailScreen> {
  Map<String, dynamic>? _teleconsult;
  Map<String, dynamic>? _clinicalNote;
  Map<String, dynamic>? _prescription;
  Map<String, dynamic>? _careInstructions;
  bool _loading = true;

  Future<void> _loadAll() async {
    try {
      final teleconsult = await ApiService.getTeleconsultation(
        widget.token,
        widget.appointmentId,
      );
      final note = await ApiService.getClinicalNote(
        widget.token,
        widget.appointmentId,
      );
      final rx = await ApiService.getPrescription(
        widget.token,
        widget.appointmentId,
      );
      final care = await ApiService.getCareInstructions(
        widget.token,
        widget.appointmentId,
      );
      if (mounted)
        setState(() {
          _teleconsult = teleconsult;
          _clinicalNote = note;
          _prescription = rx;
          _careInstructions = care;
          _loading = false;
        });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detalle de Teleconsulta')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_teleconsult != null) ...[
                    const Text(
                      'Sesión de Teleconsulta',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('Estado: ${_teleconsult!['status']}'),
                    if (_teleconsult!['session_url'] != null)
                      Text('Enlace: ${_teleconsult!['session_url']}'),
                    const SizedBox(height: 16),
                  ],
                  if (_clinicalNote != null &&
                      _clinicalNote!['visible_to_patient'] == true) ...[
                    const Text(
                      'Nota Clínica',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Motivo: ${_clinicalNote!['reason_for_consultation'] ?? ''}',
                    ),
                    Text(
                      'Resumen Subjetivo: ${_clinicalNote!['subjective_summary'] ?? ''}',
                    ),
                    Text(
                      'Objetivo: ${_clinicalNote!['objective_summary'] ?? ''}',
                    ),
                    Text('Evaluación: ${_clinicalNote!['assessment'] ?? ''}'),
                    Text('Plan: ${_clinicalNote!['plan'] ?? ''}'),
                    const SizedBox(height: 16),
                  ],
                  if (_prescription != null &&
                      _prescription!['items'] != null) ...[
                    const Text(
                      'Receta',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('Estado: ${_prescription!['status']}'),
                    for (var item in _prescription!['items'])
                      ListTile(
                        title: Text(item['medication_name']),
                        subtitle: Text(
                          '${item['dosage']} - ${item['frequency']}',
                        ),
                      ),
                    const SizedBox(height: 16),
                  ],
                  if (_careInstructions != null &&
                      _careInstructions!['content'] != null) ...[
                    const Text(
                      'Indicaciones',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(_careInstructions!['content'] ?? ''),
                    if (_careInstructions!['follow_up_recommended'] == true)
                      const Text('Seguimiento recomendado'),
                  ],
                ],
              ),
            ),
    );
  }
}

class ProfessionalTeleconsultManageScreen extends StatefulWidget {
  final String token;
  final String appointmentId;
  const ProfessionalTeleconsultManageScreen({
    super.key,
    required this.token,
    required this.appointmentId,
  });
  @override
  State<ProfessionalTeleconsultManageScreen> createState() =>
      _ProfessionalTeleconsultManageScreenState();
}

class _ProfessionalTeleconsultManageScreenState
    extends State<ProfessionalTeleconsultManageScreen> {
  Map<String, dynamic>? _teleconsult;
  bool _loading = true;

  Future<void> _load() async {
    try {
      final data = await ApiService.getProfessionalTeleconsultation(
        widget.token,
        widget.appointmentId,
      );
      if (mounted)
        setState(() {
          _teleconsult = data;
          _loading = false;
        });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _start() async {
    await ApiService.startTeleconsultation(widget.token, widget.appointmentId);
    _load();
  }

  Future<void> _end() async {
    await ApiService.endTeleconsultation(widget.token, widget.appointmentId);
    _load();
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Gestionar Teleconsulta')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Estado: ${_teleconsult?['status'] ?? 'N/A'}'),
                  const SizedBox(height: 16),
                  if (_teleconsult?['status'] == 'ready') ...[
                    ElevatedButton(
                      onPressed: _start,
                      child: const Text('Iniciar Teleconsulta'),
                    ),
                  ],
                  if (_teleconsult?['status'] == 'in_progress') ...[
                    ElevatedButton(
                      onPressed: _end,
                      child: const Text('Finalizar Teleconsulta'),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}

class ClinicalNoteEditorScreen extends StatefulWidget {
  final String token;
  final String appointmentId;
  const ClinicalNoteEditorScreen({
    super.key,
    required this.token,
    required this.appointmentId,
  });
  @override
  State<ClinicalNoteEditorScreen> createState() =>
      _ClinicalNoteEditorScreenState();
}

class _ClinicalNoteEditorScreenState extends State<ClinicalNoteEditorScreen> {
  final _reasonController = TextEditingController();
  final _subjectiveController = TextEditingController();
  final _objectiveController = TextEditingController();
  final _assessmentController = TextEditingController();
  final _planController = TextEditingController();
  bool _visibleToPatient = false;
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ApiService.updateClinicalNote(widget.token, widget.appointmentId, {
        'reason_for_consultation': _reasonController.text,
        'subjective_summary': _subjectiveController.text,
        'objective_summary': _objectiveController.text,
        'assessment': _assessmentController.text,
        'plan': _planController.text,
        'visible_to_patient': _visibleToPatient,
      });
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Nota guardada')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nota Clínica')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _reasonController,
              decoration: const InputDecoration(
                labelText: 'Motivo de consulta',
              ),
              maxLines: 2,
            ),
            TextField(
              controller: _subjectiveController,
              decoration: const InputDecoration(labelText: 'Resumen subjetivo'),
              maxLines: 3,
            ),
            TextField(
              controller: _objectiveController,
              decoration: const InputDecoration(labelText: 'Resumen objetivo'),
              maxLines: 3,
            ),
            TextField(
              controller: _assessmentController,
              decoration: const InputDecoration(labelText: 'Evaluación'),
              maxLines: 2,
            ),
            TextField(
              controller: _planController,
              decoration: const InputDecoration(labelText: 'Plan'),
              maxLines: 2,
            ),
            SwitchListTile(
              title: const Text('Visible para el paciente'),
              value: _visibleToPatient,
              onChanged: (v) => setState(() => _visibleToPatient = v),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const CircularProgressIndicator()
                  : const Text('Guardar Nota'),
            ),
          ],
        ),
      ),
    );
  }
}

class PrescriptionEditorScreen extends StatefulWidget {
  final String token;
  final String appointmentId;
  const PrescriptionEditorScreen({
    super.key,
    required this.token,
    required this.appointmentId,
  });
  @override
  State<PrescriptionEditorScreen> createState() =>
      _PrescriptionEditorScreenState();
}

class _PrescriptionEditorScreenState extends State<PrescriptionEditorScreen> {
  final _notesController = TextEditingController();
  final List<Map<String, String>> _items = [];
  bool _saving = false;

  Future<void> _save() async {
    if (_items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Agregue al menos un medicamento')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await ApiService.createPrescription(widget.token, widget.appointmentId, {
        'general_notes': _notesController.text,
        'items': _items
            .map(
              (e) => {
                'medication_name': e['name']!,
                'dosage': e['dosage']!,
                'frequency': e['frequency']!,
                'duration': e['duration']!,
              },
            )
            .toList(),
      });
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Receta creada')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Receta')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _notesController,
              decoration: const InputDecoration(labelText: 'Notas generales'),
              maxLines: 2,
            ),
            const SizedBox(height: 16),
            ..._items.map(
              (item) => ListTile(
                title: Text(item['name'] ?? ''),
                subtitle: Text('${item['dosage']} - ${item['frequency']}'),
              ),
            ),
            ElevatedButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const CircularProgressIndicator()
                  : const Text('Crear Receta'),
            ),
          ],
        ),
      ),
    );
  }
}

class CareInstructionsScreen extends StatefulWidget {
  final String token;
  final String appointmentId;
  const CareInstructionsScreen({
    super.key,
    required this.token,
    required this.appointmentId,
  });
  @override
  State<CareInstructionsScreen> createState() => _CareInstructionsScreenState();
}

class _CareInstructionsScreenState extends State<CareInstructionsScreen> {
  final _contentController = TextEditingController();
  bool _followUp = false;
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ApiService.updateCareInstructions(
        widget.token,
        widget.appointmentId,
        {
          'content': _contentController.text,
          'follow_up_recommended': _followUp,
        },
      );
      await ApiService.issueCareInstructions(
        widget.token,
        widget.appointmentId,
      );
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Indicaciones guardadas')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Indicaciones')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _contentController,
              decoration: const InputDecoration(labelText: 'Contenido'),
              maxLines: 5,
            ),
            SwitchListTile(
              title: const Text('Seguimiento recomendado'),
              value: _followUp,
              onChanged: (v) => setState(() => _followUp = v),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const CircularProgressIndicator()
                  : const Text('Guardar e Issuing'),
            ),
          ],
        ),
      ),
    );
  }
}
