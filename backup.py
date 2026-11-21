"""
Skrip Backup & Restore Database SQLite
Penggunaan:
    python backup.py backup            # Membuat file backup dengan stempel waktu
    python backup.py restore <file>    # Memulihkan database dari file backup
"""
import sys
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, "todo.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")


def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def backup_database():
    if not os.path.exists(DB_FILE):
        print(f"[!] File database {DB_FILE} belum dibuat. Jalankan aplikasi terlebih dahulu.")
        return False

    ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"todo_backup_{timestamp}.db"
    dest_path = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(DB_FILE, dest_path)
    size_kb = os.path.getsize(dest_path) / 1024
    print(f"[+] Backup berhasil dibuat: {dest_path} ({size_kb:.1f} KB)")
    return True


def restore_database(backup_filepath):
    if not os.path.exists(backup_filepath):
        print(f"[!] File backup tidak ditemukan: {backup_filepath}")
        return False

    # Buat backup keselamatan dari database saat ini jika ada
    if os.path.exists(DB_FILE):
        safety_path = f"{DB_FILE}.before_restore"
        shutil.copy2(DB_FILE, safety_path)
        print(f"[*] Salinan keselamatan database disimpan di {safety_path}")

    shutil.copy2(backup_filepath, DB_FILE)
    print(f"[+] Database berhasil dipulihkan dari {backup_filepath}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "backup":
        backup_database()
    elif sys.argv[1] == "restore":
        if len(sys.argv) < 3:
            print("Penggunaan: python backup.py restore <path_to_backup_file>")
            sys.exit(1)
        restore_database(sys.argv[2])
    else:
        print("Perintah tidak dikenal. Gunakan: 'backup' atau 'restore <file>'")
