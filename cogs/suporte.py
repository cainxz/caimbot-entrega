# cogs/suporte.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import json
import os
import re

CONFIG_FILE = "config.json"

# ---------------- CONFIG ----------------
def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def set_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- BOTÕES DE TICKET ----------------
class TicketButtons(discord.ui.View):
    def __init__(self, user: discord.Member, bot: commands.Bot):
        super().__init__(timeout=None)
        self.user = user
        self.bot = bot

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Você não pode fechar este ticket.", ephemeral=True)
            return
        await interaction.response.send_message("Ticket fechado.", ephemeral=True)
        await interaction.channel.delete()

    @discord.ui.button(label="Notificar Moderação", style=discord.ButtonStyle.green)
    async def notificar(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_config()
        mod_channel_id = config.get("mod_channel_id")
        mod_channel = interaction.guild.get_channel(mod_channel_id) if mod_channel_id else None
        if mod_channel:
            embed = discord.Embed(
                title="⚠️ Ticket Ativo",
                description=f"Usuário: {self.user.mention}\nCanal: {interaction.channel.mention}",
                color=discord.Color.orange()
            )
            await mod_channel.send(embed=embed)
            await interaction.response.send_message("Moderação notificada.", ephemeral=True)
        else:
            await interaction.response.send_message("Canal de moderação não configurado. Use `/set_mod_channel`.", ephemeral=True)

# ---------------- MODAIS DE TICKET ----------------
class ReportarModal(Modal):
    def __init__(self, bot: commands.Bot, tipo: str):
        super().__init__(title="Abrir Ticket")
        self.bot = bot
        self.tipo = tipo

        if tipo in ["reportar", "reporte"]:
            self.usuario = TextInput(label="Usuário a reportar (nome#tag)", placeholder="Ex: Jogador#1234", required=True)
            self.motivo = TextInput(label="Motivo ou evidências", style=discord.TextStyle.paragraph, required=True)
            self.add_item(self.usuario)
            self.add_item(self.motivo)
        elif tipo == "ticket":
            self.assunto = TextInput(label="Assunto do ticket", style=discord.TextStyle.paragraph, required=True)
            self.add_item(self.assunto)
        elif tipo == "tag":
            self.tag = TextInput(label="Tag desejada", required=True)
            self.motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True)
            self.add_item(self.tag)
            self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category_name = "Tickets"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        nome_limpo = re.sub(r"[^a-zA-Z0-9_-]", "", interaction.user.name)
        canal_nome = f"{self.tipo}-{nome_limpo}-{interaction.user.id}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        ticket_channel = await guild.create_text_channel(canal_nome, category=category, overwrites=overwrites)

        embed = discord.Embed(title=f"🛠 {self.tipo.capitalize()} Ticket", color=discord.Color.blue())
        if self.tipo in ["reportar", "reporte"]:
            embed.description = f"Usuário: {self.usuario.value}\nMotivo/Evidências: {self.motivo.value}"
        elif self.tipo == "ticket":
            embed.description = f"Assunto: {self.assunto.value}"
        elif self.tipo == "tag":
            embed.description = f"Tag solicitada: {self.tag.value}\nMotivo: {self.motivo.value}"
        embed.set_footer(text=f"Ticket criado por {interaction.user}")

        view = TicketButtons(interaction.user, self.bot)
        await ticket_channel.send(embed=embed, view=view)

        # ------------------- ENVIO PARA LOGS DO SUPORTE -------------------
        try:
            logs_cog = self.bot.get_cog("LogsSuporte")
            if logs_cog:
                await logs_cog.send_suporte_log(guild.id, mensagem=f"Novo ticket criado: {ticket_channel.mention}", embed=embed)
        except Exception as e:
            print(f"Erro ao enviar log de suporte: {e}")

        # Notifica moderação, se configurada
        config = get_config()
        mod_channel_id = config.get("mod_channel_id")
        mod_channel = guild.get_channel(mod_channel_id) if mod_channel_id else None
        if mod_channel:
            await mod_channel.send(embed=embed)

        await interaction.followup.send(f"Ticket criado: {ticket_channel.mention}", ephemeral=True)

# ---------------- BOTÕES PRINCIPAIS DE SUPORTE ----------------
class SuporteButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Reportar", style=discord.ButtonStyle.red)
    async def reportar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportarModal(self.bot, "reportar"))

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green)
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportarModal(self.bot, "ticket"))

    @discord.ui.button(label="Solicitar Tag", style=discord.ButtonStyle.blurple)
    async def tag(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportarModal(self.bot, "tag"))

# ---------------- COG DE SUPORTE ----------------
class Suporte(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Criação do canal principal de suporte
    @app_commands.command(name="suporte_create", description="Cria o canal principal de suporte com botões interativos.")
    @app_commands.checks.has_permissions(administrator=True)
    async def suporte_create(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        config = get_config()

        category_name = "Suporte"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        suporte_channel = discord.utils.get(guild.text_channels, name="suporte")
        if not suporte_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            suporte_channel = await guild.create_text_channel("suporte", category=category, overwrites=overwrites)
        else:
            await interaction.followup.send("O canal de suporte já existe!", ephemeral=True)
            return

        config["suporte_category_id"] = category.id
        config["suporte_channel_id"] = suporte_channel.id
        set_config(config)

        embed = discord.Embed(
            title="💬 Suporte",
            description="Clique nos botões abaixo para abrir o tipo de ticket desejado:",
            color=discord.Color.green()
        )
        view = SuporteButtons(self.bot)
        await suporte_channel.send(embed=embed, view=view)

        await interaction.followup.send(f"Canal de suporte criado: {suporte_channel.mention}", ephemeral=True)

# ---------------- SETUP ----------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Suporte(bot))
