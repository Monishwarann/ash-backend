import os

def patch_main():
    main_path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\main.dart"
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove the cardTheme block
    if "cardTheme: CardTheme(" in content:
        start_idx = content.find("cardTheme: CardTheme(")
        end_idx = content.find("),", start_idx)
        # Find the next closing parenthesis and comma for the cardTheme block
        # The block has nested parenthesis, so we need a stack or we can just regex/replace exactly.
        import re
        content = re.sub(r'cardTheme:\s*CardTheme\([\s\S]*?elevation:\s*8,\s*\),', '', content)

    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)


def patch_prediction():
    pred_path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\screens\prediction_screen.dart"
    with open(pred_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("provider.userId ?? 1", "provider.userId ?? '1'")

    with open(pred_path, "w", encoding="utf-8") as f:
        f.write(content)


def patch_api_service():
    api_path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\flutter_app\lib\services\api_service.dart"
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Add imports if not present
    if "import 'dart:io';" not in content:
        content = "import 'dart:io';\nimport 'package:path_provider/path_provider.dart';\nimport 'package:open_file/open_file.dart';\n" + content

    # Add downloadPdf method if not present
    if "downloadPdf" not in content:
        pdf_method = """
  // Download PDF
  Future<String?> downloadPdf(String logId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/generate-pdf/$logId'), headers: await _getHeaders());
      if (response.statusCode == 200) {
        final directory = await getApplicationDocumentsDirectory();
        final file = File('${directory.path}/report_$logId.pdf');
        await file.writeAsBytes(response.bodyBytes);
        await OpenFile.open(file.path);
        return file.path;
      }
    } catch (e) {
      print("Error downloading PDF: $e");
    }
    return null;
  }
}"""
        content = content.rsplit('}', 1)[0] + pdf_method

    with open(api_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_main()
    patch_prediction()
    patch_api_service()
    print("Patch successful!")
