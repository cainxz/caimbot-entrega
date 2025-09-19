# cogs/logs_suporte.py
import discord
from discord import app_commands
from discord.ext import commands
import json
import os

CONFIG_FILE = "config.json"

# -------------------------
# Funções auxiliares de config
# -------------------------
def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def set_guild_config(guild_id, key, value):
    config = get_config()
    if str(guild_id) not in config:
        config[str(guild_id)] = {}
    config[str(guild_id)][key] = value
    save_config(config)

def get_guild_config(guild_id, key):
    config = get_config()
    return config.get(str(guild_id), {}).get(key)

# -------------------------
# Cog de Logs do Suporte
# -------------------------
class LogsSuporte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Comando para configurar canal de logs do SUPORTE
    @app_commands.command(name="setup_logs_suporte", description="Cria e configura um canal de logs de SUPORTE neste servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_logs_suporte(self, interaction: discord.Interaction):
        guild = interaction.guild

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
        }

        # cria o canal com nome específico
        canal = await guild.create_text_channel("📜-logs-suporte", overwrites=overwrites)

        set_guild_config(guild.id, "suporte_logs_channel_id", canal.id)

        await interaction.response.send_message(
            f"✅ Canal de logs de suporte criado: {canal.mention}",
            ephemeral=True
        )

    # Função para enviar log do suporte
    async def send_suporte_log(self, guild_id: int, mensagem: str, embed: discord.Embed = None):
        canal_id = get_guild_config(guild_id, "suporte_logs_channel_id")
        if canal_id:
            canal = self.bot.get_channel(canal_id)
            if canal:
                if embed:
                    await canal.send(content=mensagem, embed=embed)
                else:
                    await canal.send(mensagem)

async def setup(bot):
    await bot.add_cog(LogsSuporte(bot))
