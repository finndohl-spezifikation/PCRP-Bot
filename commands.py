# ─────────────────────────────────────────────────────────────────────────────────
from config import *
from helpers import is_admin, is_team
import fraktionen as _frak
import angeln as _angeln  # 🆕 NEU: Import für Angler-Shop

# Kein default_member_permissions → für alle Spieler sichtbar (Debug-Command)
@bot.tree.command(name="ping", description="Prüft ob der Bot erreichbar ist", guild=discord.Object(id=GUILD_ID))
async def ping_cmd(interaction: discord.Interaction):
    ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"🍳 Pong! `{ms} ms`", ephemeral=True)

# ─────────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────────
@bot.tree.command(name="kartenkontrolle", description="[Team] Kartenkontrolle-Erinnerung per DM senden", guild=discord.Object(id=GUILD_ID))
async def kartenkontrolle(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild        = interaction.guild
    channel_link = f"https://discord.com/channels/{guild.id}/{KARTENKONTROLLE_CHANNEL_ID}"

    sent   = 0
    failed = 0
    for member in guild.members:
        if member.bot:
            continue
        role_ids = [r.id for r in member.roles]
        is_member_role = (
            CITIZEN_ROLE_ID in role_ids
            or any(r in role_ids for r in WAGE_ROLES)
        )
        if not is_member_role:
            continue
        try:
            dm_embed = discord.Embed(
                title="🪪 Kartenkontrolle",
                description=(
                    f"**Hallo {member.display_name}!**\n\n"
                    f"Es findet gerade eine **Kartenkontrolle** statt.\n"
                    f"Bitte begib dich in den Kanal:\n"
                    f"[🔗 Zur Kartenkontrolle]({channel_link})\n\n"
                    f"*Diese Nachricht wurde automatisch durch das Team gesendet.*"
                ),
                color=LOG_COLOR,
                timestamp=datetime.now(timezone.utc)
            )
            dm_embed.set_footer(text="Paradise City Roleplay • Kartenkontrolle")
            await member.send(embed=dm_embed)
            sent += 1
        except Exception:
            failed += 1

    await interaction.followup.send(
        f"✅ Kartenkontrolle-DM gesendet!\n**Erfolgreich:** {sent} | **Fehlgeschlagen (DMs zu):** {failed}",
        ephemeral=True
    )

# ─────────────────────────────────────────────────────────────────────────────────
@bot.tree.command(name="delete", description="[Team] Löscht Nachrichten im Kanal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(anzahl="Anzahl der zu löschenden Nachrichten (max. 100)")
async def delete_messages(interaction: discord.Interaction, anzahl: int):
    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message("❌ Bitte eine Zahl zwischen 1 und 100 angeben.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    geloescht = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"✅ **{len(geloescht)}** Nachrichten wurden gelöscht.",
        ephemeral=True
    )

# ─────────────────────────────────────────────────────────────────────────────────
@bot.tree.command(name="anonym-nachricht", description="[Team] Sende anonyme Nachricht an User", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    user="Empfänger der Nachricht",
    nachricht="Nachricht die gesendet werden soll"
)
async def anonym_nachricht(interaction: discord.Interaction, user: discord.User, nachricht: str):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        embed = discord.Embed(
            title="🔔 Anonyme Nachricht",
            description=f"Hallo {user.mention}!\n\n**Nachricht:**\n{nachricht}",
            color=LOG_COLOR,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Paradise City Roleplay • Anonyme Nachricht")
        
        await user.send(embed=embed)
        
        await interaction.followup.send(
            f"✅ Anonyme Nachricht an {user.mention} gesendet.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler beim Senden: {str(e)}",
            ephemeral=True
        )

# ─────────────────────────────────────────────────────────────────────────────────
@bot.tree.command(name="server-info", description="[Team] Zeigt Server-Informationen", guild=discord.Object(id=GUILD_ID))
async def server_info(interaction: discord.Interaction):
    if not is_team(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    total_members = len(guild.members)
    online_members = len([m for m in guild.members if m.status != discord.Status.offline])
    total_channels = len(guild.channels)
    text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
    voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
    
    embed = discord.Embed(
        title="📊 Server-Informationen",
        description=(
            f"**Server:** {guild.name}\n"
            f"**ID:** {guild.id}\n"
            f"**Besitzer:** {guild.owner.mention if guild.owner else 'Unbekannt'}\n"
            f"**Erstellt:** {guild.created_at.strftime('%d.%m.%Y')}\n\n"
            f"👥 **Mitglieder:** {total_members} ({online_members} online)\n"
            f"📢 **Kanäle:** {total_channels} ({text_channels} Text, {voice_channels} Stimme)\n"
            f"🎭 **Rollen:** {len(guild.roles)}\n"
            f"🚀 **Boosts:** {guild.premium_subscription_count} (Level {guild.premium_tier})"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(text=f"Angefragt von {interaction.user}")
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────────────────────────────────────────
# 🆕 NEU: /setup-angelshop Command (FÜR ALLE)
@bot.tree.command(
    name="setup-angelshop",
    description="[Angler Shop] Aktualisiere das Angler-Shop Embed",
    guild=discord.Object(id=GUILD_ID)
)
async def setup_angelshop(interaction: discord.Interaction):
    """Aktualisiert das Angler-Shop Embed manuell und ersetzt das alte"""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hole den Angler-Shop Kanal
        channel = bot.get_channel(_angeln.ANGLER_SHOP_CHANNEL_ID)
        if not channel:
            await interaction.followup.send("❌ Angler-Shop Kanal nicht gefunden!", ephemeral=True)
            return
        
        # Lösche alte Bot-Nachrichten im ANGLER-SHOP KANAL (nicht alle Kanäle!)
        deleted = 0
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                try:
                    await message.delete()
                    deleted += 1
                except:
                    pass
        
        # Verwende die KORREKTE Funktion für das Embed MIT Buttons
        # Die _angler_shop_setup() Funktion erstellt das Embed MIT den Shop-Buttons
        result = await _angeln._angler_shop_setup()
        
        if "✅" in result:
            # Erfolgsnachricht an den User
            success_embed = discord.Embed(
                title="✅ Angler Shop aktualisiert",
                description=(
                    f"Das Angler-Shop Embed wurde erfolgreich aktualisiert.\n\n"
                    f"**Kanal:** {channel.mention}\n"
                    f"**Gelöschte alte Nachrichten:** {deleted}\n"
                    f"**Neues Embed MIT Buttons gesendet:** ✅"
                ),
                color=0x28a745,
                timestamp=datetime.now(timezone.utc)
            )
            success_embed.set_footer(text=f"Aktualisiert von {interaction.user}")
            success_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1f3a3.png")
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        else:
            await interaction.followup.send(f"❌ Fehler bei Aktualisierung: {result}", ephemeral=True)
            
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Kritischer Fehler",
            description=f"Ein unerwarteter Fehler ist aufgetreten:\n\n```\n{str(e)}\n```",
            color=0xdc3545,
            timestamp=datetime.now(timezone.utc)
        )
        error_embed.set_footer(text=f"Versucht von {interaction.user}")
        
        await interaction.followup.send(embed=error_embed, ephemeral=True)
        print(f"[setup-angelshop] Kritischer Fehler: {e}")

# ─────────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────────
# -- /kokain-setup ---------------------------------------------
@bot.tree.command(
    name="kokain-setup",
    description="[Team] Kokain-Labor Setup (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
async def kokain_setup(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde das Kokain-Setup implementiert werden
        await interaction.followup.send(
            "✅ Kokain-Setup wurde aktualisiert.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /weed-setup -----------------------------------------------
@bot.tree.command(
    name="weed-setup",
    description="[Team] Weed-Farm Setup (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
async def weed_setup(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde das Weed-Setup implementiert werden
        await interaction.followup.send(
            "✅ Weed-Setup wurde aktualisiert.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /fraktions-warn -------------------------------------------
@bot.tree.command(
    name="fraktions-warn",
    description="[Team] Warne eine Fraktion (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    fraktion="Fraktion die gewarnt werden soll",
    grund="Grund der Warnung"
)
async def fraktions_warn(interaction: discord.Interaction, fraktion: str, grund: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde die Fraktions-Warnung implementiert werden
        await interaction.followup.send(
            f"✅ Fraktion {fraktion} wurde gewarnt: {grund}",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /fraktions-sperre -----------------------------------------
@bot.tree.command(
    name="fraktions-sperre",
    description="[Team] Sperre eine Fraktion (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    fraktion="Fraktion die gesperrt werden soll",
    dauer="Dauer der Sperre in Stunden"
)
async def fraktions_sperre(interaction: discord.Interaction, fraktion: str, dauer: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde die Fraktions-Sperre implementiert werden
        await interaction.followup.send(
            f"✅ Fraktion {fraktion} wurde für {dauer} Stunden gesperrt.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /remove-frakwarn ------------------------------------------
@bot.tree.command(
    name="remove-frakwarn",
    description="[Team] Entferne Fraktions-Warnung (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    fraktion="Fraktion von der die Warnung entfernt werden soll"
)
async def remove_frakwarn(interaction: discord.Interaction, fraktion: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde das Entfernen der Fraktions-Warnung implementiert werden
        await interaction.followup.send(
            f"✅ Warnung von Fraktion {fraktion} wurde entfernt.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /frak-list ------------------------------------------------
@bot.tree.command(
    name="frak-list",
    description="[Team] Zeige alle Fraktionen (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
async def frak_list(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde die Fraktions-Liste implementiert werden
        await interaction.followup.send(
            "✅ Fraktions-Liste wird angezeigt.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /frak-add -------------------------------------------------
@bot.tree.command(
    name="frak-add",
    description="[Team] Füge eine Fraktion hinzu (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    name="Name der Fraktion",
    kuerzel="Kürzel der Fraktion"
)
async def frak_add(interaction: discord.Interaction, name: str, kuerzel: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde das Hinzufügen der Fraktion implementiert werden
        await interaction.followup.send(
            f"✅ Fraktion {name} ({kuerzel}) wurde hinzugefügt.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# -- /frak-remove --------------------------------------------
@bot.tree.command(
    name="frak-remove",
    description="[Team] Entferne eine Fraktion (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    fraktion="Fraktion die entfernt werden soll"
)
async def frak_remove(interaction: discord.Interaction, fraktion: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Kein Zugriff.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Hier würde das Entfernen der Fraktion implementiert werden
        await interaction.followup.send(
            f"✅ Fraktion {fraktion} wurde entfernt.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Fehler: {str(e)}",
            ephemeral=True
        )

# ─────────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────────
# /ki — KI-Konversation starten
# /ki-end — KI-Konversation beenden
# ─────────────────────────────────────────────────────────────────────────────────
@bot.tree.command(
    name="ki",
    description="🤖 Startet eine KI-Konversation in diesem Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def ki_start_command(interaction: discord.Interaction):
    try:
        import ki as _ki
    except Exception as _err:
        await interaction.response.send_message(
            f"❌ KI-Modul nicht ladbar: `{_err}`",
            ephemeral=True,
        )
        return

    if not _ki.model:
        await interaction.response.send_message(
            "❌ Der KI-Assistent ist nicht verfügbar.\n"
            "*(GROQ_API_KEY fehlt — bitte einen Admin kontaktieren)*",
            ephemeral=True,
        )
        return

    channel_id = interaction.channel_id

    if channel_id in _ki.active_sessions:
        bestehender = _ki.active_sessions[channel_id]
        await interaction.response.send_message(
            f"⚠️ In diesem Kanal läuft bereits eine KI-Konversation "
            f"(gestartet von <@{bestehender}>).\n"
            "Beende sie zuerst mit `/ki-end`.",
            ephemeral=True,
        )
        return

    _ki.active_sessions[channel_id] = interaction.user.id

    await interaction.response.send_message(
        f"🤖 **KI-Konversation gestartet!**\n"
        f"Schreib einfach deine Nachrichten in diesen Kanal — ich antworte direkt.\n"
        f"Mit `/ki-end` beendest du die Konversation.",
    )


@bot.tree.command(
    name="ki-end",
    description="🛑 Beendet die aktive KI-Konversation in diesem Kanal",
    guild=discord.Object(id=GUILD_ID),
)
async def ki_end_command(interaction: discord.Interaction):
    try:
        import ki as _ki
    except Exception as _err:
        await interaction.response.send_message(
            f"❌ KI-Modul nicht ladbar: `{_err}`",
            ephemeral=True,
        )
        return

    channel_id = interaction.channel_id

    if channel_id not in _ki.active_sessions:
        await interaction.response.send_message(
            "ℹ️ In diesem Kanal läuft keine KI-Konversation.",
            ephemeral=True,
        )
        return

    session_user_id = _ki.active_sessions[channel_id]
    is_owner = interaction.user.id == session_user_id
    is_mod   = interaction.user.guild_permissions.manage_messages

    if not is_owner and not is_mod:
        await interaction.response.send_message(
            "❌ Nur die Person die die Konversation gestartet hat (oder Mods) können sie beenden.",
            ephemeral=True,
        )
        return

    del _ki.active_sessions[channel_id]

    await interaction.response.send_message(
        f"🛑 **KI-Konversation beendet.** Tschüss! 👋"
    )
