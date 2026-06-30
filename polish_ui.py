import os

def update_login():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\login_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("NEO-PANC", "NeoPanc")
    content = content.replace("assets/images/6.jpg", "assets/images/6.jpeg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Login screen updated")

def update_splash():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\splash_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("NEO-PANC", "NeoPanc")
    content = content.replace("assets/images/6.jpg", "assets/images/6.jpeg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Splash screen updated")

def update_about():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\about_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("NEO-PANC TEAM", "NeoPanc Team")
    content = content.replace("assets/images/6.jpg", "assets/images/6.jpeg")
    # Add logo to the About screen AppBar
    content = content.replace(
        "title: Text('About NeoPanc', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5, color: theme.colorScheme.onSurface)),",
        """title: Row(
          children: [
            ClipOval(
              child: Image.asset(
                'assets/images/6.jpeg',
                width: 32,
                height: 32,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            Text('About NeoPanc', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5, color: theme.colorScheme.onSurface)),
          ],
        ),"""
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("About screen updated")

def update_dashboard():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\dashboard_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Update Premium Hero Header with Logo next to the greeting
    content = content.replace(
        "                          Text(\n                            _getGreeting(), \n                            style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.6), fontSize: 16, fontWeight: FontWeight.w600),\n                          ),",
        """                          Row(
                            children: [
                              ClipOval(
                                child: Image.asset(
                                  'assets/images/6.jpeg',
                                  width: 24,
                                  height: 24,
                                  fit: BoxFit.cover,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                _getGreeting(), 
                                style: TextStyle(color: theme.colorScheme.onSurface.withOpacity(0.6), fontSize: 16, fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),"""
    )

    # 2. Add AI Confidence check below risk score if available
    content = content.replace(
        """                                  Text(
                                    _latestPrediction != null ? '${_latestPrediction!['pcri_score']}%' : '--',
                                    style: TextStyle(fontWeight: FontWeight.w900, fontSize: 32, color: theme.primaryColor),
                                  ),""",
        """                                  Text(
                                    _latestPrediction != null ? '${_latestPrediction!['pcri_score']}%' : '--',
                                    style: TextStyle(fontWeight: FontWeight.w900, fontSize: 32, color: theme.primaryColor),
                                  ),
                                  if (_latestPrediction != null && _latestPrediction!['ai_confidence'] != null)
                                    Text('Confidence: ${_latestPrediction!['ai_confidence']}%', style: const TextStyle(color: Colors.greenAccent, fontSize: 12, fontWeight: FontWeight.bold)),"""
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Dashboard screen updated")

def update_sensors():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\sensor_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add logo to the IoT Dashboard AppBar
    content = content.replace(
        "title: const Text('IoT Dashboard'),",
        """title: Row(
          children: [
            ClipOval(
              child: Image.asset(
                'assets/images/6.jpeg',
                width: 32,
                height: 32,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            const Text('IoT Dashboard'),
          ],
        ),"""
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Sensors screen updated")

def update_prediction():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\prediction_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add logo to the AI Diagnostics AppBar
    content = content.replace(
        "title: const Text('AI Diagnostics'),",
        """title: Row(
          children: [
            ClipOval(
              child: Image.asset(
                'assets/images/6.jpeg',
                width: 32,
                height: 32,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            const Text('AI Diagnostics'),
          ],
        ),"""
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Prediction screen updated")

def update_history():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\history_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add logo to the Timeline History AppBar
    content = content.replace(
        "title: const Text('Timeline History'),",
        """title: Row(
          children: [
            ClipOval(
              child: Image.asset(
                'assets/images/6.jpeg',
                width: 32,
                height: 32,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            const Text('Timeline History'),
          ],
        ),"""
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("History screen updated")

def update_profile():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\profile_screen.dart"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add logo to the User Profile AppBar
    content = content.replace(
        "title: const Text('User Profile', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5)),",
        """title: Row(
          children: [
            ClipOval(
              child: Image.asset(
                'assets/images/6.jpeg',
                width: 32,
                height: 32,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 10),
            const Text('User Profile', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5)),
          ],
        ),"""
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Profile screen updated")

def update_all_jpg_to_jpeg():
    files = [
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\dashboard_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\sensor_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\prediction_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\history_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\profile_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\about_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\login_screen.dart",
        r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\splash_screen.dart",
    ]
    for path in files:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("assets/images/6.jpg", "assets/images/6.jpeg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {os.path.basename(path)} to 6.jpeg")

if __name__ == "__main__":
    update_login()
    update_splash()
    update_about()
    update_dashboard()
    update_sensors()
    update_prediction()
    update_history()
    update_profile()
    update_all_jpg_to_jpeg()
    print("UI Polish complete")
