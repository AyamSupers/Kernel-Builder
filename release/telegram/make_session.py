"""Buat Telethon StringSession untuk postingan akun pribadi.

Jalankan di KOMPUTER/HP kamu (bukan di GitHub Actions):

    pip install telethon
    python3 make_session.py

Masukkan API ID + API HASH dari https://my.telegram.org
( API development tools ), lalu nomor HP + kode login + password 2FA
(kalau ada). Salin string SESSION yang tercetak ke GitHub secret
bernama TG_SESSION. JANGAN bagikan string ini ke siapa pun.
"""

from telethon.sessions import StringSession
from telethon.sync import TelegramClient


def main() -> None:
    api_id = int(input("API ID: ").strip())
    api_hash = input("API HASH: ").strip()
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("\n=== TG_SESSION (simpan sebagai GitHub secret) ===")
        print(client.session.save())


if __name__ == "__main__":
    main()
