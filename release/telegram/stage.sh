#!/usr/bin/env bash

# ======================================================
# 📨 TELEGRAM — Post Staging (RedPanda port)
# Adapted from LuminaireProtocol/release/telegram/stage.sh
# ======================================================
# Tidak butuh functions.sh. Semua input via environment.
#
# Wajib:
#   ZIP_PATH  — path zip hasil AnyKernel3
#   ZIP_NAME  — nama file zip (basename)
#
# Opsional (diisi dari workflow bila tersedia):
#   KSU_VARIANT (mis. "BakaSU"), KSUVER, KERNEL_FULL_VERSION / KERNEL_VER,
#   KERNEL_BRANCH, KERNEL_SOURCE_OWNER/REPO, COMPILER_STRING, LTO_MODE,
#   SUSFS_VERSION_TAG, CHANGELOG
#
# Output:
#   - copy zip ke post-stage/
#   - embed redpanda.json ke dalam zip

if [ "${DRY_RUN:-false}" = "true" ]; then
    echo "[LOG] Skipping post staging: Dry Run mode (pipeline test only)" >&2
    return 0 2>/dev/null || exit 0
fi
if [ ! -f "${ZIP_PATH:-}" ]; then
    echo "[WARN] Skipping post staging: ZIP_PATH not set or file missing (ZIP_PATH='${ZIP_PATH:-}')" >&2
    return 0 2>/dev/null || exit 0
fi

command -v jq >/dev/null 2>&1 || { echo "[ERROR] post staging: jq not found" >&2; return 1 2>/dev/null || exit 1; }
command -v zip >/dev/null 2>&1 || { echo "[ERROR] post staging: zip not found" >&2; return 1 2>/dev/null || exit 1; }

# Normalisasi variant key: "BakaSU" -> "BAKASU", "KernelSU-Next" -> "KSUNEXT".
# NOTE: '-' harus di ujung set tr, kalau di tengah (' -_') dibaca
# sebagai range 0x20-0x5F dan menghapus huruf/angka!
VARIANT_RAW="${KSU_VARIANT:-${KERNEL_VARIANT:-UNKNOWN}}"
VARIANT_KEY="$(echo "$VARIANT_RAW" | tr '[:lower:]' '[:upper:]' | tr -d ' _-')"
case "$VARIANT_KEY" in
    KERNELSUNEXT) VARIANT_KEY="KSUNEXT" ;;
    SUKISUULTRA) VARIANT_KEY="SUKISU" ;;
    BAKASU|KSUNEXT|KSU|SUKISU|VANILLA) ;;
    *) VARIANT_KEY="$(echo "$VARIANT_RAW" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9' '_')" ;;
esac

LINUX_VER="${KERNEL_FULL_VERSION:-${KERNEL_VER:-N/A}}"
KERNEL_VERSION="$(echo "$LINUX_VER" | cut -d. -f1,2)"

STAGE_DIR="${STAGE_DIR:-${GITHUB_WORKSPACE:-$PWD}/post-stage}"
mkdir -p "$STAGE_DIR"
cp "$ZIP_PATH" "${STAGE_DIR}/${ZIP_NAME}"

META_FILE="$(mktemp -d)/redpanda.json"

jq -n \
    --arg variant "$VARIANT_KEY" \
    --arg variant_label "$VARIANT_RAW" \
    --arg variant_version "${KSUVER:+v$KSUVER}" \
    --arg susfs_version "${SUSFS_VERSION_TAG:-}" \
    --arg susfs_enabled "${SUSFS_ENABLED:-1}" \
    --arg linux_ver "$LINUX_VER" \
    --arg kernel_version "$KERNEL_VERSION" \
    --arg kernel_branch "${KERNEL_BRANCH:-}" \
    --arg kernel_source_owner "${KERNEL_SOURCE_OWNER:-AyamSupers}" \
    --arg kernel_source_repo "${KERNEL_SOURCE_REPO:-kernel}" \
    --arg compiler_string "${COMPILER_STRING:-${CLANG_CHOICE:-Neutron} Clang}" \
    --arg lto_mode "${LTO_MODE:-THIN}" \
    --arg applied_patches "${APPLIED_PATCHES:-susfs}" \
    --arg patch_versions "${PATCH_VERSIONS:-}" \
    '$ARGS.named' > "$META_FILE" \
    || { echo "[ERROR] Post staging: meta file creation failed!" >&2; return 1 2>/dev/null || exit 1; }

zip -q -j "${STAGE_DIR}/${ZIP_NAME}" "$META_FILE" \
    || { echo "[ERROR] Post staging: embedding meta into zip failed!" >&2; return 1 2>/dev/null || exit 1; }
rm -rf "$(dirname "$META_FILE")"

echo "[LOG] Post stage ready: ${ZIP_NAME} (${VARIANT_KEY}) ✅" >&2

return 0 2>/dev/null || true
