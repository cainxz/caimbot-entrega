# cogs/moderacao.py
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import timedelta, datetime

CONFIG_FILE = "config.json"
WARNS_FILE = "warns.json"

# ---------------- CONFIG ----------------
def get_guild_config(guild_id):
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(str(guild_id), {})

def set_guild_config(guild_id, data):
    if not os.path.exists(CONFIG_FILE):
        full_data = {}
    else:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            full_data = json.load(f)
    full_data[str(guild_id)] = data
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)

# ---------------- WARNS ----------------
def get_warns():
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def set_warns(data):
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------------- COG ----------------
class Moderacao(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_message_times = {}
        self.tempbans = {}
        self.check_spam.start()

    # ---------------- LOG ----------------
    async def _log_action(self, interaction: discord.Interaction, title: str, fields: dict, color: discord.Color):
        config = get_guild_config(interaction.guild.id)
        log_channel_id = config.get("log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                icon_url = interaction.user.display_avatar.url
                embed = discord.Embed(title=f"Log: {title}", color=color)
                embed.set_author(name=f"Executado por: {interaction.user.display_name}", icon_url=icon_url)
                for name, value in fields.items():
                    embed.add_field(name=name, value=value, inline=False)
                embed.set_footer(text=f"ID do Moderador: {interaction.user.id}")
                await log_channel.send(embed=embed)

    # ---------------- COMANDOS ----------------
    @app_commands.command(name="setup_logs", description="Cria e configura o canal de logs deste servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_logs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        config = get_guild_config(interaction.guild.id)
        log_channel_id = config.get("log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await interaction.followup.send(f"Um canal de logs já existe: {log_channel.mention}", ephemeral=True)
                return
            else:
                config.pop("log_channel_id")
                set_guild_config(interaction.guild.id, config)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        try:
            log_channel = await interaction.guild.create_text_channel("caimbot-logs", overwrites=overwrites)
            config["log_channel_id"] = log_channel.id
            set_guild_config(interaction.guild.id, config)
            await interaction.followup.send(f"Canal de logs {log_channel.mention} criado com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Não foi possível criar o canal de logs. Erro: {e}", ephemeral=True)

    @app_commands.command(name="set_mod_channel", description="Configura o canal de moderação para receber tickets.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_mod_channel(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        config = get_guild_config(interaction.guild.id)
        config["mod_channel_id"] = canal.id
        set_guild_config(interaction.guild.id, config)
        await interaction.followup.send(f"Canal de moderação configurado: {canal.mention}", ephemeral=True)

    @app_commands.command(name="limpar", description="Apaga um número de mensagens do canal.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def limpar(self, interaction: discord.Interaction, quantidade: int):
        await interaction.response.defer()
        deleted = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(f"Pronto! `{len(deleted)}` mensagens apagadas.")
        await self._log_action(interaction, "🧹 Limpeza de Canal", {"Canal": interaction.channel.mention, "Mensagens Apagadas": f"`{len(deleted)}`"}, discord.Color.blue())

    # ---------------- BAN / KICK ----------------
    @app_commands.command(name="kick", description="Expulsa um membro do servidor.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Nenhum motivo fornecido."):
        await interaction.response.defer()
        if membro.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(f"Não posso expulsar `{membro.display_name}`. Role maior ou igual à minha.")
            return
        try:
            await membro.kick(reason=motivo)
            await interaction.followup.send(f"`{membro.display_name}` foi expulso. Motivo: {motivo}")
            await self._log_action(interaction, "👢 Membro Expulso", {"Membro Expulso": membro.mention, "Motivo": motivo}, discord.Color.red())
        except Exception as e:
            await interaction.followup.send(f"Erro ao expulsar `{membro.display_name}`: {e}")

    @app_commands.command(name="ban", description="Bane um membro do servidor.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Nenhum motivo fornecido."):
        await interaction.response.defer()
        if membro.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(f"Não posso banir `{membro.display_name}`. Role maior ou igual à minha.")
            return
        try:
            await membro.ban(reason=motivo)
            await interaction.followup.send(f"`{membro.display_name}` foi banido. Motivo: {motivo}")
            await self._log_action(interaction, "🔨 Membro Banido", {"Membro Banido": membro.mention, "Motivo": motivo}, discord.Color.dark_red())
        except Exception as e:
            await interaction.followup.send(f"Erro ao banir `{membro.display_name}`: {e}")

    # ---------------- TEMPBAN ----------------
    @app_commands.command(name="tempban", description="Ban temporário por X minutos.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def tempban(self, interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Nenhum motivo fornecido."):
        await interaction.response.defer()
        if membro.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(f"Não posso banir `{membro.display_name}`. Role maior ou igual à minha.")
            return
        try:
            await membro.ban(reason=motivo)
            unban_time = datetime.utcnow() + timedelta(minutes=minutos)
            self.tempbans[membro.id] = {"guild": interaction.guild.id, "unban_time": unban_time}
            await interaction.followup.send(f"`{membro.display_name}` foi banido por {minutos} minutos. Motivo: {motivo}")
            await self._log_action(interaction, "⏱️ Tempban", {"Membro": membro.mention, "Duração": f"{minutos} min", "Motivo": motivo}, discord.Color.dark_magenta())
        except Exception as e:
            await interaction.followup.send(f"Erro ao aplicar tempban `{membro.display_name}`: {e}")

    # ---------------- MUTE ----------------
    @app_commands.command(name="mute", description="Coloca um membro em timeout por X minutos.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Nenhum motivo fornecido."):
        await interaction.response.defer()
        try:
            duracao = discord.utils.utcnow() + timedelta(minutes=minutos)
            await membro.timeout(duracao, reason=motivo)
            await interaction.followup.send(f"`{membro.display_name}` foi mutado por {minutos} minutos. Motivo: {motivo}")
            await self._log_action(interaction, "🔇 Membro Mutado", {"Membro Mutado": membro.mention, "Duração": f"{minutos} minutos", "Motivo": motivo}, discord.Color.orange())
        except Exception as e:
            await interaction.followup.send(f"Erro ao mutar `{membro.display_name}`: {e}")

    @app_commands.command(name="unmute", description="Remove o timeout (mute) de um membro.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.defer()
        try:
            await membro.timeout(None, reason="Removido por comando /unmute")
            await interaction.followup.send(f"`{membro.display_name}` não está mais mutado.")
            await self._log_action(interaction, "🔊 Membro Desmutado", {"Membro Desmutado": membro.mention}, discord.Color.green())
        except Exception as e:
            await interaction.followup.send(f"Erro ao desmutar `{membro.display_name}`: {e}")

    # ---------------- WARNS ----------------
    @app_commands.command(name="warn", description="Aplica uma advertência a um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Nenhum motivo fornecido."):
        await interaction.response.defer(ephemeral=True)
        warns = get_warns()
        user_id = str(membro.id)
        if user_id not in warns:
            warns[user_id] = []
        warns[user_id].append({"moderador": str(interaction.user.id), "motivo": motivo})
        set_warns(warns)
        await interaction.followup.send(f"`{membro.display_name}` recebeu uma advertência. Motivo: {motivo}", ephemeral=True)
        await self._log_action(interaction, "⚠️ Advertência", {"Membro Advertido": membro.mention, "Motivo": motivo}, discord.Color.yellow())

    @app_commands.command(name="warns", description="Mostra todas as advertências de um usuário.")
    async def warns(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.defer(ephemeral=True)
        warns = get_warns()
        user_id = str(membro.id)
        if user_id not in warns or len(warns[user_id]) == 0:
            await interaction.followup.send(f"`{membro.display_name}` não tem advertências.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Advertências de {membro.display_name}", color=discord.Color.orange())
        for i, warn in enumerate(warns[user_id], start=1):
            moderador = await self.bot.fetch_user(int(warn["moderador"]))
            embed.add_field(name=f"Advertência {i}", value=f"Motivo: {warn['motivo']}\nModerador: {moderador.mention}", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="clear_warns", description="Remove todas as advertências de um usuário.")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_warns(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.defer(ephemeral=True)
        warns = get_warns()
        user_id = str(membro.id)
        if user_id in warns:
            warns[user_id] = []
            set_warns(warns)
            await interaction.followup.send(f"Todas as advertências de `{membro.display_name}` foram removidas.", ephemeral=True)
            await self._log_action(interaction, "🧹 Advertências Limpas", {"Membro": membro.mention}, discord.Color.blue())
        else:
            await interaction.followup.send(f"`{membro.display_name}` não tinha advertências.", ephemeral=True)

    # ---------------- HELP ----------------
    @app_commands.command(name="help", description="Mostra a lista de comandos disponíveis.")
    async def help_comandos(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="📜 Lista de Comandos - CaimBot", color=discord.Color.blurple())
        embed.add_field(
            name="⚙️ Moderação",
            value=(
                "/kick <membro> [motivo]\n"
                "/ban <membro> [motivo]\n"
                "/softban <membro> [motivo]\n"
                "/tempban <membro> <minutos> [motivo]\n"
                "/mute <membro> <minutos> [motivo]\n"
                "/unmute <membro>\n"
                "/warn <membro> [motivo]\n"
                "/warns <membro>\n"
                "/clear_warns <membro>\n"
                "/limpar <quantidade>\n"
                "/set_mod_channel <canal>"
            ),
            inline=False
        )
        embed.add_field(
            name="📝 Administração",
            value=("/setup_logs - Cria e configura canal de logs\n"
                   "/ping - Testa se o bot está online"),
            inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ---------------- SPAM ----------------
    @tasks.loop(seconds=1)  
    async def check_spam(self):
        for user_id, times in list(self.user_message_times.items()):
            self.user_message_times[user_id] = [t for t in times if (datetime.utcnow() - t).total_seconds() < 3]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = str(message.author.id)
        self.user_message_times.setdefault(user_id, []).append(datetime.utcnow())
        if len(self.user_message_times[user_id]) > 15:
            try:
                await message.channel.send(f"{message.author.mention}, você está enviando mensagens rápido demais!", delete_after=3)
                await message.delete()
            except:
                pass

# ---------------- SETUP ----------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderacao(bot))
