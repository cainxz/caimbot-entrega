import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import asyncio


load_dotenv()
token_dc = os.getenv("bot_token")

Intents = discord.Intents.default()
Intents.message_content = True
Intents.members = True

bot = commands.Bot(command_prefix="/", intents=Intents)


@bot.event
async def on_ready():
    print(f"O {bot.user} está online!")
    print("--------------------")
    print("Sincronizando árvore de comandos...")
    try:
        synced = await bot.tree.sync()
        print(f"Árvore de comandos sincronizada. {len(synced)} comandos carregados.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")



@bot.tree.command(name="ping", description="Responde com uma mensagem de teste.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"{interaction.user.mention} pinga uma sugada aqui no meu ovo filho da puta!"
    )


async def main():
    async with bot:
        await bot.load_extension("cogs.moderacao")
        await bot.load_extension("cogs.suporte")
        await bot.load_extension("cogs.logs_suporte")  
        await bot.load_extension("cogs.utilidades")
        await bot.start(token_dc)

asyncio.run(main())
