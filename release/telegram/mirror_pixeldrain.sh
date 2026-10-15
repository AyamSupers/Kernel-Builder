#!/usr/bin/env bash

# ======================================================
# 🪞 TELEGRAM — PixelDrain Mirror (RedPanda)
# Upload zip staged ke PixelDrain, export DOWNLOAD_URL.
#
# Prioritas tombol Download:
#   1. DOWNLOAD_URL manual (input workflow download_url)
#   2. Auto-mirror PixelDrain (butuh PIXELDRAIN_API_KEY)
#   3. Fallback halaman GitHub Releases (di rich_message.py)
#
# Input via environment:
#   STAGE_DIR          — dir berisi *.zip (default /tmp/post-stage)
#   DOWNLOAD_URL       — kalau sudah di-set (manual), skip upload
#   PIXELDRAIN_API_KEY — API key dari https://pixeldrain.com/user/api_keys
#                        (simpan sebagai repo secret)
#   PIXELDRAIN_API     — override base API (default https://pixeldrain.com/api)
#
# Output:
#   - DOWNLOAD_URL diekspor ke $GITHUB_ENV (kalau tersedia)
#   - URL dicetak ke stdout (baris terakhir)
# ======================================================

set -eo pipefail

STAGE_DIR="${STAGE_DIR:-/tmp/post-stage}"
PIXELDRAIN_API="${PIXELDRAIN_API:-https://pixeldrain.com/api}"

# 1. URL manual menang — tidak perlu upload.
if [ -n "${DOWNLOAD_URL:-}" ]; then
    echo "[LOG] mirror: DOWNLOAD_URL manual dipakai, skip PixelDrain ✅" >&2
    [ -n "${GITHUB_ENV:-}" ] && echo "DOWNLOAD_URL=${DOWNLOAD_URL}" >> "$GITHUB_ENV"
    echo "$DOWNLOAD_URL"
    exit 0
fi

# 2. Tanpa API key -> skip, biar fallback ke Releases.
if [ -z "${PIXELDRAIN_API_KEY:-}" ]; then
    echo "[WARN] mirror: PIXELDRAIN_API_KEY tidak di-set — tombol Download fallback ke GitHub Releases" >&2
    exit 0
fi

command -v curl >/dev/null 2>&1 || { echo "[ERROR] mirror: curl not found" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "[ERROR] mirror: jq not found" >&2; exit 1; }

mapfile -t zips < <(find "$STAGE_DIR" -maxdepth 2 -name '*.zip' | sort)
if [ "${#zips[@]}" -eq 0 ]; then
    echo "[WARN] mirror: tidak ada zip di ${STAGE_DIR} — skip" >&2
    exit 0
fi

upload_one() {
    local file="$1" name resp file_id
    name="$(basename "$file")"
    resp="$(curl -s --max-time 600 -u ":${PIXELDRAIN_API_KEY}" \
        -T "$file" "${PIXELDRAIN_API}/file/${name}")"
    file_id="$(jq -r '.id // empty' <<< "$resp")"
    if [ -z "$file_id" ]; then
        echo "[ERROR] mirror: upload gagal untuk ${name}: ${resp}" >&2
        return 1
    fi
    echo "$file_id"
}

ids=()
for z in "${zips[@]}"; do
    echo "[LOG] mirror: uploading $(basename "$z")..." >&2
    ids+=("$(upload_one "$z")") || exit 1
done

if [ "${#ids[@]}" -eq 1 ]; then
    DOWNLOAD_URL="https://pixeldrain.com/u/${ids[0]}"
else
    # Multi-file -> gabung jadi satu list biar 1 tombol cukup.
    files_json="$(printf '%s\n' "${ids[@]}" | jq -R . | jq -s -c 'map({id: .})')"
    payload="$(jq -n --argjson files "$files_json" \
        --arg title "RedPanda GKI Kernel" '{title: $title, files: $files}')"
    resp="$(curl -s --max-time 60 -u ":${PIXELDRAIN_API_KEY}" \
        -X POST -H 'Content-Type: application/json' \
        -d "$payload" "${PIXELDRAIN_API}/list")"
    list_id="$(jq -r '.id // empty' <<< "$resp")"
    if [ -n "$list_id" ]; then
        DOWNLOAD_URL="https://pixeldrain.com/l/${list_id}"
    else
        echo "[WARN] mirror: buat list gagal (${resp}) — pakai file pertama" >&2
        DOWNLOAD_URL="https://pixeldrain.com/u/${ids[0]}"
    fi
fi

echo "[LOG] mirror: DOWNLOAD_URL=${DOWNLOAD_URL} ✅" >&2
[ -n "${GITHUB_ENV:-}" ] && echo "DOWNLOAD_URL=${DOWNLOAD_URL}" >> "$GITHUB_ENV"
echo "$DOWNLOAD_URL"
