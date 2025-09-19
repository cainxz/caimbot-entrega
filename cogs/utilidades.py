# cogs/utilidades.py
import discord
from discord import app_commands
from discord.ext import commands

class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Faz o bot enviar uma mensagem em um canal.")
    @app_commands.describe(
        canal="Canal onde a mensagem será enviada",
        mensagem="O que o bot deve dizer"
    )
    @app_commands.checks.has_permissions(administrator=True)  # 🔒 Só admins podem usar
    async def say(self, interaction: discord.Interaction, canal: discord.TextChannel, mensagem: str):
        # Envia a mensagem no canal escolhido
        await canal.send(mensagem)
        # Confirma de forma privada
        await interaction.response.send_message(f"✅ Mensagem enviada em {canal.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utilidades(bot))
