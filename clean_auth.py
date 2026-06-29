import os
import re

def clean_login_screen():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\login_screen.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove the _demoLogin function
    content = re.sub(r'void _demoLogin\(\) async \{.*?\n  \}', '', content, flags=re.DOTALL)
    
    # Remove the Demo Login Button block
    demo_btn_pattern = r'// Demo Login Button for Examiners.*?const SizedBox\(height: 24\),'
    content = re.sub(demo_btn_pattern, 'const SizedBox(height: 24),', content, flags=re.DOTALL)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def clean_api_service():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\services\api_service.dart"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove login method
    content = re.sub(r'// Auth: Login.*?\}', '', content, flags=re.DOTALL)
    # Remove register method
    # Be careful not to remove too much. Let's do it simply:
    content = re.sub(r'// Auth: Register.*?\}', '', content, flags=re.DOTALL)
    
    # Actually, let's just do a string replacement for the known blocks.
    pass


if __name__ == "__main__":
    clean_login_screen()
    print("Cleaned login_screen.dart")
