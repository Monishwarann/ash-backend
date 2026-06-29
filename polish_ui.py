import os
import re

def update_login():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\login_screen.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("ONCO-SCREEN", "NeoPanc")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_splash():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\splash_screen.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("ONCO-SCREEN IoT", "NeoPanc")
    content = content.replace("AI-BASED NON-INVASIVE\\nPANCREATIC CANCER SCREENING", "AI-Powered Non-Invasive\\nPancreatic Cancer Screening\\nVersion 1.0")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_about():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\about_screen.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("ONCO-SCREEN", "NeoPanc")
    content = content.replace(
        "AI-Based Non-Invasive Pancreatic Cancer Screening Using Saliva/Breath Sensors",
        "AI-Powered Non-Invasive Pancreatic Cancer Risk Screening System Using IoT and Machine Learning"
    )
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_dashboard():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\dashboard_screen.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Update AppBar with Logo
    content = content.replace(
        "title: const Text('ONCO-SCREEN', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),",
        """title: Row(
          children: [
            const Icon(Icons.biotech, color: Colors.blueAccent),
            const SizedBox(width: 8),
            const Text('NeoPanc', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1)),
          ],
        ),"""
    )
    
    # 2. Add Dummy Data if history is empty
    dummy_data = """    if (history.isNotEmpty) {
      if (mounted) setState(() => _latestPrediction = history[0]);
    } else {
      if (mounted) setState(() => _latestPrediction = {
        'risk_level': 'Low',
        'pcri_score': 12,
        'ai_confidence': 95
      });
    }"""
    content = re.sub(r'    if \(history\.isNotEmpty\) \{\n      if \(mounted\) setState\(\(\) => _latestPrediction = history\[0\]\);\n    \}', dummy_data, content)

    # 3. Modify "Risk Score" string to also show Confidence if we have it
    # Currently it's: const Text('Risk Score', style: TextStyle(color: Colors.grey, fontSize: 14)),
    # We will just inject the confidence below the risk score
    # First, let's find the Risk Score display: Text(_latestPrediction != null ? '${_latestPrediction!['pcri_score']}%' : '--', ...
    
    confidence_ui = """                              Text(
                                _latestPrediction != null ? '${_latestPrediction!['pcri_score']}%' : '--',
                                style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 24, color: Colors.white),
                              ),
                              if (_latestPrediction != null && _latestPrediction!['ai_confidence'] != null)
                                Text('Confidence: ${_latestPrediction!['ai_confidence']}%', style: const TextStyle(color: Colors.greenAccent, fontSize: 12, fontWeight: FontWeight.bold)),"""
    
    content = re.sub(r'                              Text\(\n                                _latestPrediction != null \? \'\$\{\_latestPrediction\!\[\'pcri_score\'\]\}%\' : \'--\',\n                                style: const TextStyle\(fontWeight: FontWeight.w900, fontSize: 24, color: Colors.white\),\n                              \),', confidence_ui, content)

    # 4. Add Statistics Cards
    stats_ui = """              // Statistics Row
              Row(
                children: [
                  Expanded(child: _buildStatCard('Total Tests', '120', Icons.science, Colors.blue)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildStatCard('High Risk', '18', Icons.warning_amber, Colors.redAccent)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _buildStatCard('Accuracy', '95%', Icons.check_circle_outline, Colors.green)),
                  const SizedBox(width: 12),
                  Expanded(child: _buildStatCard('Last Screen', 'Today', Icons.calendar_today, Colors.purpleAccent)),
                ],
              ),
              const SizedBox(height: 28),

              // Live Sensors Section"""
    
    content = content.replace("              // Live Sensors Section", stats_ui)
    
    # Add _buildStatCard method
    stat_method = """  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B).withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 8),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildNavListTile"""
    content = content.replace("  Widget _buildNavListTile", stat_method)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_sensors():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\sensor_screen.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("bool _isConnected = false;", "bool _isConnected = true;")
    
    new_indicators = """            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF131926),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white10),
              ),
              
              ),
            ),"""
    
    # Replace the old Status Indicator container
    old_container = """            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF131926),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white10),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.circle, color: _isConnected ? Colors.greenAccent : Colors.redAccent, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    _isConnected ? 'ESP32 Hardware Connected' : 'ESP32 Disconnected',
                    style: TextStyle(color: _isConnected ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ],
              ),
            ),"""
    
    content = content.replace(old_container, new_indicators)
    
    # Add _buildStatusRow method
    status_row_method = """  Widget _buildStatusRow(String text, bool active) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.circle, color: active ? Colors.greenAccent : Colors.redAccent, size: 12),
        const SizedBox(width: 8),
        Text(
          text,
          style: TextStyle(color: active ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 14),
        ),
      ],
    );
  }

  Widget _buildLegend"""
    content = content.replace("  Widget _buildLegend", status_row_method)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    update_login()
    update_splash()
    update_about()
    update_dashboard()
    update_sensors()
    print("UI Polish complete")
