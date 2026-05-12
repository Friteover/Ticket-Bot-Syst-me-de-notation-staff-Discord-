"""
╔══════════════════════════════════════════════════════╗
║         TICKET BOT — Système de notation staff        ║
║         (Notation via salon temporaire)               ║
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

BOT_TOKEN              = "TOKEN_ICI"
STAFF_ROLE_ID          = 1426275412014796953   # ID du rôle staff
TICKET_CATEGORY        = "Tickets"            # Nom de la catégorie Discord des tickets
LOG_CHANNEL_ID         = 1426275558957777109   # ID du salon staff qui reçoit les notes
RATING_CHANNEL_TIMEOUT = 120                  # Secondes avant suppression du salon de notation

# ══════════════════════════════════════════════
#  BOT
# ══════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


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

    def __init__(self, note: int, ticket_name: str, staff: discord.Member, owner: discord.Member, rating_channel: discord.TextChannel):
        super().__init__()
        self.note           = note
        self.ticket_name    = ticket_name
        self.staff          = staff
        self.owner          = owner
        self.rating_channel = rating_channel

    async def on_submit(self, interaction: discord.Interaction):
        await send_log(
            interaction=interaction,
            note=self.note,
            commentaire=self.commentaire.value.strip(),
            ticket_name=self.ticket_name,
            staff=self.staff,
            owner=self.owner,
        )
        # Supprime le salon de notation après l'envoi
        await asyncio.sleep(5)
        try:
            await self.rating_channel.delete(reason="Avis soumis")
        except discord.NotFound:
            pass


# ══════════════════════════════════════════════
#  VUE — Boutons commentaire
# ══════════════════════════════════════════════

class AfterRatingView(View):
    def __init__(self, note: int, ticket_name: str, staff: discord.Member, owner: discord.Member, rating_channel: discord.TextChannel):
        super().__init__(timeout=RATING_CHANNEL_TIMEOUT)
        self.note           = note
        self.ticket_name    = ticket_name
        self.staff          = staff
        self.owner          = owner
        self.rating_channel = rating_channel

    @discord.ui.button(label="Ajouter un commentaire", style=discord.ButtonStyle.secondary, emoji="💬")
    async def with_comment(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("❌ Ce salon de notation ne te concerne pas.", ephemeral=True)
            return
        await interaction.response.send_modal(
            CommentModal(self.note, self.ticket_name, self.staff, self.owner, self.rating_channel)
        )

    @discord.ui.button(label="Envoyer sans commentaire", style=discord.ButtonStyle.success, emoji="✅")
    async def without_comment(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("❌ Ce salon de notation ne te concerne pas.", ephemeral=True)
            return
        await send_log(
            interaction=interaction,
            note=self.note,
            commentaire=None,
            ticket_name=self.ticket_name,
            staff=self.staff,
            owner=self.owner,
        )
        await asyncio.sleep(5)
        try:
            await self.rating_channel.delete(reason="Avis soumis sans commentaire")
        except discord.NotFound:
            pass

    async def on_timeout(self):
        """Supprime le salon si aucune réponse après le délai."""
        try:
            await self.rating_channel.delete(reason="Délai de notation dépassé")
        except discord.NotFound:
            pass


# ══════════════════════════════════════════════
#  VUE — Sélection de la note (boutons étoiles)
# ══════════════════════════════════════════════

class RatingView(View):
    def __init__(self, ticket_name: str, staff: discord.Member, owner: discord.Member, rating_channel: discord.TextChannel):
        super().__init__(timeout=RATING_CHANNEL_TIMEOUT)
        self.ticket_name    = ticket_name
        self.staff          = staff
        self.owner          = owner
        self.rating_channel = rating_channel

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
            # Vérifie que c'est bien le propriétaire du ticket
            if interaction.user.id != self.owner.id:
                await interaction.response.send_message(
                    "❌ Ce salon de notation ne te concerne pas.", ephemeral=True
                )
                return

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

            after_view = AfterRatingView(note, self.ticket_name, self.staff, self.owner, self.rating_channel)
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Souhaites-tu laisser un commentaire ?",
                    color=couleurs[note],
                ),
                view=after_view,
            )
        return callback

    async def on_timeout(self):
        """Supprime le salon si aucune note après le délai."""
        try:
            await self.rating_channel.delete(reason="Délai de notation dépassé")
        except discord.NotFound:
            pass


# ══════════════════════════════════════════════
#  ENVOI DE LA NOTE DANS LE SALON STAFF (LOG)
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
    embed.add_field(name="👤  Utilisateur",  value=f"{owner.mention}\n`{owner.name}`",                                  inline=True)
    embed.add_field(name="🛡️  Staff",        value=f"{staff.mention}\n`{staff.name}`" if staff else "Inconnu",          inline=True)
    embed.add_field(name="⭐  Note",         value=f"**{note} / 5**",                                                   inline=True)
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
        description=f"✅ Merci pour ton retour ! Ta note **{note}/5** a bien été enregistrée.\n\nCe salon sera supprimé dans 5 secondes.",
        color=couleurs[note],
    )
    await interaction.response.send_message(embed=confirm)


# ══════════════════════════════════════════════
#  CRÉATION DU SALON DE NOTATION
# ══════════════════════════════════════════════

async def create_rating_channel(
    owner: discord.Member,
    staff: discord.Member,
    ticket_name: str,
    guild: discord.Guild,
):
    """
    Crée un salon temporaire visible uniquement par l'owner pour qu'il note le staff.
    Le salon est automatiquement supprimé après RATING_CHANNEL_TIMEOUT secondes
    ou dès que l'avis est soumis.
    """
    # Permissions : visible UNIQUEMENT par l'owner (personne d'autre ne peut voir)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        owner:              discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me:           discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    # Nom du salon : avis-<pseudo>
    channel_name = f"avis-{owner.name.lower().replace(' ', '-')}"

    rating_channel = await guild.create_text_channel(
        name=channel_name,
        category=None,
        overwrites=overwrites,
        topic=f"Notation du ticket {ticket_name} — fermé par {staff.display_name}",
    )

    # Envoie le message de notation dans le nouveau salon
    view = RatingView(
        ticket_name=ticket_name,
        staff=staff,
        owner=owner,
        rating_channel=rating_channel,
    )

    embed = discord.Embed(
        title="🎫  Votre ticket a été fermé",
        description=(
            f"Ton ticket **`{ticket_name}`** a été fermé par **{staff.display_name}**.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Tu as aimé le support reçu ?**\n"
            "Prends quelques secondes pour noter le staff 🙏\n\n"
            "Clique sur une note ci-dessous ⬇️\n\n"
            f"⏳ *Ce salon sera automatiquement supprimé dans **{RATING_CHANNEL_TIMEOUT // 60} minutes** si aucune réponse.*"
        ),
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    embed.set_thumbnail(url=staff.display_avatar.url)
    embed.set_footer(text="Ta note aide à améliorer la qualité du support.")

    await rating_channel.send(content=owner.mention, embed=embed, view=view)

    return rating_channel


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

        # Trouver l'owner du ticket (premier non-bot, non-staff à avoir écrit)
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
                + (
                    f"Un salon de notation a été créé pour {ticket_owner.mention}.\n"
                    if ticket_owner else ""
                )
                + "\n**Le salon sera supprimé dans 10 secondes.**"
            ),
            color=0xED4245,
            timestamp=datetime.utcnow(),
        )
        await interaction.response.edit_message(view=self)
        await channel.send(embed=closing_embed)

        # Crée le salon de notation pour l'owner
        if ticket_owner:
            await create_rating_channel(
                owner=ticket_owner,
                staff=staff_user,
                ticket_name=channel.name,
                guild=interaction.guild,
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
            "et un salon sera créé pour noter notre support 🙏"
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
            + (f"Salon de notation créé pour {ticket_owner.mention}.\n" if ticket_owner else "")
            + "**Suppression dans 10 secondes.**"
        ),
        color=0xED4245,
        timestamp=datetime.utcnow(),
    )
    await ctx.send(embed=closing_embed)

    # Crée le salon de notation pour l'owner
    if ticket_owner:
        await create_rating_channel(
            owner=ticket_owner,
            staff=staff_user,
            ticket_name=channel.name,
            guild=ctx.guild,
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
