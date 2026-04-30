        off_count += 1
                gesamt += 1

        lines.append("")

    beschreibung = "\n".join(lines)
    beschreibung += (
        "\n\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        f"\U0001F465 **Aktuelle Teammitglieder gesamt:** {gesamt}\n\n"
        f"\U0001F7E2 **On Duty** ({on_count}) \u2014 *Teammitglied ist aktiv im Support und Co.*\n"
        f"\U0001F534 **Off Duty** ({off_count}) \u2014 *Teammitglied bearbeitet derzeit keine Supportanfragen und Co.*"
    )

    embed = discord.Embed(
        title="\U0001F3C6 Team \u00DCbersicht \u2014 Paradise City Roleplay",
        description=beschreibung,
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2022 Team-\u00DCbersicht | Zuletzt aktualisiert")
    return embed


# ── Persistent View ───────────────────────────────────────────────────────────────────

class TeamOverviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _is_team(self, member: discord.Member) -> bool:
        return any(r.id in TEAM_ROLE_IDS for r in member.roles)

    async def _update_embed(self, interaction: discord.Interaction):
        duty_data = load_duty()
        embed     = build_team_embed(interaction.guild, duty_data)
        try:
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(
        label="On Duty",
        emoji="\U0001F4F1",
        style=discord.ButtonStyle.success,
        custom_id="team_on_duty",
    )
    async def on_duty_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_team(interaction.user):
            await interaction.response.send_message(
                "\u274C Nur Teammitglieder k\u00F6nnen ihren Dienststatus \u00E4ndern.",
                ephemeral=True,
            )
            return

        duty_data = load_duty()
        uid = interaction.user.id
        if uid not in duty_data["on_duty"]:
            duty_data["on_duty"].append(uid)
            save_duty(duty_data)

        await interaction.response.send_message(
            "\u2705 Du bist jetzt **\U0001F7E2 On Duty**.", ephemeral=True
        )
        await self._update_embed(interaction)

    @discord.ui.button(
        label="Off Duty",
        emoji="\U0001F4F5",
        style=discord.ButtonStyle.danger,
        custom_id="team_off_duty",
    )
    async def off_duty_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_team(interaction.user):
            await interaction.response.send_message(
                "\u274C Nur Teammitglieder k\u00F6nnen ihren Dienststatus \u00E4ndern.",
                ephemeral=True,
            )
            return

        duty_data = load_duty()
        uid = interaction.user.id
        if uid in duty_data["on_duty"]:
            duty_data["on_duty"].remove(uid)
            save_duty(duty_data)

        await interaction.response.send_message(
            "\u2705 Du bist jetzt **\U0001F534 Off Duty**.", ephemeral=True
        )
        await self._update_embed(interaction)


# ── Auto Setup ────────────────────────────────────────────────────────────────────────

async def auto_team_setup():
    for guild in bot.guilds:
        channel = guild.get_channel(TEAM_OVERVIEW_CHANNEL_ID)
        if not channel:
            continue

        duty_data = load_duty()
        embed     = build_team_embed(guild, duty_data)
        view      = TeamOverviewView()

        # Vorhandene Nachricht bearbeiten
        if duty_data.get("message_id"):
            try:
                msg = await channel.fetch_message(duty_data["message_id"])
                await msg.edit(embed=embed, view=view)
                print(f"[team_overview] Embed aktualisiert in #{channel.name}")
                return
            except Exception:
                pass

        # Altes Embed suchen und löschen
        try:
            async for msg in channel.history(limit=20):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Team \u00DCbersicht" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            break
        except Exception:
            pass

        # Neu posten
        try:
            new_msg = await channel.send(embed=embed, view=view)
            duty_data["message_id"] = new_msg.id
            save_duty(duty_data)
            print(f"[team_overview] Embed gepostet in #{channel.name}")
        except Exception as e:
            print(f"[team_overview] Fehler: {e}")


# ── Slash Command: /team-rollen (einmaliger Debug-Befehl) ────────────────────────────

@bot.tree.command(
    name="team-rollen",
    description="[Admin] Zeigt alle Rollen-IDs des Servers",
    guild=discord.Object(id=GUILD_ID),
)
async def team_rollen(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id in {INHABER_ROLE_ID} for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    zeilen = ["**Rollen nach Position (oben = höchste Rolle):**\n"]
    for role in sorted(interaction.guild.roles, reverse=True):
        if role.name == "@everyone":
            continue
        zeilen.append(f"`{role.id}` — **{role.name}**")

    text = "\n".join(zeilen)
    # Discord Limit: 2000 Zeichen — aufteilen falls nötig
    chunks = []
    aktuell = ""
    for z in zeilen:
        if len(aktuell) + len(z) + 1 > 1900:
            chunks.append(aktuell)
            aktuell = z + "\n"
        else:
            aktuell += z + "\n"
    if aktuell:
        chunks.append(aktuell)

    await interaction.response.send_message(chunks[0], ephemeral=True)
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=True)


# ── Slash Command: /setup-teamembed ──────────────────────────────────────────────────

@bot.tree.command(
    name="setup-teamembed",
    description="[Team] Löscht das alte Team-Embed und postet ein neues mit allen Änderungen",
    guild=discord.Object(id=GUILD_ID),
)
async def setup_teamembed(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID and not any(r.id in TEAM_ROLE_IDS | {INHABER_ROLE_ID} for r in interaction.user.roles):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    for guild in bot.guilds:
        channel = guild.get_channel(TEAM_OVERVIEW_CHANNEL_ID)
        if not channel:
            continue

        duty_data = load_duty()

        # Alle Bot-Nachrichten mit Team-Embed im Kanal löschen
        try:
            async for msg in channel.history(limit=50):
                if msg.author.id == bot.user.id and msg.embeds:
                    for emb in msg.embeds:
                        if emb.title and "Team \u00DCbersicht" in emb.title:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            break
        except Exception as e:
            print(f"[team_overview] Fehler beim Löschen: {e}")

        # message_id zurücksetzen und neu posten
        duty_data["message_id"] = None
        save_duty(duty_data)

        embed   = build_team_embed(guild, duty_data)
        view    = TeamOverviewView()
        new_msg = await channel.send(embed=embed, view=view)
        duty_data["message_id"] = new_msg.id
        save_duty(duty_data)
        print(f"[team_overview] Neues Embed gepostet in #{channel.name}")

    await interaction.followup.send("\u2705 Team-Embed wurde neu erstellt.", ephemeral=True)
