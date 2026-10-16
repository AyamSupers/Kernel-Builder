# ======================================================
# 👤 TELEGRAM — Sender Akun Pribadi / Channel 2 (RedPanda)
# Via user session (Telethon/MTProto) — tampil atas nama akun sendiri.
# BUKAN Bot API: akun user tidak bisa kirim tombol inline/tabel,
# jadi format disederhanakan: foto + teks polos + file.
#
# Butuh secret: TG_API_ID, TG_API_HASH, TG_SESSION, CHANNEL_2.
# Tanpa secret -> skip aman (exit 0).
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
    api_id = os.environ.get("TG_API_ID", "").strip()
    api_hash = os.environ.get("TG_API_HASH", "").strip()
    session = os.environ.get("TG_SESSION", "").strip()
    target = os.environ.get("TG_CHANNEL_2", "").strip() or os.environ.get("CHANNEL_2", "").strip()
    if not (api_id and api_hash and session and target):
        print("[WARN] user-post: TG_API_ID/TG_API_HASH/TG_SESSION/CHANNEL_2 belum lengkap — skip", flush=True)
        return

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    stage_dir = os.environ.get("STAGE_DIR", "/tmp/post-stage")
    metas = pc.load_metas(stage_dir)
    if not metas:
        print("[WARN] user-post: no staged variants — skip", flush=True)
        return
    env = pc.shared_env(metas[0])
    download = rm.download_url(env)
    changelogs = rm.changelogs_url(env)

    client = TelegramClient(StringSession(session), int(api_id), api_hash)
    await client.start()
    try:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banner")
        banners = sorted({p for pat in BANNER_PATTERNS for p in glob.glob(os.path.join(base, pat))})
        if banners:
            await client.send_file(target, banners[0], caption=short_caption(env, download))
        await client.send_message(target, compose_text(env, download, changelogs), link_preview=False)
        if not download:
            for meta in metas:
                await client.send_file(target, meta["zip_path"], caption=meta["zip_name"])
        print(f"[info] user-post: terkirim ke {target} ✅", flush=True)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
