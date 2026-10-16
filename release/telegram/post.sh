#!/usr/bin/env bash

# ======================================================
# 📨 TELEGRAM — Post Sender, Build / Release (RedPanda port)
# Adapted from LuminaireProtocol/release/telegram/post.sh
# Memakai Bot API 10.1+ sendRichMessage via api.telegram.org
# (batas upload 50MB per file).
# ======================================================

set -eo pipefail

ROOT_DIR="${ROOT_DIR:-${GITHUB_WORKSPACE:?post: set ROOT_DIR or GITHUB_WORKSPACE}}"
TELEGRAM_DIR="${ROOT_DIR}/release/telegram"

source "${TELEGRAM_DIR}/config.sh"
source "${TELEGRAM_DIR}/common.sh"

STAGE_DIR="${STAGE_DIR:-/tmp/post-stage}"
PAYLOAD_FILE="/tmp/post_payload.json"
ATTACHMENTS_FILE="/tmp/post_attachments.txt"
RESPONSE_FILE="/tmp/post_response.json"

cleanup() {
    rm -f "$PAYLOAD_FILE" "$ATTACHMENTS_FILE" "$RESPONSE_FILE"
}

send_post() {
    local chat_id="$1" thread_id="$2" with_banner="$3" label="$4" pin="$5"
    local -a attachment_specs send_args
    local message_id

    POST_BANNER="$with_banner" \
    TELEGRAM_GROUP="${TELEGRAM_GROUP:-}" \
    CHANGELOG="${CHANGELOG:-}" \
    DOWNLOAD_URL="${DOWNLOAD_URL:-}" \
    GITHUB_SERVER_URL="${GITHUB_SERVER_URL:-https://github.com}" \
    GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}" \
    python3 "${TELEGRAM_DIR}/post_card.py" "$STAGE_DIR" "$PAYLOAD_FILE" "$ATTACHMENTS_FILE" \
        || error "Telegram: ${label} builder failed!"

    mapfile -t attachment_specs < "$ATTACHMENTS_FILE"

    send_args=(-F "chat_id=${chat_id}" -F "rich_message=<${PAYLOAD_FILE}")
    for spec in "${attachment_specs[@]}"; do
        send_args+=(-F "$spec")
    done
    [ -n "$thread_id" ] && send_args+=(-F "message_thread_id=${thread_id}")

    log "📨 Sending ${label} (${RUN_MODE_UPPER}, ${#attachment_specs[@]} attachment(s))..."
    TELEGRAM_API_TIMEOUT="$TELEGRAM_UPLOAD_TIMEOUT" \
    telegram_api_call "sendRichMessage" "$RESPONSE_FILE" "$label" "${send_args[@]}" \
        || error "${label} failed"

    message_id="$(jq -r '.result.message_id // empty' <<< "$TG_RESPONSE")"
    log "Sent ✅ ${label} (message_id=${message_id})"

    if [ "${pin}" = "1" ] && [ -n "${message_id}" ]; then
        log "📌 Pinning ${label} (message_id=${message_id})..."
        telegram_api_call "pinChatMessage" "$RESPONSE_FILE" "Pin ${label}" \
            -F "chat_id=${chat_id}" -F "message_id=${message_id}" -F "disable_notification=true" \
            || warn "Pin ${label} failed — pastikan bot admin dengan izin pin"
    fi
}

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    warn "Skipping post: TELEGRAM_BOT_TOKEN (atau BOT_TOKEN) not set"
    exit 0
fi
if [ ! -d "$STAGE_DIR" ] || [ -z "$(find "$STAGE_DIR" -name '*.zip' -print -quit)" ]; then
    warn "Skipping post: no staged variants in ${STAGE_DIR}"
    exit 0
fi

# RUN_MODE default BUILD agar kompatibel dengan workflow lama yang
# hanya punya input telegram_notify + github_release.
if [ -z "${RUN_MODE:-}" ]; then
    if [ "${GITHUB_RELEASE_FLAG:-${GITHUB_RELEASE:-false}}" = "true" ]; then
        RUN_MODE="Release"
    else
        RUN_MODE="Build"
    fi
fi

RUN_MODE_UPPER="${RUN_MODE^^}"
case "$RUN_MODE_UPPER" in
    BUILD|RELEASE) ;;
    *) error "Telegram: unknown RUN_MODE '${RUN_MODE:-}' — expected Build or Release" ;;
esac

trap cleanup EXIT

# Tujuan kirim: Auto (ikut RUN_MODE: Release->channel, Build->grup),
# atau paksa Group / Channel via input telegram_target.
TARGET_UPPER="${TELEGRAM_TARGET:-Auto}"
TARGET_UPPER="${TARGET_UPPER^^}"
case "$TARGET_UPPER" in
    AUTO|"")
        if [ "$RUN_MODE_UPPER" = "RELEASE" ]; then
            TARGET_UPPER="CHANNEL"
        else
            TARGET_UPPER="GROUP"
        fi
        ;;
    GROUP|CHANNEL) ;;
    *) error "Telegram: unknown TELEGRAM_TARGET '${TELEGRAM_TARGET:-}' — expected Auto, Group, or Channel" ;;
esac

if [ "$TARGET_UPPER" = "CHANNEL" ]; then
    [ -n "${TELEGRAM_CHANNEL_ID:-}" ] || error "TELEGRAM_CHANNEL_ID (atau CHANNEL_ID) not set — isi secret CHANNEL_ID untuk target Channel"
    send_post "$TELEGRAM_CHANNEL_ID" "" 1 "Channel post" 1
    exit 0
fi

# GROUP -> grup + thread (thread opsional, kosong = General)
[ -n "${TELEGRAM_CHAT_ID:-}" ] || error "TELEGRAM_CHAT_ID (atau CHAT_ID) not set"
send_post "$TELEGRAM_CHAT_ID" "${TELEGRAM_THREAD_ID_BUILD:-}" 1 "Group post" 0
