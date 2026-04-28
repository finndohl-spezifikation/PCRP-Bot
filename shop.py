# -*- coding: utf-8 -*-
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# shop.py \u2014 3-Shop-System (Kwik-E-Markt / Baumarkt / Schwarzmarkt)
# Paradise City Roleplay Discord Bot
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

import json
import re as _re
from config import *
from helpers import is_admin
from economy_helpers import (
    load_economy, save_economy, get_user, load_shop, save_shop,
    load_team_shop, save_team_shop, load_angler_shop, save_angler_shop,
    find_shop_item, find_inventory_item, normalize_item_name,
    has_citizen_or_wage, shop_item_autocomplete, all_shops_item_autocomplete,
    channel_error, log_transaction
)
from handy import give_handy_channel_access

# \u2500\u2500 Konstanten \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_RUBBELLOS_NAME       = "\U0001F39F\uFE0F| Rubbellos"
_RUBBELLOS_TAGESLIMIT = 3

SCHWARZMARKT_ROLE_ID = 1490855730767597738

SHOPS = {
    "kwik": {
        "label":   "\U0001F3EA Kwik-E-Markt",
        "emoji":   "\U0001F3EA",
        "channel": 1490890311755628584,
    },
    "baumarkt": {
        "label":   "\U0001F528 Baumarkt",
        "emoji":   "\U0001F528",
        "channel": 1492976742497783818,
    },
    "schwarzmarkt": {
        "label":   "\U0001F575\uFE0F Schwarzmarkt",
        "emoji":   "\U0001F575\uFE0F",
        "channel": 1492977067665526804,
    },
}

CHANNEL_TO_SHOP = {v["channel"]: k for k, v in SHOPS.items()}

# user_id -> [{"name", "qty", "price", "shop"}]
_SHOP_CARTS: dict[int, list] = {}

_SHOP_EMBED_COLORS = {
    "kwik":         0xF1C40F,
    "baumarkt":     0xE67E22,
    "schwarzmarkt": 0x2C2F33,
}


# \u2500\u2500 Hilfsfunktionen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _has_schwarzmarkt_access(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {ADMIN_ROLE_ID, MOD_ROLE_ID, SCHWARZMARKT_ROLE_ID})


def _is_shop_admin(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return bool(role_ids & {ADMIN_ROLE_ID, SHOP_ADMIN_ROLE_ID})


def _item_shop(item: dict) -> str:
    return item.get("shop", "kwik")


_PAGE_SIZE = 15


def _get_shop_items(shop_key: str, member: discord.Member, search: str = "") -> list:
    role_ids = {r.id for r in member.roles}
    is_adm   = ADMIN_ROLE_ID in role_ids
    items = [
        i for i in load_shop()
        if _item_shop(i) == shop_key
        and (is_adm or not i.get("allowed_role") or i.get("allowed_role") in role_ids)
    ]
    if search:
        s = search.lower()
        items = [i for i in items if s in _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', i["name"]).strip().lower()]
    return items


def _build_shop_embed(shop_key: str, member: discord.Member, page: int = 0, search: str = "") -> tuple[discord.Embed, int]:
    shop     = SHOPS[shop_key]
    filtered = _get_shop_items(shop_key, member, search=search)
    eco      = load_economy()
    ud       = get_user(eco, member.id)
    cash     = int(ud.get("cash", 0))

    total_pages = max(1, -(-len(filtered) // _PAGE_SIZE))
    page        = max(0, min(page, total_pages - 1))
    page_items  = filtered[page * _PAGE_SIZE : (page + 1) * _PAGE_SIZE]

    lines = []
    for item in page_items:
        clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', item['name']).strip()
        lines.append(f"\u27A4 **{clean}**\u3000\u2014\u3000`{item['price']:,} \U0001F4B5`")

    sep         = "\u2015" * 22
    empty_hint  = f"*Keine Ergebnisse f\u00FCr \u201E{search}\u201C.*" if search else "*Dieser Shop ist aktuell leer.*"
    desc        = sep + "\n" + ("\n".join(lines) if lines else empty_hint) + "\n" + sep

    title = f"{shop['emoji']}  {shop['label']}"
    if search:
        title += f"  \U0001F50D {search}"

    embed = discord.Embed(
        title=title,
        description=desc,
        color=_SHOP_EMBED_COLORS.get(shop_key, LOG_COLOR),
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(name="\U0001F4B5 Dein Bargeld", value=f"**{cash:,} $**", inline=True)

    cart     = _SHOP_CARTS.get(member.id, [])
    subtotal = sum(c["price"] * c["qty"] for c in cart)
    count    = sum(c["qty"] for c in cart)
    if count > 0:
        embed.add_field(
            name="\U0001F6D2 Warenkorb",
            value=f"**{count}x** \u2014 {subtotal:,} $",
            inline=True
        )
    else:
        embed.add_field(name="\U0001F6D2 Warenkorb", value="leer", inline=True)

    footer = "Item w\u00E4hlen \u2022 Nur Bargeld"
    if total_pages > 1:
        footer += f"  |  Seite {page + 1}/{total_pages}"
    embed.set_footer(text=f"{shop['emoji']} {footer}")
    return embed, total_pages


# \u2500\u2500 Kauf-Logik (Hilfsfunktion) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

async def _execute_buy(
    interaction: discord.Interaction,
    item: dict,
    menge: int,
    shop_key: str,
) -> bool:
    """F\u00FChrt den Kauf durch. Gibt True zur\u00FCck wenn erfolgreich."""
    role_ids = {r.id for r in interaction.user.roles}
    is_adm   = ADMIN_ROLE_ID in role_ids

    if not is_adm and not has_citizen_or_wage(interaction.user):
        await interaction.response.send_message("\u274C Du hast keine Berechtigung.", ephemeral=True)
        return False

    if menge < 1 or menge > 100:
        await interaction.response.send_message("\u274C Menge muss zwischen **1** und **100** liegen.", ephemeral=True)
        return False

    # Schwarzmarkt-Zugang
    if shop_key == "schwarzmarkt" and not is_adm and not _has_schwarzmarkt_access(interaction.user):
        await interaction.response.send_message("\u274C Du hast keinen Zugang zum Schwarzmarkt.", ephemeral=True)
        return False

    # Rollen-Check f\u00FCr Item
    allowed_role = item.get("allowed_role")
    if allowed_role and not is_adm and allowed_role not in role_ids:
        rolle_obj = interaction.guild.get_role(allowed_role)
        rname     = rolle_obj.name if rolle_obj else f"<@&{allowed_role}>"
        await interaction.response.send_message(
            f"\u274C Dieses Item ist nur f\u00FCr die Rolle **{rname}** erh\u00E4ltlich.", ephemeral=True
        )
        return False

    eco       = load_economy()
    user_data = get_user(eco, interaction.user.id)

    # Rubbellos-Tageslimit
    if normalize_item_name(item["name"]) == normalize_item_name(_RUBBELLOS_NAME) and not is_adm:
        today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rb_daily = user_data.get("rubbellos_daily", {"date": "", "count": 0})
        rb_count = rb_daily["count"] if rb_daily.get("date") == today else 0
        if rb_count + menge > _RUBBELLOS_TAGESLIMIT:
            verbleibend = max(0, _RUBBELLOS_TAGESLIMIT - rb_count)
            await interaction.response.send_message(
                f"\u274C Du kannst nur **{_RUBBELLOS_TAGESLIMIT} Rubbellose pro Tag** kaufen.\n"
                f"Heute gekauft: **{rb_count}** \u2014 noch kaufbar: **{verbleibend}**.",
                ephemeral=True
            )
            return False

    gesamtpreis = item["price"] * menge
    if user_data["cash"] < gesamtpreis:
        await interaction.response.send_message(
            f"\u274C Nicht genug **Bargeld**.\n"
            f"**Preis:** {item['price']:,} \U0001F4B5 \u00D7 {menge} = **{gesamtpreis:,} \U0001F4B5**\n"
            f"**Dein Bargeld:** {user_data['cash']:,} \U0001F4B5\n"
            f"\u2139\uFE0F Hebe Geld mit `/auszahlen` ab.",
            ephemeral=True
        )
        return False

    user_data["cash"] -= gesamtpreis
    user_data.setdefault("inventory", [])
    for _ in range(menge):
        user_data["inventory"].append(item["name"])

    if normalize_item_name(item["name"]) == normalize_item_name(_RUBBELLOS_NAME):
        today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        rb_daily = user_data.get("rubbellos_daily", {"date": "", "count": 0})
        rb_count = rb_daily["count"] if rb_daily.get("date") == today else 0
        user_data["rubbellos_daily"] = {"date": today, "count": rb_count + menge}

    save_economy(eco)

    if normalize_item_name(item["name"]) == normalize_item_name(HANDY_ITEM_NAME):
        await give_handy_channel_access(interaction.guild, interaction.user)

    menge_text = f" \u00D7 {menge}" if menge > 1 else ""
    embed = discord.Embed(
        title="\u2705 Gekauft!",
        description=(
            f"Du hast **{item['name']}**{menge_text} f\u00FCr **{gesamtpreis:,} \U0001F4B5** gekauft.\n"
            f"**Verbleibendes Bargeld:** {user_data['cash']:,} \U0001F4B5"
        ),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    return True


# \u2500\u2500 Mengen-Modal (nach Item-Auswahl per Dropdown) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class BuyMengeModal(discord.ui.Modal):
    def __init__(self, item: dict, shop_key: str):
        import re as _re
        _clean = _re.sub(r'<a?:[^:]+:\d+>\s*\|?\s*', '', item['name']).strip()
        super().__init__(title=f"\U0001F6D2 {_clean[:35]} kaufen")
        self.item     = item
        self.shop_key = shop_key

        self.menge_input = discord.ui.TextInput(
            label=f"Menge  (Preis: {item['price']:,}$ pro St\u00FCck)",
            placeholder="z.B. 1",
            default="1",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.menge_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            menge = int(self.menge_input.value.strip())
        except ValueError:
            await interaction.response.send_message("\u274C Bitte eine g\u00FCltige Zahl eingeben.", ephemeral=True)
            return

        if menge < 1 or menge > 100:
            await interaction.response.send_message("\u274C Menge muss zwischen **1** und **100** liegen.", ephemeral=True)
            return

        uid  = interaction.user.id
        cart = _SHOP_CARTS.setdefault(uid, [])
        for entry in cart:
            if entry["name"] == self.item["name"] and entry["shop"] == self.shop_key:
                entry["qty"] += menge
                break
        else:
            cart.append({"name": self.item["name"], "qty": menge, "price": self.item["price"], "shop": self.shop_key})

        eco      = load_economy()
        ud       = get_user(eco, uid)
        cash     = int(ud.get("cash", 0))
        subtotal = sum(c["price"] * c["qty"] for c in cart)
        count    = sum(c["qty"] for c in cart)

        clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', self.item["name"]).strip()
        lines = []
        for c in cart:
            c_clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', c["name"]).strip()
            lines.append(f"\u27A4 **{c_clean}** \u00D7 {c['qty']} \u2014 `{c['price'] * c['qty']:,} \U0001F4B5`")

        sep   = "\u2015" * 22
        embed = discord.Embed(
            title="\U0001F6D2 Warenkorb",
            description=sep + "\n" + "\n".join(lines) + "\n" + sep,
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F4B0 Zwischensumme", value=f"**{subtotal:,} $**", inline=True)
        embed.add_field(name="\U0001F4B5 Dein Bargeld",  value=f"**{cash:,} $**",      inline=True)
        if cash < subtotal:
            embed.add_field(
                name="\u26A0\uFE0F Hinweis",
                value="Nicht genug Bargeld f\u00FCr den gesamten Warenkorb!",
                inline=False
            )
        embed.set_footer(text="Paradise City Roleplay \u2022 Shop")
        await interaction.response.send_message(embed=embed, view=CartCheckoutView(uid, interaction.guild), ephemeral=True)


# \u2500\u2500 Direkt-Kauf-Modal (Itemname + Menge frei eintippen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500

class DirektkaufModal(discord.ui.Modal, title="\u270F\uFE0F Direkt kaufen"):
    item_input = discord.ui.TextInput(
        label="Itemname",
        placeholder="z.B. Burger, Holz, Pistole \u2026",
        min_length=1,
        max_length=100,
        required=True
    )
    menge_input = discord.ui.TextInput(
        label="Menge",
        placeholder="z.B. 1",
        default="1",
        min_length=1,
        max_length=3,
        required=True
    )

    def __init__(self, shop_key: str):
        super().__init__()
        self.shop_key = shop_key

    async def on_submit(self, interaction: discord.Interaction):
        try:
            menge = int(self.menge_input.value.strip())
        except ValueError:
            await interaction.response.send_message("\u274C Bitte eine g\u00FCltige Zahl als Menge eingeben.", ephemeral=True)
            return

        if menge < 1 or menge > 100:
            await interaction.response.send_message("\u274C Menge muss zwischen **1** und **100** liegen.", ephemeral=True)
            return

        items = load_shop()
        item  = find_shop_item(items, self.item_input.value.strip())
        if not item:
            await interaction.response.send_message(
                f"\u274C Item **{self.item_input.value}** nicht gefunden.\n"
                "Schaue dir die Liste oben an und achte auf den genauen Namen.",
                ephemeral=True
            )
            return

        uid  = interaction.user.id
        cart = _SHOP_CARTS.setdefault(uid, [])
        for entry in cart:
            if entry["name"] == item["name"] and entry["shop"] == self.shop_key:
                entry["qty"] += menge
                break
        else:
            cart.append({"name": item["name"], "qty": menge, "price": item["price"], "shop": self.shop_key})

        eco      = load_economy()
        ud       = get_user(eco, uid)
        cash     = int(ud.get("cash", 0))
        subtotal = sum(c["price"] * c["qty"] for c in cart)
        lines    = []
        for c in cart:
            c_clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', c["name"]).strip()
            lines.append(f"\u27A4 **{c_clean}** \u00D7 {c['qty']} \u2014 `{c['price'] * c['qty']:,} \U0001F4B5`")

        sep   = "\u2015" * 22
        embed = discord.Embed(
            title="\U0001F6D2 Warenkorb",
            description=sep + "\n" + "\n".join(lines) + "\n" + sep,
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F4B0 Zwischensumme", value=f"**{subtotal:,} $**", inline=True)
        embed.add_field(name="\U0001F4B5 Dein Bargeld",  value=f"**{cash:,} $**",      inline=True)
        if cash < subtotal:
            embed.add_field(
                name="\u26A0\uFE0F Hinweis",
                value="Nicht genug Bargeld f\u00FCr den gesamten Warenkorb!",
                inline=False
            )
        embed.set_footer(text="Paradise City Roleplay \u2022 Shop")
        await interaction.response.send_message(embed=embed, view=CartCheckoutView(uid, interaction.guild), ephemeral=True)


# \u2500\u2500 Item-Auswahl Select \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class BuyItemSelect(discord.ui.Select):
    def __init__(self, shop_key: str, page_items: list):
        import re
        self.shop_key = shop_key
        options = []
        for item in page_items[:25]:
            name = item["name"]
            custom = re.search(r'<(a?):([^:]+):(\d+)>', name)
            label  = re.sub(r'<a?:[^:]+:\d+>\s*\|?\s*', '', name).strip() or name
            if custom:
                emoji = discord.PartialEmoji(
                    animated=bool(custom.group(1)),
                    name=custom.group(2),
                    id=int(custom.group(3))
                )
            else:
                emoji = None
            opt = discord.SelectOption(
                label=label[:100],
                value=name[:100],
                description=f"{item['price']:,} \U0001f4b5",
                emoji=emoji
            )
            options.append(opt)
        super().__init__(
            placeholder="\U0001F6D2 Items ausw\u00E4hlen (max. 10 gleichzeitig)...",
            min_values=1,
            max_values=min(len(options), 10),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        items_db = load_shop()
        selected = []
        for name in self.values:
            item = find_shop_item(items_db, name)
            if item:
                selected.append(item)

        if not selected:
            await interaction.response.send_message("\u274C Items nicht mehr verf\u00FCgbar.", ephemeral=True)
            return

        if len(selected) == 1:
            await interaction.response.send_modal(BuyMengeModal(selected[0], self.shop_key))
        elif len(selected) <= 5:
            # Modal mit je einem Mengen-Feld pro Item
            await interaction.response.send_modal(MultiMengeModal(selected, self.shop_key))
        else:
            # 6-10 Items: alle mit Menge 1 in den Warenkorb
            uid  = interaction.user.id
            cart = _SHOP_CARTS.setdefault(uid, [])
            for item in selected:
                for entry in cart:
                    if entry["name"] == item["name"] and entry["shop"] == self.shop_key:
                        entry["qty"] += 1
                        break
                else:
                    cart.append({"name": item["name"], "qty": 1, "price": item["price"], "shop": self.shop_key})

            eco      = load_economy()
            ud       = get_user(eco, uid)
            cash     = int(ud.get("cash", 0))
            subtotal = sum(c["price"] * c["qty"] for c in cart)
            lines    = []
            for c in cart:
                c_clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', c["name"]).strip()
                lines.append(f"\u27A4 **{c_clean}** \u00D7 {c['qty']} \u2014 `{c['price'] * c['qty']:,} \U0001F4B5`")
            sep   = "\u2015" * 22
            embed = discord.Embed(
                title="\U0001F6D2 Warenkorb",
                description=sep + "\n" + "\n".join(lines) + "\n" + sep,
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="\U0001F4B0 Zwischensumme", value=f"**{subtotal:,} $**", inline=True)
            embed.add_field(name="\U0001F4B5 Dein Bargeld",  value=f"**{cash:,} $**",      inline=True)
            embed.add_field(
                name="\u2139\uFE0F Hinweis",
                value="Bei mehr als 5 Items wird Menge **1** gesetzt. Nutze \u201E\u270F\uFE0F Direkt kaufen\u201C um Mengen anzupassen.",
                inline=False
            )
            if cash < subtotal:
                embed.add_field(name="\u26A0\uFE0F", value="Nicht genug Bargeld f\u00FCr den gesamten Warenkorb!", inline=False)
            embed.set_footer(text="Paradise City Roleplay \u2022 Shop")
            await interaction.response.send_message(embed=embed, view=CartCheckoutView(uid, interaction.guild), ephemeral=True)


# \u2500\u2500 Multi-Item Mengen-Modal (2\u20135 Items gleichzeitig) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class MultiMengeModal(discord.ui.Modal):
    def __init__(self, items: list, shop_key: str):
        super().__init__(title="\U0001F6D2 Mengen eingeben")
        self.items    = items
        self.shop_key = shop_key
        self.inputs   = []

        for item in items[:5]:
            clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', item["name"]).strip()
            inp = discord.ui.TextInput(
                label=f"{clean[:40]}  ({item['price']:,} $)",
                placeholder="Menge (z.B. 1)",
                default="1",
                min_length=1,
                max_length=3,
                required=True
            )
            self.inputs.append(inp)
            self.add_item(inp)

    async def on_submit(self, interaction: discord.Interaction):
        uid  = interaction.user.id
        cart = _SHOP_CARTS.setdefault(uid, [])
        errors = []

        for item, inp in zip(self.items, self.inputs):
            try:
                menge = int(inp.value.strip())
            except ValueError:
                errors.append(f"\u274C **{item['name']}**: ung\u00FCltige Menge")
                continue
            if menge < 1 or menge > 100:
                errors.append(f"\u274C **{item['name']}**: Menge 1\u2013100")
                continue
            for entry in cart:
                if entry["name"] == item["name"] and entry["shop"] == self.shop_key:
                    entry["qty"] += menge
                    break
            else:
                cart.append({"name": item["name"], "qty": menge, "price": item["price"], "shop": self.shop_key})

        eco      = load_economy()
        ud       = get_user(eco, uid)
        cash     = int(ud.get("cash", 0))
        subtotal = sum(c["price"] * c["qty"] for c in cart)
        lines    = []
        for c in cart:
            c_clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', c["name"]).strip()
            lines.append(f"\u27A4 **{c_clean}** \u00D7 {c['qty']} \u2014 `{c['price'] * c['qty']:,} \U0001F4B5`")

        sep   = "\u2015" * 22
        embed = discord.Embed(
            title="\U0001F6D2 Warenkorb",
            description=sep + "\n" + "\n".join(lines) + "\n" + sep,
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="\U0001F4B0 Zwischensumme", value=f"**{subtotal:,} $**", inline=True)
        embed.add_field(name="\U0001F4B5 Dein Bargeld",  value=f"**{cash:,} $**",      inline=True)
        if errors:
            embed.add_field(name="\u26A0\uFE0F Fehler", value="\n".join(errors), inline=False)
        if cash < subtotal:
            embed.add_field(name="\u26A0\uFE0F Hinweis", value="Nicht genug Bargeld f\u00FCr den gesamten Warenkorb!", inline=False)
        embed.set_footer(text="Paradise City Roleplay \u2022 Shop")
        await interaction.response.send_message(embed=embed, view=CartCheckoutView(uid, interaction.guild), ephemeral=True)


# \u2500\u2500 Warenkorb-Checkout-View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class CartCheckoutView(TimedDisableView):
    def __init__(self, user_id: int, guild):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.user_id = user_id
        self.guild   = guild

    @discord.ui.button(label="\u2705 Kaufen", style=discord.ButtonStyle.green)
    async def checkout(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid  = interaction.user.id
        cart = _SHOP_CARTS.get(uid, [])
        if not cart:
            embed = discord.Embed(
                title="\U0001F6D2 Warenkorb leer",
                description="Dein Warenkorb ist leer.",
                color=0xE74C3C
            )
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            return

        eco       = load_economy()
        user_data = get_user(eco, uid)
        is_adm    = ADMIN_ROLE_ID in {r.id for r in interaction.user.roles}

        subtotal = sum(c["price"] * c["qty"] for c in cart)
        if user_data["cash"] < subtotal:
            await interaction.response.send_message(
                f"\u274C Nicht genug **Bargeld**.\n"
                f"**Summe:** {subtotal:,} \U0001F4B5 | **Bargeld:** {user_data['cash']:,} \U0001F4B5",
                ephemeral=True
            )
            return

        bought = []
        errors = []
        items  = load_shop()
        actual_cost = 0

        for entry in cart:
            item = find_shop_item(items, entry["name"])
            if not item:
                errors.append(f"\u274C **{entry['name']}** nicht mehr verf\u00FCgbar")
                continue

            menge       = entry["qty"]
            gesamtpreis = item["price"] * menge

            if normalize_item_name(item["name"]) == normalize_item_name(_RUBBELLOS_NAME) and not is_adm:
                today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                rb_daily = user_data.get("rubbellos_daily", {"date": "", "count": 0})
                rb_count = rb_daily["count"] if rb_daily.get("date") == today else 0
                rb_in_cart = sum(c["qty"] for c in cart if normalize_item_name(c["name"]) == normalize_item_name(_RUBBELLOS_NAME))
                if rb_count + rb_in_cart > _RUBBELLOS_TAGESLIMIT:
                    errors.append(f"\u274C Rubbellos-Tageslimit ({_RUBBELLOS_TAGESLIMIT}) erreicht")
                    continue

            user_data.setdefault("inventory", [])
            user_data["cash"] -= gesamtpreis
            actual_cost       += gesamtpreis
            for _ in range(menge):
                user_data["inventory"].append(item["name"])

            if normalize_item_name(item["name"]) == normalize_item_name(_RUBBELLOS_NAME):
                today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                rb_daily = user_data.get("rubbellos_daily", {"date": "", "count": 0})
                rb_count = rb_daily["count"] if rb_daily.get("date") == today else 0
                user_data["rubbellos_daily"] = {"date": today, "count": rb_count + menge}

            clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', item["name"]).strip()
            bought.append(f"\u2705 **{clean}** \u00D7 {menge} \u2014 {gesamtpreis:,} \U0001F4B5")

        if bought:
            names_summary = ", ".join(
                _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', e["name"]).strip() + f" \u00D7{e['qty']}"
                for e in cart
            )[:50]
            log_transaction(user_data, f"\U0001F6D2 Shop: {names_summary}", -actual_cost)

            for entry in cart:
                if normalize_item_name(entry["name"]) == normalize_item_name(HANDY_ITEM_NAME):
                    await give_handy_channel_access(interaction.guild, interaction.user)

            save_economy(eco)
            _SHOP_CARTS.pop(uid, None)

        lines = bought + errors
        embed = discord.Embed(
            title="\U0001F6D2 Kauf abgeschlossen" if bought else "\u274C Kauf fehlgeschlagen",
            description="\n".join(lines) if lines else "Nichts gekauft.",
            color=0x2ECC71 if bought else 0xE74C3C,
            timestamp=datetime.now(timezone.utc)
        )
        if bought:
            embed.add_field(
                name="\U0001F4B5 Verbleibendes Bargeld",
                value=f"**{user_data['cash']:,} $**",
                inline=True
            )
        embed.set_footer(text="Paradise City Roleplay \u2022 Shop")
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="\U0001F5D1\uFE0F Warenkorb leeren", style=discord.ButtonStyle.red)
    async def clear_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        _SHOP_CARTS.pop(interaction.user.id, None)
        embed = discord.Embed(
            title="\U0001F5D1\uFE0F Warenkorb geleert",
            description="Dein Warenkorb wurde geleert.",
            color=0xE74C3C
        )
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


# \u2500\u2500 Such-Modal \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class SuchModal(discord.ui.Modal):
    def __init__(self, shop_key: str):
        super().__init__(title="\U0001F50D Shop durchsuchen")
        self.shop_key = shop_key
        self.suchbegriff = discord.ui.TextInput(
            label="Suchbegriff",
            placeholder="z.\u202FB. Fahrrad, Waffe, ...",
            min_length=1,
            max_length=40,
            required=True
        )
        self.add_item(self.suchbegriff)

    async def on_submit(self, interaction: discord.Interaction):
        term  = self.suchbegriff.value.strip()
        embed, total_pages = _build_shop_embed(self.shop_key, interaction.user, page=0, search=term)
        view  = ShopPageView(self.shop_key, interaction.user, page=0, total_pages=total_pages, search=term)
        await interaction.response.edit_message(embed=embed, view=view)


# \u2500\u2500 Suchleiste (Select-Feld \u00FCber den Items) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class SearchBarSelect(discord.ui.Select):
    def __init__(self, shop_key: str, search: str = ""):
        self.shop_key = shop_key
        if search:
            placeholder = f"\U0001F50D Aktive Suche: {search[:30]}"
            options = [
                discord.SelectOption(
                    label=f"\U0001F50D Suche \u00E4ndern\u2026",
                    value="suchen",
                    description="Neuen Suchbegriff eingeben",
                    emoji="\u270F\uFE0F"
                ),
                discord.SelectOption(
                    label="Suche l\u00F6schen \u2014 alle Items zeigen",
                    value="loeschen",
                    description="Zur\u00FCck zur vollst\u00E4ndigen Liste",
                    emoji="\u274C"
                ),
            ]
        else:
            placeholder = "\U0001F50D Items suchen\u2026"
            options = [
                discord.SelectOption(
                    label="Suchbegriff eingeben\u2026",
                    value="suchen",
                    description="Tippe einen Begriff um Items zu finden",
                    emoji="\U0001F50D"
                ),
            ]
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "loeschen":
            view = interaction.message  # nur f\u00FCr Typ-Hint
            embed, total_pages = _build_shop_embed(self.shop_key, interaction.user, 0, search="")
            new_view = ShopPageView(self.shop_key, interaction.user, 0, total_pages, search="")
            await interaction.response.edit_message(embed=embed, view=new_view)
        else:
            await interaction.response.send_modal(SuchModal(self.shop_key))


# \u2500\u2500 Seiten-View (Bl\u00E4ttern + Kaufen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class ShopPageView(TimedDisableView):
    def __init__(self, shop_key: str, member: discord.Member, page: int, total_pages: int, search: str = ""):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.shop_key    = shop_key
        self.member      = member
        self.page        = page
        self.total_pages = total_pages
        self.search      = search
        self._rebuild()

    def _rebuild(self):
        self.clear_items()

        # Row 0: Suchleiste (Select-Feld, sieht aus wie eine Suchleiste)
        self.add_item(SearchBarSelect(self.shop_key, self.search))

        # Row 1: Items kaufen
        page_items = _get_shop_items(self.shop_key, self.member, search=self.search)[
            self.page * _PAGE_SIZE : (self.page + 1) * _PAGE_SIZE
        ]
        if page_items:
            buy_select      = BuyItemSelect(self.shop_key, page_items)
            buy_select.row  = 1
            self.add_item(buy_select)

        # Row 2: \u270F\uFE0F Direkt kaufen  |  \U0001F6D2 Kasse (falls Warenkorb gef\u00FCllt)
        _shop_key = self.shop_key

        direkt_btn = discord.ui.Button(
            label="\u270F\uFE0F Direkt kaufen",
            style=discord.ButtonStyle.primary,
            row=2
        )

        async def direkt_cb(interaction: discord.Interaction):
            await interaction.response.send_modal(DirektkaufModal(_shop_key))

        direkt_btn.callback = direkt_cb
        self.add_item(direkt_btn)

        cart = _SHOP_CARTS.get(self.member.id, [])
        if cart:
            subtotal  = sum(c["price"] * c["qty"] for c in cart)
            count     = sum(c["qty"] for c in cart)
            kasse_btn = discord.ui.Button(
                label=f"\U0001F6D2 Kasse ({count}x \u2014 {subtotal:,} $)",
                style=discord.ButtonStyle.success,
                row=2
            )

            async def kasse_cb(interaction: discord.Interaction):
                uid      = interaction.user.id
                cart_now = _SHOP_CARTS.get(uid, [])
                eco      = load_economy()
                ud       = get_user(eco, uid)
                cash     = int(ud.get("cash", 0))
                sub      = sum(c["price"] * c["qty"] for c in cart_now)
                lines    = []
                for c in cart_now:
                    c_clean = _re.sub(r'<a?:[^:]+:\d+>\s*[|]\s*', '', c["name"]).strip()
                    lines.append(f"\u27A4 **{c_clean}** \u00D7 {c['qty']} \u2014 `{c['price'] * c['qty']:,} \U0001F4B5`")
                sep   = "\u2015" * 22
                embed = discord.Embed(
                    title="\U0001F6D2 Warenkorb",
                    description=sep + "\n" + ("\n".join(lines) if lines else "Leer.") + "\n" + sep,
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="\U0001F4B0 Zwischensumme", value=f"**{sub:,} $**", inline=True)
                embed.add_field(name="\U0001F4B5 Dein Bargeld",  value=f"**{cash:,} $**", inline=True)
                if cash < sub:
                    embed.add_field(name="\u26A0\uFE0F Hinweis", value="Nicht genug Bargeld!", inline=False)
                embed.set_footer(text="Paradise City Roleplay \u2022 Shop")
                await interaction.response.send_message(embed=embed, view=CartCheckoutView(uid, interaction.guild), ephemeral=True)

            kasse_btn.callback = kasse_cb
            self.add_item(kasse_btn)

        # Row 3: \u2716 Schlie\u00DFen  |  \u25C0 Zur\u00FCck  |  Weiter \u25B6
        close_btn = discord.ui.Button(label="\u2716 Schlie\u00DFen", style=discord.ButtonStyle.danger, row=3)

        async def close_cb(interaction: discord.Interaction):
            try:
                await interaction.response.defer()
                await interaction.delete_original_response()
            except Exception:
                pass

        close_btn.callback = close_cb
        self.add_item(close_btn)

        prev  = discord.ui.Button(label="\u25C0 Zur\u00FCck", style=discord.ButtonStyle.secondary, disabled=self.page <= 0, row=3)
        next_ = discord.ui.Button(label="Weiter \u25B6",  style=discord.ButtonStyle.secondary, disabled=self.page >= self.total_pages - 1, row=3)

        async def prev_cb(interaction: discord.Interaction):
            self.page -= 1
            embed, self.total_pages = _build_shop_embed(self.shop_key, interaction.user, self.page, search=self.search)
            self.member = interaction.user
            self._rebuild()
            await interaction.response.edit_message(embed=embed, view=self)

        async def next_cb(interaction: discord.Interaction):
            self.page += 1
            embed, self.total_pages = _build_shop_embed(self.shop_key, interaction.user, self.page, search=self.search)
            self.member = interaction.user
            self._rebuild()
            await interaction.response.edit_message(embed=embed, view=self)

        prev.callback  = prev_cb
        next_.callback = next_cb

        if self.total_pages > 1:
            self.add_item(prev)
            self.add_item(next_)


# \u2500\u2500 Shop-Auswahl Select \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class ShopSelectView(TimedDisableView):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)

        options = []
        for key, cfg in SHOPS.items():
            if key == "schwarzmarkt" and not _has_schwarzmarkt_access(member):
                continue
            options.append(discord.SelectOption(
                label=cfg["label"],
                value=key,
                emoji=cfg["emoji"],
            ))

        select = discord.ui.Select(
            placeholder="Welchen Shop m\u00F6chtest du \u00F6ffnen?",
            options=options,
            custom_id="shop_select",
        )
        select.callback = self.on_select
        self.add_item(select)
        self.member = member

    async def on_select(self, interaction: discord.Interaction):
        shop_key = interaction.data["values"][0]
        shop_cfg = SHOPS[shop_key]
        is_adm   = ADMIN_ROLE_ID in {r.id for r in interaction.user.roles}

        if shop_key == "schwarzmarkt" and not _has_schwarzmarkt_access(interaction.user):
            await interaction.response.edit_message(
                embed=discord.Embed(description="\u274C Du hast keinen Zugang zum Schwarzmarkt.", color=0xE74C3C),
                view=None
            )
            return

        if not is_adm and interaction.channel.id != shop_cfg["channel"]:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    description=f"\u274C Der **{shop_cfg['label']}** ist nur in <#{shop_cfg['channel']}> zug\u00E4nglich.",
                    color=0xE74C3C
                ),
                view=None
            )
            return

        embed, total_pages = _build_shop_embed(shop_key, interaction.user, page=0)
        view = ShopPageView(shop_key, interaction.user, page=0, total_pages=total_pages)
        await interaction.response.edit_message(embed=embed, view=view)


# \u2500\u2500 Channel-Embed Views (persistent, ein Button pro Shop) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_SHOP_COLORS = {
    "kwik":         0xF1C40F,
    "baumarkt":     0xE67E22,
    "schwarzmarkt": 0x2C2F33,
}

_SHOP_BANNERS = {
    "kwik": (
        "\U0001F3EA **Willkommen im Kwik-E-Markt!**\n"
        "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        "\u27A4 Hier findest du allt\u00E4gliche Waren des Lebens.\n"
        "\u27A4 Lebensmittel, Getr\u00E4nke, Hygieneartikel und mehr.\n"
        "\u27A4 Bezahlung nur mit **Bargeld** (\U0001F4B5).\n\n"
        "Klicke auf den Button um den Shop zu \u00F6ffnen!"
    ),
    "baumarkt": (
        "\U0001F528 **Willkommen im Baumarkt!**\n"
        "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        "\u27A4 Alles rund ums Bauen, Reparieren und Ausstatten.\n"
        "\u27A4 Werkzeug, Materialien und Ausr\u00FCstung.\n"
        "\u27A4 Bezahlung nur mit **Bargeld** (\U0001F4B5).\n\n"
        "Klicke auf den Button um den Shop zu \u00F6ffnen!"
    ),
    "schwarzmarkt": (
        "\U0001F575\uFE0F **Willkommen auf dem Schwarzmarkt.**\n"
        "\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\u2015\n"
        "\u27A4 Hier gibt es Dinge, die man \u00F6ffentlich nicht findet.\n"
        "\u27A4 Zugang nur f\u00FCr autorisierte Personen.\n"
        "\u27A4 Bezahlung nur mit **Bargeld** (\U0001F4B5).\n\n"
        "Klicke auf den Button wenn du Zugang hast."
    ),
}


class ShopChannelButton(discord.ui.Button):
    def __init__(self, shop_key: str):
        cfg = SHOPS[shop_key]
        labels = {
            "kwik":         "\U0001F3EA Shop \u00F6ffnen",
            "baumarkt":     "\U0001F528 Shop \u00F6ffnen",
            "schwarzmarkt": "\U0001F575\uFE0F Shop \u00F6ffnen",
        }
        styles = {
            "kwik":         discord.ButtonStyle.primary,
            "baumarkt":     discord.ButtonStyle.primary,
            "schwarzmarkt": discord.ButtonStyle.danger,
        }
        super().__init__(
            label=labels[shop_key],
            style=styles[shop_key],
            custom_id=f"shop_open_{shop_key}",
        )
        self.shop_key = shop_key

    async def callback(self, interaction: discord.Interaction):
        shop_key = self.shop_key

        if shop_key == "schwarzmarkt" and not _has_schwarzmarkt_access(interaction.user):
            await interaction.response.send_message(
                "\u274C Du hast keinen Zugang zum **Schwarzmarkt**.",
                ephemeral=True
            )
            return

        if not has_citizen_or_wage(interaction.user):
            await interaction.response.send_message(
                "\u274C Du ben\u00F6tigst eine g\u00FCltige Rolle um hier einkaufen zu k\u00F6nnen.",
                ephemeral=True
            )
            return

        embed, total_pages = _build_shop_embed(shop_key, interaction.user, page=0)
        view = ShopPageView(shop_key, interaction.user, page=0, total_pages=total_pages)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ShopKwikChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopChannelButton("kwik"))


class ShopBaumarktChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopChannelButton("baumarkt"))


class ShopSchwarzmarktChannelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopChannelButton("schwarzmarkt"))


_CHANNEL_VIEWS = {
    "kwik":         ShopKwikChannelView,
    "baumarkt":     ShopBaumarktChannelView,
    "schwarzmarkt": ShopSchwarzmarktChannelView,
}


def _build_channel_embed(shop_key: str) -> discord.Embed:
    # Items dynamisch aus JSON laden (wie im Angler-Shop)
    all_items = load_shop()
    items     = [i for i in all_items if _item_shop(i) == shop_key]
    sep       = "\u2015" * 22

    if items:
        lines = []
        for it in items:
            role_hint = ""
            if it.get("allowed_role"):
                role_hint = " \U0001F512"
            lines.append(
                f"\u27A4 **{it['name']}**\u3000\u2014\u3000`{it.get('price', 0):,} \U0001F4B5`{role_hint}"
            )
        item_block = "\n".join(lines)
    else:
        item_block = "*Dieser Shop ist aktuell leer.*"

    description = (
        f"{_SHOP_BANNERS[shop_key]}\n"
        f"{sep}\n"
        f"{item_block}\n"
        f"{sep}"
    )

    embed = discord.Embed(
        title=SHOPS[shop_key]["label"],
        description=description,
        color=_SHOP_COLORS[shop_key],
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Paradise City Roleplay \u2014 Shop")
    return embed


# \u2500\u2500 Auto-Setup (wird von embed_manager aufgerufen) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

_SHOP_MSG_FILE = DATA_DIR / "shop_msg_ids.json"


def _load_shop_msg_ids() -> dict:
    if _SHOP_MSG_FILE.exists():
        try:
            return json.load(open(_SHOP_MSG_FILE))
        except Exception:
            pass
    return {}


def _save_shop_msg_ids(ids: dict):
    with open(_SHOP_MSG_FILE, "w") as f:
        json.dump(ids, f)


async def auto_shop_setup():
    msg_ids = _load_shop_msg_ids()

    for guild in bot.guilds:
        for shop_key, cfg in SHOPS.items():
            channel = guild.get_channel(cfg["channel"])
            if not channel:
                continue

            embed = _build_channel_embed(shop_key)
            view  = _CHANNEL_VIEWS[shop_key]()
            mid   = msg_ids.get(shop_key)

            if mid:
                try:
                    msg = await channel.fetch_message(int(mid))
                    await msg.edit(embed=embed, view=view)
                    print(f"[shop] Embed aktualisiert: {shop_key} in #{channel.name}")
                    continue
                except Exception:
                    pass

            try:
                new_msg = await channel.send(embed=embed, view=view)
                msg_ids[shop_key] = new_msg.id
                _save_shop_msg_ids(msg_ids)
                print(f"[shop] Embed gepostet: {shop_key} in #{channel.name}")
            except Exception as e:
                print(f"[shop] \u274C Fehler beim Posten ({shop_key}): {e}")


async def refresh_all_shop_embeds():
    """Aktualisiert ALLE Shop-Embeds (Kwik/Baumarkt/Schwarzmarkt + Angler)
    nach einer Item-\u00C4nderung. Wird nach /shop-add, /shop-edit, /delete-item
    aufgerufen damit \u00C4nderungen sofort in Discord sichtbar sind."""
    try:
        await auto_shop_setup()
    except Exception as _e:
        print(f"[shop] auto_shop_setup fehlgeschlagen: {_e}")
    # Angler-Shop separat refreshen (eigener Channel + eigene Logik)
    try:
        from angeln import _angler_shop_setup
        result = await _angler_shop_setup()
        print(f"[shop] Angler-Shop Embed: {result}")
    except Exception as _e:
        print(f"[shop] _angler_shop_setup fehlgeschlagen: {_e}")




# \u2500\u2500 /shop-add \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class ShopAddConfirmView(TimedDisableView):
    def __init__(self, name: str, price: int, shop_key: str, allowed_role_id=None):
        super().__init__(timeout=INTERACTION_VIEW_TIMEOUT)
        self.name            = name
        self.price           = price
        self.shop_key        = shop_key
        self.allowed_role_id = allowed_role_id

    @discord.ui.button(label="\u2705 Best\u00E4tigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Je nach Shop-Typ in die richtige JSON-Datei schreiben
        if self.shop_key in {"kwik", "baumarkt", "schwarzmarkt"}:
            items = load_shop()
            entry = {"name": self.name, "price": self.price, "shop": self.shop_key}
            if self.allowed_role_id:
                entry["allowed_role"] = self.allowed_role_id
            items.append(entry)
            save_shop(items)
            shop_label = SHOPS[self.shop_key]["label"]
        elif self.shop_key == "team":
            items = load_team_shop()
            items.append({"name": self.name})
            save_team_shop(items)
            shop_label = "\U0001F4E6 Team-Shop"
        elif self.shop_key == "angler":
            items = load_angler_shop()
            items.append({"name": self.name, "price": self.price})
            save_angler_shop(items)
            shop_label = "\U0001F3A3 Angler-Shop"
        else:
            try:
                await interaction.response.send_message(
                    f"\u274C Unbekannter Shop: `{self.shop_key}`", ephemeral=True
                )
            except Exception:
                pass
            return

        # Alle Buttons deaktivieren
        for child in self.children:
            child.disabled = True

        # Rolle-Info + Preis-Info
        rolle_info = ""
        if self.allowed_role_id and self.shop_key in {"kwik", "baumarkt", "schwarzmarkt"}:
            r = interaction.guild.get_role(self.allowed_role_id)
            rolle_info = f"\n**Nur f\u00FCr:** {r.mention if r else self.allowed_role_id}"
        price_info = f"**{self.price:,} \U0001F4B5**" if self.shop_key != "team" else "(Team-Shop)"

        # SOFORT auf den Button antworten (<3s) \u2014 verhindert 'Interaktion fehlgeschlagen'
        confirmation_embed = discord.Embed(
            title="\u2705 Item hinzugef\u00FCgt",
            description=(
                f"**{self.name}** f\u00FCr {price_info} wurde zum "
                f"**{shop_label}** hinzugef\u00FCgt.{rolle_info}\n\n"
                "\u23F3 Shop-Embeds werden im Hintergrund aktualisiert\u2026"
            ),
            color=LOG_COLOR
        )
        try:
            await interaction.response.edit_message(embed=confirmation_embed, view=self)
        except Exception as _e:
            # Fallback falls edit_message fehlschl\u00E4gt
            try:
                await interaction.response.send_message(embed=confirmation_embed, ephemeral=True)
            except Exception:
                print(f"[shop] Confirm-Antwort fehlgeschlagen: {_e}")

        # Jetzt im Hintergrund Shop-Embeds aktualisieren (kann 2-5s dauern)
        try:
            await refresh_all_shop_embeds()
        except Exception as _e:
            print(f"[shop] refresh_all_shop_embeds nach /shop-add fehlgeschlagen: {_e}")

    @discord.ui.button(label="\u274C Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="\u274C Abgebrochen",
                description="Das Item wurde nicht hinzugef\u00FCgt.",
                color=MOD_COLOR
            ),
            view=self
        )


# \u2500\u2500 /shop-add \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="shop-add",
    description="[Shop] F\u00FCge ein neues Item zu einem Shop hinzu (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    itemname="Name des Items",
    preis="Preis in $ (im Team-Shop ignoriert)",
    shop="In welchem Shop soll das Item angelegt werden?",
    rolle="(Optional) Nur diese Rolle kann das Item kaufen (nur Haupt-Shops)"
)
@app_commands.choices(shop=[
    app_commands.Choice(name="\U0001F3EA Kwik-E-Markt",       value="kwik"),
    app_commands.Choice(name="\U0001F528 Baumarkt",            value="baumarkt"),
    app_commands.Choice(name="\U0001F575\uFE0F Schwarzmarkt",  value="schwarzmarkt"),
    app_commands.Choice(name="\U0001F4E6 Team-Shop",          value="team"),
    app_commands.Choice(name="\U0001F3A3 Angler-Shop",        value="angler"),
])
async def shop_add(
    interaction: discord.Interaction,
    itemname: str,
    preis: int,
    shop: str,
    rolle: discord.Role = None
):
    if not _is_shop_admin(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return
    if preis <= 0 and shop != "team":
        await interaction.response.send_message("\u274C Preis muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
        return

    SHOP_LABELS_ADD = {
        "kwik":         SHOPS["kwik"]["label"],
        "baumarkt":     SHOPS["baumarkt"]["label"],
        "schwarzmarkt": SHOPS["schwarzmarkt"]["label"],
        "team":         "\U0001F4E6 Team-Shop",
        "angler":       "\U0001F3A3 Angler-Shop",
    }
    shop_label = SHOP_LABELS_ADD[shop]

    # Team-Shop hat keinen Preis, keine Rollenbeschr\u00E4nkung
    if shop == "team":
        price_line = "**Preis:** (Team-Shop \u2014 ignoriert)\n"
        rolle_info = ""
        rolle      = None
    else:
        price_line = f"**Preis:** {preis:,} \U0001F4B5\n"
        rolle_info = f"\n**Nur f\u00FCr:** {rolle.mention}" if rolle else "\n**Rollenbeschr\u00E4nkung:** Keine"
        # Angler-Shop unterst\u00FCtzt keine Rollenbeschr\u00E4nkung
        if shop == "angler" and rolle:
            rolle_info = "\n**Hinweis:** Rollenbeschr\u00E4nkung wird im Angler-Shop ignoriert."
            rolle      = None

    embed = discord.Embed(
        title="\U0001F6D2 Neues Item hinzuf\u00FCgen?",
        description=(
            f"**Name:** {itemname}\n"
            f"{price_line}"
            f"**Shop:** {shop_label}"
            f"{rolle_info}\n\n"
            "Bitte best\u00E4tige das Hinzuf\u00FCgen."
        ),
        color=LOG_COLOR
    )
    await interaction.response.send_message(
        embed=embed,
        view=ShopAddConfirmView(itemname, preis, shop, rolle.id if rolle else None),
        ephemeral=True
    )


# \u2500\u2500 /shop-edit \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="shop-edit",
    description="[Shop] Bearbeite ein bestehendes Item (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    itemname="Name des Items das bearbeitet werden soll",
    neuer_preis="Neuer Preis in $ (leer lassen um nicht zu \u00E4ndern)",
    neuer_name="Neuer Name des Items (leer lassen um nicht zu \u00E4ndern)",
    shop="In welchem Shop soll das Item sein? (leer lassen um nicht zu \u00E4ndern)"
)
@app_commands.choices(
    shop=[
        app_commands.Choice(name="\U0001F3EA Kwik-E-Markt",      value="kwik"),
        app_commands.Choice(name="\U0001F528 Baumarkt",          value="baumarkt"),
        app_commands.Choice(name="\U0001F575\uFE0F Schwarzmarkt", value="schwarzmarkt"),
        app_commands.Choice(name="\U0001F4E6 Team-Shop",         value="team"),
        app_commands.Choice(name="\U0001F3A3 Angler-Shop",       value="angler"),
    ]
)
@app_commands.autocomplete(itemname=all_shops_item_autocomplete)
async def shop_edit(
    interaction: discord.Interaction,
    itemname: str,
    neuer_preis: int = None,
    neuer_name: str = None,
    shop: app_commands.Choice[str] = None
):
    if not _is_shop_admin(interaction.user):
        await interaction.response.send_message("\u274C Kein Zugriff.", ephemeral=True)
        return

    if neuer_preis is None and neuer_name is None and shop is None:
        await interaction.response.send_message(
            "\u274C Bitte gib einen neuen Preis, Namen oder Shop an.", ephemeral=True
        )
        return

    # Defer damit Discord nicht timeoutet (auto_shop_setup braucht >3s)
    await interaction.response.defer(ephemeral=True)

    # \u2500\u2500 Item in allen Shops finden \u2500\u2500
    MAIN_KEYS = {"kwik", "baumarkt", "schwarzmarkt"}

    items       = load_shop()
    shop_item   = find_shop_item(items, itemname)
    source_type = "main" if shop_item else None
    source_items = items if shop_item else None
    source_save  = save_shop if shop_item else None

    if not shop_item:
        team_items = load_team_shop()
        shop_item  = find_shop_item(team_items, itemname)
        if shop_item:
            source_type  = "team"
            source_items = team_items
            source_save  = save_team_shop

    if not shop_item:
        angler_items = load_angler_shop()
        shop_item    = find_shop_item(angler_items, itemname)
        if shop_item:
            source_type  = "angler"
            source_items = angler_items
            source_save  = save_angler_shop

    if not shop_item:
        await interaction.followup.send(
            f"\u274C Item **{itemname}** wurde nicht gefunden.", ephemeral=True
        )
        return

    # Aktueller Shop-Schl\u00FCssel (f\u00FCr Vergleich)
    if source_type == "main":
        current_shop_key = shop_item.get("shop", "kwik")
    elif source_type == "team":
        current_shop_key = "team"
    else:
        current_shop_key = "angler"

    changes = []

    # \u2500\u2500 Preis \u00E4ndern \u2500\u2500
    if neuer_preis is not None:
        if neuer_preis <= 0:
            await interaction.followup.send("\u274C Preis muss gr\u00F6\u00DFer als 0 sein.", ephemeral=True)
            return
        old_price          = shop_item.get("price", 0)
        shop_item["price"] = neuer_preis
        changes.append(f"**Preis:** {old_price:,} \U0001F4B5 \u2192 {neuer_preis:,} \U0001F4B5")

    # \u2500\u2500 Name \u00E4ndern (inkl. Inventar-Rename) \u2500\u2500
    if neuer_name:
        old_name          = shop_item["name"]
        shop_item["name"] = neuer_name
        eco = load_economy()
        for uid, udata in eco.items():
            udata["inventory"] = [
                neuer_name if i == old_name else i
                for i in udata.get("inventory", [])
            ]
        save_economy(eco)
        changes.append(f"**Name:** {old_name} \u2192 {neuer_name}")

    # \u2500\u2500 Shop-Wechsel (unterst\u00FCtzt Cross-Shop-Moves) \u2500\u2500
    shop_label_map = {
        "kwik":         "\U0001F3EA Kwik-E-Markt",
        "baumarkt":     "\U0001F528 Baumarkt",
        "schwarzmarkt": "\U0001F575\uFE0F Schwarzmarkt",
        "team":         "\U0001F4E6 Team-Shop",
        "angler":       "\U0001F3A3 Angler-Shop",
    }

    if shop is not None and shop.value != current_shop_key:
        target_key = shop.value
        old_label  = shop_label_map.get(current_shop_key, current_shop_key)
        new_label  = shop_label_map.get(target_key, target_key)

        # Aus Quell-Shop entfernen
        source_items.remove(shop_item)
        source_save(source_items)

        # In Ziel-Shop einf\u00FCgen
        if target_key in MAIN_KEYS:
            shop_item["shop"] = target_key
            target_items = load_shop() if source_type != "main" else source_items
            # Wenn source_type == "main", wurde schon aus der Liste entfernt, gleiche Liste nutzen
            if source_type != "main":
                target_items.append(shop_item)
                save_shop(target_items)
            else:
                source_items.append(shop_item)
                save_shop(source_items)
        elif target_key == "team":
            # Team-Shop-Format: nur name (ohne price/shop)
            team_entry = {"name": shop_item["name"]}
            target_items = load_team_shop()
            target_items.append(team_entry)
            save_team_shop(target_items)
        elif target_key == "angler":
            angler_entry = {"name": shop_item["name"], "price": shop_item.get("price", 0)}
            target_items = load_angler_shop()
            target_items.append(angler_entry)
            save_angler_shop(target_items)

        changes.append(f"**Shop:** {old_label} \u2192 {new_label}")
    else:
        # Kein Shop-Wechsel \u2014 nur Source-File speichern (Preis/Name-\u00C4nderungen)
        source_save(source_items)

    # \u2500\u2500 Discord-Shop-Embeds sofort aktualisieren (inkl. Angler-Shop) \u2500\u2500
    await refresh_all_shop_embeds()

    embed = discord.Embed(
        title="\u270F\uFE0F Item bearbeitet",
        description="\n".join(changes),
        color=LOG_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text=f"Bearbeitet von {interaction.user}")
    await interaction.followup.send(embed=embed, ephemeral=True)


# \u2500\u2500 /delete-item \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@bot.tree.command(
    name="delete-item",
    description="[Shop] Entfernt ein Item aus dem Shop (Admin)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(itemname="Name des Items das entfernt werden soll")
@app_commands.autocomplete(itemname=all_shops_item_autocomplete)
async def delete_item(interaction: discord.Interaction, itemname: str):
    if not _is_shop_admin(interaction.user):
        await interaction.response.send_message("\u274C Keine Berechtigung.", ephemeral=True)
        return

    # Defer damit Discord nicht timeoutet (auto_shop_setup braucht >3s)
    await interaction.response.defer(ephemeral=True)

    items      = load_shop()
    shop_item  = find_shop_item(items, itemname)
    _save_fn   = save_shop
    shop_label = None

    if not shop_item:
        team_items = load_team_shop()
        shop_item  = find_shop_item(team_items, itemname)
        if shop_item:
            items      = team_items
            _save_fn   = save_team_shop
            shop_label = "Team Shop"

    if not shop_item:
        angler_items = load_angler_shop()
        shop_item    = find_shop_item(angler_items, itemname)
        if shop_item:
            items      = angler_items
            _save_fn   = save_angler_shop
            shop_label = "Angler Shop"

    if not shop_item:
        await interaction.followup.send(
            f"\u274C Das Item **{itemname}** wurde nicht gefunden.", ephemeral=True
        )
        return

    if shop_label is None:
        shop_label = SHOPS.get(_item_shop(shop_item), SHOPS["kwik"])["label"]

    items.remove(shop_item)
    _save_fn(items)

    # Discord-Shop-Embeds sofort aktualisieren (inkl. Angler-Shop)
    await refresh_all_shop_embeds()

    item_name       = shop_item["name"]
    eco             = load_economy()
    players_cleaned = 0
    total_removed   = 0
    for uid, user_data in eco.items():
        inv    = user_data.get("inventory", [])
        before = len(inv)
        user_data["inventory"] = [i for i in inv if i != item_name]
        removed = before - len(user_data["inventory"])
        if removed > 0:
            players_cleaned += 1
            total_removed   += removed
    save_economy(eco)

    embed = discord.Embed(
        title="\U0001F5D1\uFE0F Item aus Shop entfernt",
        description=(
            f"**Item:** {item_name}\n"
            f"**Shop:** {shop_label}\n"
            f"**Preis war:** {shop_item.get('price', 0):,} \U0001F4B5\n"
            f"**Entfernt von:** {interaction.user.mention}\n\n"
            f"**Inventare bereinigt:** {players_cleaned} Spieler\n"
            f"**Items entfernt:** {total_removed}\u00D7"
        ),
        color=MOD_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
