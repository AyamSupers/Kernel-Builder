# ======================================================
# 👤 TELEGRAM — Sender Akun Pribadi / Channel (RedPanda)
# Via user session (Telethon/MTProto) — tampil atas nama akun sendiri.
# BUKAN Bot API: akun user tidak bisa kirim tombol inline/tabel,
# jadi format disederhanakan: foto + teks polos + file.
#
# Dipakai workflow "Telegram Rich Notify" untuk target Channel
# (RedPanda Build) dan bisa kirim ke BEBERAPA channel sekaligus.
#
# Cara pakai:
#   python3 post_user.py          -> kirim post hasil staging (butuh STAGE_DIR)
#   python3 post_user.py text     -> kirim teks polos dari env MSG
#
# Butuh secret: TG_API_ID, TG_API_HASH, TG_SESSION, lalu daftar channel di
# TG_CHANNELS (dipisah koma). Nama lama TG_CHANNEL_2 / CHANNEL_2 masih
# didukung sebagai fallback. Tanpa secret -> skip aman (exit 0).
# Buat session string: python3 release/telegram/make_session.py (di lokal)
# ======================================================

from __future__ import annotations

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import caption
import post_card as pc
import rich_message as rm

BANNER_PATTERNS = ("*.png", "*.jpg", "*.jpeg")


def env_value(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def resolve_targets() -> list:
    """Daftar channel tujuan: TG_CHANNELS (pisah koma) > TG_CHANNEL_2/CHANNEL_2."""
    raw = env_value("TG_CHANNELS", "TG_CHANNEL_2", "CHANNEL_2")
    return [t.strip() for t in raw.split(",") if t.strip()]


def compose_text(env: dict, download: str, changelogs: str) -> str:
    lines = [
        "RedPanda GKI Kernel",
        "",
        f"Kernel: Linux {(env.get('LINUX_VER', '') or 'N/A').strip()}",
        f"Toolchain: {(env.get('COMPILER_STRING', '') or 'N/A').strip()}",
        f"Variant: {rm.variant_line(env)}",
        f"LTO: {caption.LTO_DISPLAY.get(env.get('LTO_MODE', '').strip(), env.get('LTO_MODE', '').strip() or 'N/A')}",
        "",
        "Credit:",
    ]
    lines += [f"\u2022 {c}" for c in rm.CREDITS]
    raw = env.get("CHANGELOG", "").strip()
    entries = [e.strip() for e in raw.split(";") if e.strip()]
    if entries:
        lines += ["", "Changelog:"]
        lines += [f"\u2022 {e}" for e in entries]
    lines += ["", f"Download: {download or '-'}"]
    if changelogs:
        lines.append(f"Changelogs: {changelogs}")
    lines += ["", f"Support: {rm.SUPPORT_URL}", f"Channel: {rm.CHANNEL_URL}"]
    return "\n".join(lines)


def short_caption(env: dict, download: str) -> str:
    text = f"RedPanda GKI Kernel\n{rm.variant_line(env)}\nDownload: {download or '-'}"
    return text[:1000]


async def main() -> None:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "stage").strip().lower()
    api_id = env_value("TG_API_ID")
    api_hash = env_value("TG_API_HASH")
    session = env_value("TG_SESSION")
    targets = resolve_targets()
    if not (api_id and api_hash and session and targets):
        print("[WARN] user-post: TG_API_ID/TG_API_HASH/TG_SESSION/TG_CHANNELS belum lengkap — skip", flush=True)
        return

    text_mode = mode == "text"
    if text_mode:
        message = env_value("MSG")
        if not message:
            print("[WARN] user-post: MSG kosong — skip", flush=True)
            return
    else:
        stage_dir = os.environ.get("STAGE_DIR", "/tmp/post-stage")
        metas = pc.load_metas(stage_dir)
        if not metas:
            print("[WARN] user-post: no staged variants — skip", flush=True)
            return
        env = pc.shared_env(metas[0])
        download = rm.download_url(env)
        changelogs = rm.changelogs_url(env)
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banner")
        banners = sorted({p for pat in BANNER_PATTERNS for p in glob.glob(os.path.join(base, pat))})

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    client = TelegramClient(StringSession(session), int(api_id), api_hash)
    await client.start()
    try:
        # Satu channel gagal tidak menghentikan channel lainnya.
        for target in targets:
            try:
                if text_mode:
                    await client.send_message(target, message, link_preview=False)
                    print(f"[info] user-post: notif terkirim ke {target} ✅", flush=True)
                    continue

                if banners:
                    await client.send_file(target, banners[0], caption=short_caption(env, download))
                await client.send_message(target, compose_text(env, download, changelogs), link_preview=False)
                if not download:
                    for meta in metas:
                        await client.send_file(target, meta["zip_path"], caption=meta["zip_name"])
                print(f"[info] user-post: terkirim ke {target} ✅", flush=True)
            except Exception as exc:  # noqa: BLE001 - lanjut ke channel berikutnya
                print(f"[WARN] user-post: gagal kirim ke {target}: {exc}", flush=True)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
