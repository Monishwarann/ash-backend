import os
import re

def update_firebase_service():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\services\firebase_service.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix fetchHistoryLogs collection name
    content = content.replace(".collection('predictions')", ".collection('screening_logs')")

    # 2. Add updateUserProfile method
    update_method = """  // Update User Profile
  Future<bool> updateUserProfile(String userId, Map<String, dynamic> data) async {
    try {
      await _db.collection('users').doc(userId).update(data);
      return true;
    } catch (e) {
      print("Error updating profile: $e");
      return false;
    }
  }

  // Fetch User Profile
  Future<Map<String, dynamic>?> fetchUserProfile(String userId) async {
    try {
      final doc = await _db.collection('users').doc(userId).get();
      return doc.data();
    } catch (e) {
      return null;
    }
  }
}"""
    # Replace the last closing brace with the new methods
    content = content.rsplit('}', 1)[0] + update_method
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_profile_screen():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\profile_screen.dart"
    # Complete rewrite of profile screen to add Stateful logic and editing
    new_content = """import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/firebase_service.dart';
import '../main.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final FirebaseService _firebaseService = FirebaseService();
  bool _isLoading = true;
  
  // Profile Data
  String _name = 'User';
  String _age = '45';
  String _gender = 'Male';
  String _bloodGroup = 'O+';
  String _phone = '+1 234 567 8900';

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final provider = Provider.of<UserStateProvider>(context, listen: false);
    if (provider.userId != null) {
      final data = await _firebaseService.fetchUserProfile(provider.userId!);
      if (data != null && mounted) {
        setState(() {
          _name = data['username'] ?? provider.username ?? 'User';
          _age = data['age']?.toString() ?? '45';
          _gender = data['gender'] ?? 'Male';
          _bloodGroup = data['bloodGroup'] ?? 'O+';
          _phone = data['phone'] ?? '+1 234 567 8900';
        });
      }
    }
    if (mounted) setState(() => _isLoading = false);
  }

  void _showEditDialog() {
    final nameCtrl = TextEditingController(text: _name);
    final ageCtrl = TextEditingController(text: _age);
    final genderCtrl = TextEditingController(text: _gender);
    final bloodCtrl = TextEditingController(text: _bloodGroup);
    final phoneCtrl = TextEditingController(text: _phone);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF131926),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) {
        return Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 24, right: 24, top: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Edit Profile', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),
              TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Name')),
              const SizedBox(height: 10),
              TextField(controller: ageCtrl, decoration: const InputDecoration(labelText: 'Age'), keyboardType: TextInputType.number),
              const SizedBox(height: 10),
              TextField(controller: genderCtrl, decoration: const InputDecoration(labelText: 'Gender')),
              const SizedBox(height: 10),
              TextField(controller: bloodCtrl, decoration: const InputDecoration(labelText: 'Blood Group')),
              const SizedBox(height: 10),
              TextField(controller: phoneCtrl, decoration: const InputDecoration(labelText: 'Phone')),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () async {
                    final provider = Provider.of<UserStateProvider>(context, listen: false);
                    if (provider.userId != null) {
                      await _firebaseService.updateUserProfile(provider.userId!, {
                        'username': nameCtrl.text,
                        'age': nameCtrl.text,
                        'gender': genderCtrl.text,
                        'bloodGroup': bloodCtrl.text,
                        'phone': phoneCtrl.text,
                      });
                      setState(() {
                        _name = nameCtrl.text;
                        _age = ageCtrl.text;
                        _gender = genderCtrl.text;
                        _bloodGroup = bloodCtrl.text;
                        _phone = phoneCtrl.text;
                      });
                      // Update provider name
                      provider.setUser(provider.userId!, _name, provider.email ?? '');
                    }
                    if (mounted) Navigator.pop(context);
                  },
                  child: const Text('Save Changes'),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<UserStateProvider>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('User Profile'),
        actions: [
          IconButton(icon: const Icon(Icons.edit, color: Colors.blueAccent), onPressed: _showEditDialog),
        ],
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                children: [
                  const CircleAvatar(
                    radius: 50,
                    backgroundColor: Color(0xFF3B82F6),
                    child: Icon(Icons.person, size: 50, color: Colors.white),
                  ),
                  const SizedBox(height: 16),
                  Text(_name, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                  Text(provider.email ?? '', style: const TextStyle(color: Colors.grey)),
                  const SizedBox(height: 32),
                  
                  _buildProfileItem(Icons.badge, 'Name', _name),
                  _buildProfileItem(Icons.cake, 'Age', _age),
                  _buildProfileItem(Icons.person_outline, 'Gender', _gender),
                  _buildProfileItem(Icons.bloodtype, 'Blood Group', _bloodGroup),
                  _buildProfileItem(Icons.phone, 'Phone', _phone),
                  
                  const SizedBox(height: 48),
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        await _firebaseService.logout();
                        if (context.mounted) {
                          provider.clearUser();
                          Navigator.pushReplacementNamed(context, '/login');
                        }
                      },
                      icon: const Icon(Icons.logout),
                      label: const Text('Logout', style: TextStyle(fontWeight: FontWeight.bold)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent.withOpacity(0.2),
                        foregroundColor: Colors.redAccent,
                        elevation: 0,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildProfileItem(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12.0),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: Colors.blueAccent),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}"""
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    update_firebase_service()
    update_profile_screen()
    print("Frontend logic applied successfully.")
