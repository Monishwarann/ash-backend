import os

dart_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flutter_app', 'lib', 'services', 'api_service.dart')
with open(dart_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add firebase_auth import
if "import 'package:firebase_auth/firebase_auth.dart';" not in content:
    content = content.replace("import '../models/patient.dart';", "import '../models/patient.dart';\nimport 'package:firebase_auth/firebase_auth.dart';")

# Add token helper
token_helper = """  Future<Map<String, String>> _getHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      final token = await user.getIdToken();
      return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };
    }
    return {'Content-Type': 'application/json'};
  }"""
content = content.replace("  ApiService({required this.baseUrl});", "  ApiService({required this.baseUrl});\n\n" + token_helper)

# Update int userId to String userId everywhere
content = content.replace("int userId", "String userId")

# Update POST requests to use headers
content = content.replace("headers: {'Content-Type': 'application/json'}", "headers: await _getHeaders()")

# Update GET requests to include headers
content = content.replace("http.get(Uri.parse('$baseUrl/api/telemetry/latest/$userId'))", "http.get(Uri.parse('$baseUrl/api/telemetry/latest/$userId'), headers: await _getHeaders())")
content = content.replace("http.get(Uri.parse('$baseUrl/api/history/$userId'))", "http.get(Uri.parse('$baseUrl/api/history/$userId'), headers: await _getHeaders())")

# Fix syntax error on line 12
content = content.replace("async Future<Map<String, dynamic>> login", "Future<Map<String, dynamic>> login")

with open(dart_path, 'w', encoding='utf-8') as f:
    f.write(content)
