import 'package:flutter/material.dart';

class ModerationDashboardScreen extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<ModerationDashboardScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Moderacion')),
      body: Center(child: Text('Moderacion - Dashboard')),
    );
  }
}

class ReportsListScreen extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<ReportsListScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Denuncias')),
      body: Center(child: Text('Lista de denuncias')),
    );
  }
}

class CasesListScreen extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<CasesListScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Casos de Moderacion')),
      body: Center(child: Text('Lista de casos')),
    );
  }
}

class SanctionsScreen extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<SanctionsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Sanciones')),
      body: Center(child: Text('Sanciones activas')),
    );
  }
}

class ReviewsModerationScreen extends StatefulWidget {
  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<ReviewsModerationScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Reseñas')),
      body: Center(child: Text('Moderacion de reseñas')),
    );
  }
}

class PatientReviewScreen extends StatefulWidget {
  final String appointmentId;
  final String professionalName;

  PatientReviewScreen({
    required this.appointmentId,
    required this.professionalName,
  });

  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<PatientReviewScreen> {
  int _rating = 0;
  final _commentController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Dejar Resena')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Profesional: ${widget.professionalName}',
              style: TextStyle(fontSize: 18),
            ),
            SizedBox(height: 16),
            Text('Calificacion general:', style: TextStyle(fontSize: 16)),
            Row(
              children: List.generate(5, (index) {
                return IconButton(
                  icon: Icon(index < _rating ? Icons.star : Icons.star_border),
                  onPressed: () => setState(() => _rating = index + 1),
                );
              }),
            ),
            SizedBox(height: 16),
            TextField(
              controller: _commentController,
              decoration: InputDecoration(
                labelText: 'Comentario (opcional)',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            SizedBox(height: 24),
            Center(
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: Text('Enviar Resena'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ProfessionalInternalReviewScreen extends StatefulWidget {
  final String appointmentId;
  final String patientName;

  ProfessionalInternalReviewScreen({
    required this.appointmentId,
    required this.patientName,
  });

  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<ProfessionalInternalReviewScreen> {
  int _rating = 0;
  final _commentController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Evaluacion Interna')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Paciente: ${widget.patientName}',
              style: TextStyle(fontSize: 18),
            ),
            SizedBox(height: 16),
            Text('Respeto:', style: TextStyle(fontSize: 16)),
            Row(
              children: List.generate(5, (index) {
                return IconButton(
                  icon: Icon(index < _rating ? Icons.star : Icons.star_border),
                  onPressed: () => setState(() => _rating = index + 1),
                );
              }),
            ),
            SizedBox(height: 16),
            TextField(
              controller: _commentController,
              decoration: InputDecoration(
                labelText: 'Notas internas (opcional)',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
            SizedBox(height: 24),
            Center(
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: Text('Guardar Evaluacion'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class CreateReportScreen extends StatefulWidget {
  final String subjectType;
  final String subjectId;

  CreateReportScreen({required this.subjectType, required this.subjectId});

  @override
  State<StatefulWidget> createState() => _State();
}

class _State extends State<CreateReportScreen> {
  String _category = 'abuse';
  String _severity = 'medium';
  final _descriptionController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Crear Denuncia')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Categoria:', style: TextStyle(fontSize: 16)),
            DropdownButton<String>(
              value: _category,
              items: [
                DropdownMenuItem(value: 'abuse', child: Text('Abuso')),
                DropdownMenuItem(value: 'fraud', child: Text('Fraude')),
                DropdownMenuItem(value: 'harassment', child: Text('Acoso')),
                DropdownMenuItem(value: 'no_show', child: Text('No asistio')),
                DropdownMenuItem(value: 'other', child: Text('Otro')),
              ],
              onChanged: (v) => setState(() => _category = v!),
            ),
            SizedBox(height: 16),
            Text('Severidad:', style: TextStyle(fontSize: 16)),
            DropdownButton<String>(
              value: _severity,
              items: [
                DropdownMenuItem(value: 'low', child: Text('Baja')),
                DropdownMenuItem(value: 'medium', child: Text('Media')),
                DropdownMenuItem(value: 'high', child: Text('Alta')),
                DropdownMenuItem(value: 'critical', child: Text('Critica')),
              ],
              onChanged: (v) => setState(() => _severity = v!),
            ),
            SizedBox(height: 16),
            TextField(
              controller: _descriptionController,
              decoration: InputDecoration(
                labelText: 'Descripcion',
                border: OutlineInputBorder(),
              ),
              maxLines: 5,
            ),
            SizedBox(height: 24),
            Center(
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: Text('Enviar Denuncia'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
