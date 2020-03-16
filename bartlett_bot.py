
import discord
from discord.ext import commands

import asyncpg
import asyncio
import os


token = os.environ.get("BARTLETT_BOT_TOKEN")
server_id = os.environ.get("BARTLETT_SERVER_ID")
PG_PSW = os.environ.get("POSTGRES_PSW")
client = discord.Client()

bot = commands.Bot(command_prefix='.')


@bot.event
async def on_ready():
    print("Bartlett bot is set and ready to work...")


async def create_db_pool():
    bot.pg_con = await asyncpg.create_pool(database="test_bartlett_db", user="postgres", password=PG_PSW)


for cog in os.listdir(".\\cogs"):
    if cog.endswith(".py") and not cog.startswith("_"):
        try:
            cog = f"""cogs.{cog.replace('.py', '')}"""
            bot.load_extension(cog)
        except Exception as e:
            print(f"""The {cog} cannot be loaded: """)
            raise e


# ========================================================================


bot.loop.run_until_complete(create_db_pool())
bot.run(token)
