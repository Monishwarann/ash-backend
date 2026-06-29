with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# The error was caused by the leftover prompt and API call logic which starts after line 65 and ends right before "Initial Database Setup" (line 144)
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "prompt = f\"\"\"" in line:
        start_idx = i - 1 # start from previous empty line or wherever
    if "# Initial Database Setup" in line:
        end_idx = i

if start_idx != -1 and end_idx != -1:
    del lines[start_idx:end_idx]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
