# -*- coding: utf-8 -*-
# ══════════════════════════════════════════════════════════════
# server_schutz.py — Schutz vor unbefugten Server-Änderungen
# Paradise City Roleplay Discord Bot
#
# Überwacht: Kanal-/Kategorie-Erstellung, -Bearbeitung, -Löschung
#            Rollen-Erstellung, -Bearbeitung, -Löschung
#
# Erlaubt NUR: Server-Inhaber & Bot-Owner
# Bei unbefugter Aktion: sofort rückgängig + Mod-Log
# ══════════════════════════════════════════════════════════════

import asyncio
from config import *

# Bot-Owner ID wird beim Start gecacht
_bot_owner_id: int | None = None


async def _get_owner_id() -> int | None:
    global _bot_owner_id
    if _bot_owner_id is None:
        try:
            info = await bot.application_info()
            _bot_owner_id = info.owner.id
        except Exception:
            pass
    return _bot_owner_id


def _ist_berechtigt(user_id: int, guild: discord.Guild) -> bool:
    """Gibt True zurück wenn der User Server-Inhaber oder Bot-Owner ist."""
    if user_id == guild.owner_id:
        return True
    if _bot_owner_id and user_id == _bot_owner_id:
        return True
    return False


async def _audit_user(guild: discord.Guild, action: discord.AuditLogAction) -> discord.Member | None:
    """Liest den letzten Audit-Log-Eintrag für die gegebene Aktion."""
    try:
        async for entry in guild.audit_logs(limit=1, action=action):
            return entry.user
    except Exception:
        pass
    return None


async def _log_verstoss(
    guild: discord.Guild,
    user: discord.Member | None,
    aktion: str,
    ziel: str,
    rueckgaengig: bool,
):
    """Postet einen Warn-Embed im Mod-Log."""
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return

    status = "✅ Automatisch rückgängig gemacht" if rueckgaengig else "⚠️ Konnte nicht rückgängig gemacht werden"

    embed = discord.Embed(
        title="🚨 Unbefugte Server-Änderung erkannt",
        description=(
            f"**Aktion:** {aktion}\n"
            f"**Ziel:** {ziel}\n"
            f"**Ausgeführt von:** {user.mention if user else 'Unbekannt'}\n\n"
            f"**Status:** {status}\n\n"
            "Nur der Server-Inhaber und der Bot-Owner dürfen diese Aktion ausführen."
        ),
        color=0xFF0000,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay • Server-Schutz")
    await log_ch.send(embed=embed)


# ══════════════════════════════════════════════════════════════
# Kanal / Kategorie — ERSTELLT
# ══════════════════════════════════════════════════════════════

@bot.listen("on_guild_channel_create")
async def schutz_kanal_erstellt(channel: discord.abc.GuildChannel):
    await asyncio.sleep(1)  # Audit-Log braucht kurz
    guild = channel.guild
    await _get_owner_id()

    user = await _audit_user(guild, discord.AuditLogAction.channel_create)
    if user and user.bot:
        return  # Bot-Aktionen ignorieren
    if user and _ist_berechtigt(user.id, guild):
        return

    typ  = "Kategorie" if isinstance(channel, discord.CategoryChannel) else "Kanal"
    name = channel.name
    ok   = False
    try:
        await channel.delete(reason="Server-Schutz: unbefugte Erstellung")
        ok = True
    except discord.Forbidden:
        pass

    await _log_verstoss(guild, user, f"{typ} erstellt", f"**#{name}**", ok)


# ══════════════════════════════════════════════════════════════
# Kanal / Kategorie — GELÖSCHT
# ══════════════════════════════════════════════════════════════

@bot.listen("on_guild_channel_delete")
async def schutz_kanal_geloescht(channel: discord.abc.GuildChannel):
    await asyncio.sleep(1)
    guild = channel.guild
    await _get_owner_id()

    user = await _audit_user(guild, discord.AuditLogAction.channel_delete)
    if user and user.bot:
        return
    if user and _ist_berechtigt(user.id, guild):
        return

    typ = "Kategorie" if isinstance(channel, discord.CategoryChannel) else "Kanal"
    await _log_verstoss(
        guild, user,
        f"{typ} gelöscht",
        f"**#{channel.name}**",
        False,  # Löschen kann nicht rückgängig gemacht werden
    )


# ══════════════════════════════════════════════════════════════
# Kanal / Kategorie — BEARBEITET
# ══════════════════════════════════════════════════════════════

@bot.listen("on_guild_channel_update")
async def schutz_kanal_bearbeitet(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
    await asyncio.sleep(1)
    guild = after.guild
    await _get_owner_id()

    user = await _audit_user(guild, discord.AuditLogAction.channel_update)
    if user and user.bot:
        return
    if user and _ist_berechtigt(user.id, guild):
        return

    typ = "Kategorie" if isinstance(after, discord.CategoryChannel) else "Kanal"
    await _log_verstoss(
        guild, user,
        f"{typ} bearbeitet",
        f"**#{after.name}**",
        False,
    )


# ══════════════════════════════════════════════════════════════
# Rolle — ERSTELLT
# ══════════════════════════════════════════════════════════════

@bot.listen("on_guild_role_create")
async def schutz_rolle_erstellt(role: discord.Role):
    await asyncio.sleep(1)
    guild = role.guild
    await _get_owner_id()

    user = await _audit_user(guild, discord.AuditLogAction.role_create)
    if user and user.bot:
        return
    if user and _ist_berechtigt(user.id, guild):
        return

    name = role.name
    ok   = False
    try:
        await role.delete(reason="Server-Schutz: unbefugte Rollen-Erstellung")
        ok = True
    except discord.Forbidden:
        pass

    await _log_verstoss(guild, user, "Rolle erstellt", f"**@{name}**", ok)


# ══════════════════════════════════════════════════════════════
# Rolle — GELÖSCHT
# ══════════════════════════════════════════════════════════════

@bot.listen("on_guild_role_delete")
async def schutz_rolle_geloescht(role: discord.Role):
    await asyncio.sleep(1)
    guild = role.guild
    await _get_owner_id()

    user = await _audit_user(guild, discord.AuditLogAction.role_delete)
    if user and user.bot:
        return
    if user and _ist_berechtigt(user.id, guild):
        return

    await _log_verstoss(guild, user, "Rolle gelöscht", f"**@{role.name}**", False)


# ══════════════════════════════════════════════════════════════
# Rolle — BEARBEITET
# ══════════════════════════════════════════════════════════════

@bot.listen("on_guild_role_update")
async def schutz_rolle_bearbeitet(before: discord.Role, after: discord.Role):
    await asyncio.sleep(1)
    guild = after.guild
    await _get_owner_id()

    user = await _audit_user(guild, discord.AuditLogAction.role_update)
    if user and user.bot:
        return
    if user and _ist_berechtigt(user.id, guild):
        return

    await _log_verstoss(guild, user, "Rolle bearbeitet", f"**@{after.name}**", False)
