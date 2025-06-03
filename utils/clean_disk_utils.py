import os
import shutil

def clean_disk():
    paths_to_clean = [
        "/tmp",
        "/var/tmp",
        os.path.expanduser("~/.cache"),
        os.path.expanduser("~/Downloads"),
    ]

    size_freed = 0

    for path in paths_to_clean:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        size_freed += os.path.getsize(file_path)
                        os.remove(file_path)
                    except Exception:
                        continue
                for dir in dirs:
                    try:
                        shutil.rmtree(os.path.join(root, dir))
                    except Exception:
                        continue

    freed_space = round(size_freed / (1024 * 1024), 2)
    return f"🧹 {freed_space} MB disk alanı temizlendi."
