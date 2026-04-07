@bot.event
async def on_member_join(member):
    # Rolle vergeben
    rolle = member.guild.get_role(1490855725516460234)
    if rolle:
        try:
            await member.add_roles(rolle)
        except discord.Forbidden:
            print(f"Konnte Rolle an {member.name} nicht vergeben (Fehlende Rechte).")

    # Willkommens-Embed
    embed = discord.Embed(
        title="Willkommen bei Kryptik Roleplay!",
        description=(
            "Dein RP-Server mit ultimativem Spaß und hochwertigem RP.\n\n"
            "Wir wünschen dir viel Spaß auf unserem Server und hoffen, dass du dich gut zurechtfindest.\n\n"
            "Solltest du mal Schwierigkeiten haben, melde dich gerne jederzeit über ein Support-Ticket im Channel <#1490855943230066818>."
        ),
        color=0x00BFFF
    )
    
    try:
        await member.send(content=f"Hallo {member.mention}!", embed=embed)
    except discord.Forbidden:
        print(f"Konnte {member.name} keine DM senden.")
