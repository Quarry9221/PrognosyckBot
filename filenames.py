import os

# Папки, які не потрібно включати
EXCLUDED_DIRS = {".venv", "__pycache__", ".pytest_cache", ".git", ".sql", ".csv", ".txt", ".log", "reports", "exports", "backups", "logs", "scripts", "legacy"}

# Розширення файлів, які не потрібно включати
EXCLUDED_EXTENSIONS = {".db", ".txt", ".log"}

def list_files(base_path, indent=0):
    for item in sorted(os.listdir(base_path)):
        if item in EXCLUDED_DIRS:
            continue
        full_path = os.path.join(base_path, item)
        if os.path.isdir(full_path):
            print("    " * indent + f"[{item}/]")
            list_files(full_path, indent + 1)
        else:
            ext = os.path.splitext(item)[1]
            if ext in EXCLUDED_EXTENSIONS:
                continue
            print("    " * indent + f"{item} ({ext})")

# "." означає поточну директорію
project_path = "."
list_files(project_path)