"""
Buat akun admin dashboard pertama kali. Dashboard tidak punya halaman
registrasi publik (sengaja, biar tidak sembarang orang bisa daftar akun),
jadi akun awal dibuat lewat script ini di server.

Cara pakai:
    python -m backend.scripts.create_admin
"""
import getpass

from backend.services.auth_service import register_admin


def main():
    print("=== Buat Akun Dashboard WA Tugas ===")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()
    confirm = getpass.getpass("Konfirmasi Password: ").strip()

    if not username or not password:
        print("❌ Username & password wajib diisi.")
        return

    if password != confirm:
        print("❌ Password & konfirmasi tidak sama.")
        return

    try:
        register_admin(username, password)
    except ValueError as e:
        print(f"❌ {e}")
        return

    print(f"✅ Akun '{username}' berhasil dibuat. Silakan login di dashboard.")


if __name__ == "__main__":
    main()
