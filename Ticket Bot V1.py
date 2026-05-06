"""
╔══════════════════════════════════════════════════════╗
║         TICKET BOT — Système de notation staff        ║
╚══════════════════════════════════════════════════════╝

INSTALLATION :
    pip install discord.py

CONFIGURATION :
    Modifie les variables ci-dessous avant de lancer le bot.
"""

import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
from datetime import datetime

# ══════════════════════════════════════════════
#  CONFIGURATION — À MODIFIER
# ══════════════════════════════════════════════

BOT_TOKEN         = "TON_TOKEN_ICI"
STAFF_ROLE_ID     = 123456789012345678   # ID du rôle staff
TICKET_CATEGORY   = "Tickets"            # Nom de la catégorie Discord des tickets
LOG_CHANNEL_ID    = 123456789012345678   # ID du salon staff qui reçoit les notes

# ══════════════════════════════════════════════
#  MODAL — Commentaire après la note
# ══════════════════════════════════════════════

class CommentModal(Modal, title="Laisser un commentaire"):
    commentaire = TextInput(
        label="Votre commentaire",
        placeholder="Décrivez votre expérience avec le staff...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )

    def __init__(self, note: int, ticket_name: str, staff: discord.Member, owner: discord.Member):
        super().__init__()
        self.note        = note
        self.ticket_name = ticket_name
        self.staff       = staff
        self.owner       = owner

    async def on_submit(self, interaction: discord.Interaction):
        await send_log(
            interaction=interaction,
            note=self.note,
            commentaire=self.commentaire.value.strip(),
            ticket_name=self.ticket_name,
            staff=self.staff,
            owner=self.owner,
        )


# ══════════════════════════════════════════════
#  VUE — Boutons commentaire
# ══════════════════════════════════════════════

class AfterRatingView(View):
    def __init__(self, note: int, ticket_name: str, staff: discord.Member, owner: discord.Member):
        super().__init__(timeout=120)
        self.note        = note
        self.ticket_name = ticket_name
        self.staff       = staff
        self.owner       = owner

    @discord.ui.button(label="Ajouter un commentaire", style=discord.ButtonStyle.secondary, emoji="💬")
    async def with_comment(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            CommentModal(self.note, self.ticket_name, self.staff, self.owner)
        )

    @discord.ui.button(label="Envoyer sans commentaire", style=discord.ButtonStyle.success, emoji="✅")
    async def without_comment(self, interaction: discord.Interaction, button: Button):
        await send_log(
            interaction=interaction,
            note=self.note,
            commentaire=None,
            ticket_name=self.ticket_name,
            staff=self.staff,
            owner=self.owner,
        )


# ══════════════════════════════════════════════
#  VUE — Sélection de la note (boutons étoiles)
# ══════════════════════════════════════════════

class RatingView(View):
    def __init__(self, ticket_name: str, staff: discord.Member, owner: discord.Member):
        super().__init__(timeout=300)
        self.ticket_name = ticket_name
        self.staff       = staff
        self.owner       = owner

        STARS = [
            ("😡  1 / 5", discord.ButtonStyle.danger,    1),
            ("😕  2 / 5", discord.ButtonStyle.danger,    2),
            ("😐  3 / 5", discord.ButtonStyle.secondary, 3),
            ("😊  4 / 5", discord.ButtonStyle.success,   4),
            ("🤩  5 / 5", discord.ButtonStyle.success,   5),
        ]
        for label, style, note in STARS:
            btn = Button(label=label, style=style)
            btn.callback = self._make_cb(note)
            self.add_item(btn)

    def _make_cb(self, note: int):
        async def callback(interaction: discord.Interaction):
            for item in self.children:
                item.disabled = True

            stars    = "⭐" * note + "☆" * (5 - note)
            emojis   = {1: "😡", 2: "😕", 3: "😐", 4: "😊", 5: "🤩"}
            couleurs = {1: 0xED4245, 2: 0xFEE75C, 3: 0x95A5A6, 4: 0x57F287, 5: 0x57F287}

            embed = discord.Embed(
                description=f"Tu as choisi **{stars}** ({note}/5) {emojis[note]}\nVeux-tu ajouter un commentaire ?",
                color=couleurs[note],
            )
            await interaction.response.edit_message(embed=embed, view=self)

            after_view = AfterRatingView(note, self.ticket_name, self.staff, self.owner)
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Souhaites-tu laisser un commentaire ?",
                    color=couleurs[note],
                ),
                view=after_view,
                ephemeral=True,
            )
        return callback


# ══════════════════════════════════════════════
#  ENVOI DE LA NOTES DANS LE SALON STAFF
# ══════════════════════════════════════════════

async def send_log(
    interaction: discord.Interaction,
    note: int,
    commentaire,
    ticket_name: str,
    staff: discord.Member,
    owner: discord.Member,
):
    stars    = "⭐" * note + "☆" * (5 - note)
    emojis   = {1: "😡", 2: "😕", 3: "😐", 4: "😊", 5: "🤩"}
    couleurs = {1: 0xED4245, 2: 0xFEE75C, 3: 0x95A5A6, 4: 0x57F287, 5: 0x57F287}
    verdicts = {
        1: "Très mauvaise expérience",
        2: "Mauvaise expérience",
        3: "Expérience neutre",
        4: "Bonne expérience",
        5: "Excellente expérience !",
    }

    embed = discord.Embed(
        title=f"{emojis[note]}  Avis ticket — {ticket_name}",
        description=f"**{verdicts[note]}**  •  {stars}  ({note}/5)",
        color=couleurs[note],
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="👤  Utilisateur",  value=f"{owner.mention}\n`{owner.name}`",           inline=True)
    embed.add_field(name="🛡️  Staff",        value=f"{staff.mention}\n`{staff.name}`" if staff else "Inconnu", inline=True)
    embed.add_field(name="⭐  Note",         value=f"**{note} / 5**",                             inline=True)
    embed.add_field(
        name="💬  Commentaire",
        value=f"> {commentaire}" if commentaire else "*Aucun commentaire laissé.*",
        inline=False,
    )
    embed.set_thumbnail(url=owner.display_avatar.url)
    embed.set_footer(
        text=f"ID utilisateur : {owner.id}",
        icon_url=staff.display_avatar.url if staff else None,
    )

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)

    confirm = discord.Embed(
        description=f"✅ Merci pour ton retour ! Ta note **{note}/5** a bien été enregistrée.",
        color=couleurs[note],
    )
    await interaction.response.send_message(embed=confirm, ephemeral=True)


# ══════════════════════════════════════════════
#  MESSAGE DM DE NOTATION ENVOYÉ À L'USER
# ══════════════════════════════════════════════

async def send_rating_dm(
    owner: discord.Member,
    staff: discord.Member,
    ticket_name: str,
    channel: discord.TextChannel,
):
    view = RatingView(ticket_name=ticket_name, staff=staff, owner=owner)

    embed = discord.Embed(
        title="🎫  Votre ticket a été fermé",
        description=(
            f"Ton ticket **`{ticket_name}`** a été fermé par **{staff.display_name}**.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Tu as aimé le support reçu ?**\n"
            "Prends quelques secondes pour noter le staff 🙏\n\n"
            "Clique sur une note ci-dessous ⬇️"
        ),
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    embed.set_thumbnail(url=staff.display_avatar.url)
    embed.set_footer(text="Ta note aide à améliorer la qualité du support.")

    try:
        await owner.send(embed=embed, view=view)
        return True
    except discord.Forbidden:
        fallback = discord.Embed(
            title="⚠️  Tes DMs sont désactivés",
            description=(
                f"{owner.mention}, note le staff ici avant la fermeture du ticket :"
            ),
            color=0xFEE75C,
        )
        await channel.send(embed=fallback, view=view)
        return False


# ══════════════════════════════════════════════
#  VUE — Bouton fermeture dans le ticket
# ══════════════════════════════════════════════

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fermer le ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="persistent_close_ticket",
    )
    async def close(self, interaction: discord.Interaction, button: Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        is_staff   = staff_role in interaction.user.roles if staff_role else False

        if not is_staff:
            await interaction.response.send_message(
                "❌ Seul le **staff** peut fermer un ticket.", ephemeral=True
            )
            return

        channel    = interaction.channel
        staff_user = interaction.user

        # Trouver l'owner du ticket
        ticket_owner = None
        async for msg in channel.history(oldest_first=True, limit=30):
            if not msg.author.bot:
                sr = channel.guild.get_role(STAFF_ROLE_ID)
                if sr not in msg.author.roles:
                    ticket_owner = msg.author
                    break

        button.disabled = True
        button.label    = "Ticket fermé"

        closing_embed = discord.Embed(
            title="🔒  Ticket fermé",
            description=(
                f"Ce ticket a été fermé par {staff_user.mention}.\n"
                f"Un message de notation a été envoyé à {ticket_owner.mention if ticket_owner else 'l\'utilisateur'}.\n\n"
                "**Le salon sera supprimé dans 10 secondes.**"
            ),
            color=0xED4245,
            timestamp=datetime.utcnow(),
        )
        await interaction.response.edit_message(view=self)
        await channel.send(embed=closing_embed)

        if ticket_owner:
            await send_rating_dm(
                owner=ticket_owner,
                staff=staff_user,
                ticket_name=channel.name,
                channel=channel,
            )

        await asyncio.sleep(10)
        await channel.delete(reason=f"Ticket fermé par {staff_user}")


# ══════════════════════════════════════════════
#  COMMANDES
# ══════════════════════════════════════════════

@bot.command(name="ticket")
async def create_ticket(ctx: commands.Context):
    """Crée un nouveau salon de ticket."""
    guild    = ctx.guild
    category = discord.utils.get(guild.categories, name=TICKET_CATEGORY)

    if not category:
        category = await guild.create_category(TICKET_CATEGORY)

    staff_role = guild.get_role(STAFF_ROLE_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author:         discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel = await guild.create_text_channel(
        name=f"ticket-{ctx.author.name}",
        category=category,
        overwrites=overwrites,
    )

    embed = discord.Embed(
        title="🎫  Nouveau Ticket",
        description=(
            f"Bienvenue {ctx.author.mention} !\n\n"
            "Le staff va vous répondre dès que possible.\n"
            "Décrivez votre problème en détail ci-dessous.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Lorsque votre problème est résolu, le staff fermera le ticket\n"
            "et vous recevrez un message pour noter notre support 🙏"
        ),
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=f"Ticket de {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await channel.send(embed=embed, view=TicketCloseView())
    await ctx.message.delete()

    try:
        await ctx.author.send(
            embed=discord.Embed(
                description=f"✅ Ton ticket a été créé : {channel.mention}",
                color=0x57F287,
            )
        )
    except discord.Forbidden:
        pass


@bot.command(name="fermer")
async def fermer_ticket(ctx: commands.Context):
    """Ferme manuellement un ticket (staff uniquement)."""
    staff_role = ctx.guild.get_role(STAFF_ROLE_ID)
    if not staff_role or staff_role not in ctx.author.roles:
        await ctx.send("❌ Seul le **staff** peut utiliser cette commande.")
        return

    channel    = ctx.channel
    staff_user = ctx.author

    ticket_owner = None
    async for msg in channel.history(oldest_first=True, limit=30):
        if not msg.author.bot and staff_role not in msg.author.roles:
            ticket_owner = msg.author
            break

    closing_embed = discord.Embed(
        title="🔒  Ticket fermé",
        description=(
            f"Ticket fermé par {staff_user.mention}.\n"
            "**Suppression dans 10 secondes.**"
        ),
        color=0xED4245,
        timestamp=datetime.utcnow(),
    )
    await ctx.send(embed=closing_embed)

    if ticket_owner:
        await send_rating_dm(
            owner=ticket_owner,
            staff=staff_user,
            ticket_name=channel.name,
            channel=channel,
        )

    await asyncio.sleep(10)
    await channel.delete(reason=f"Ticket fermé par {staff_user}")


# ══════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════

@bot.event
async def on_ready():
    bot.add_view(TicketCloseView())
    print(f"Bot connecté : {bot.user}  (ID: {bot.user.id})")
    print(f"Serveurs     : {len(bot.guilds)}")
    print(f"Salon logs   : {LOG_CHANNEL_ID}")


# ══════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════

bot.run(BOT_TOKEN)
