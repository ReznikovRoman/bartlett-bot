
import discord
from discord.ext import commands

import os


token = os.environ.get("BARTLETT_BOT_TOKEN")
# server_id = os.environ.get("BARTLETT_SERVER_ID")
client = discord.Client()

bot = commands.Bot(command_prefix='.')


@bot.event
async def on_ready():
    print("Bartlett bot is set and ready to work...")


bot.run(token)
