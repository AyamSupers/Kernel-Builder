#!/usr/bin/env bash

# ======================================================
# 📨 TELEGRAM — Post Configuration (RedPanda port)
# Adapted from LuminaireProtocol/release/telegram/config.sh
# ======================================================
# Cara pakai:
#   - Set secrets di GitHub: BOT_TOKEN (atau TELEGRAM_BOT_TOKEN),
#     CHAT_ID (atau TELEGRAM_CHAT_ID), MESSAGE_THREAD_ID (opsional),
#     CHANNEL_ID (atau TELEGRAM_CHANNEL_ID, untuk Release),
#     TELEGRAM_API_ID / TELEGRAM_API_HASH (untuk Local Bot API).
#   - Edit nilai default di bawah sesuai grup/channel kamu.

TELEGRAM_API_BASE="${TELEGRAM_API_BASE:-https://api.telegram.org}"
TELEGRAM_API_TIMEOUT="${TELEGRAM_API_TIMEOUT:-60}"
TELEGRAM_UPLOAD_TIMEOUT="${TELEGRAM_UPLOAD_TIMEOUT:-900}"
TELEGRAM_MAX_RETRIES="${TELEGRAM_MAX_RETRIES:-3}"

# Kompatibilitas nama secret lama (Kernel-Builder) -> nama baru (Luminaire)
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-${BOT_TOKEN:-}}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-${CHAT_ID:-}}"
# Tanpa CHANNEL_ID: mode Release ikut terkirim ke CHAT_ID (grup).
TELEGRAM_CHANNEL_ID="${TELEGRAM_CHANNEL_ID:-${CHANNEL_ID:-${TELEGRAM_CHAT_ID:-}}}"

# Grup diskusi (tanpa @). Dipakai untuk tombol "RedPanda Lab" di postingan.
TELEGRAM_GROUP="${TELEGRAM_GROUP:-ArtecxyzArchive}"

# Thread topik grup untuk mode Build. Kosongkan = kirim ke General.
# Bisa juga diisi via secrets MESSAGE_THREAD_ID.
TELEGRAM_THREAD_ID_BUILD="${TELEGRAM_THREAD_ID_BUILD:-${MESSAGE_THREAD_ID:-}}"

# Thread untuk notifikasi push (event push ke branch). Kosongkan = General.
TELEGRAM_THREAD_ID_EVENT="${TELEGRAM_THREAD_ID_EVENT:-}"
