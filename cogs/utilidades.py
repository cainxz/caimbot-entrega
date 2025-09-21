# cogs/utilidades.py
import discord
from discord import app_commands
from discord.ext import commands

class SayModal(discord.ui.Modal, title="Enviar mensagem"):
    def __init__(self, canal: discord.TextChannel):
        super().__init__()
        self.canal = canal

        self.mensagem = discord.ui.TextInput(
            label="Mensagem",
            style=discord.TextStyle.paragraph,
            placeholder="Digite a mensagem que o bot deve enviar...",
            required=True,
            max_length=4000
        )
        self.add_item(self.mensagem)

    async def on_submit(self, interaction: discord.Interaction):
        texto = self.mensagem.value

        if texto.startswith(">"):
            linhas = texto.split("\n")
            texto = "\n".join(
                [linhas[0]] + ["> " + l if l and not l.startswith(">") else l for l in linhas[1:]]
            )

        await self.canal.send(texto)
        await interaction.response.send_message(
            f"✅ Mensagem enviada em {self.canal.mention}", ephemeral=True
        )

class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Faz o bot enviar uma mensagem em um canal.")
    @app_commands.describe(
        canal="Canal onde a mensagem será enviada"
    )
    @app_commands.checks.has_permissions(administrator=True)  
    async def say(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.send_modal(SayModal(canal))

async def setup(bot):
    await bot.add_cog(Utilidades(bot))
