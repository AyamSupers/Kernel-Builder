import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

async def main():
    # Mengambil konfigurasi dari Environment Variable
    TOKEN = os.environ.get("BOT_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")
    THREAD_ID = os.environ.get("MESSAGE_THREAD_ID") # Bisa None jika tidak ada

    bot = Bot(token=TOKEN)

    keyboard = [
        [
            InlineKeyboardButton("📥 Download", url="https://example.com/download"),
            InlineKeyboardButton("📝 Changelogs", url="https://example.com/changelogs")
        ],
        [
            InlineKeyboardButton("❤️ Donate", url="https://example.com/donate"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/channel_anda")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Siapkan argumen dasar
    send_args = {
        "chat_id": CHAT_ID,
        "text": "Halo! Ini adalah pesan otomatis dari GitHub Actions.",
        "reply_markup": reply_markup
    }

    # Tambahkan message_thread_id HANYA JIKA variabelnya ada dan tidak kosong
    if THREAD_ID and THREAD_ID.strip() != "":
        send_args["message_thread_id"] = int(THREAD_ID)
        print(f"Mengirim ke Topik ID: {THREAD_ID}")
    else:
        print("Mengirim ke Chat Utama (tanpa Topik)")

    # Kirim pesan
    await bot.send_message(**send_args)
    print("Pesan berhasil dikirim!")

if __name__ == '__main__':
    asyncio.run(main())
