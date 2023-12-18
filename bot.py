# package imports
import asyncio
import discord
import dotenv
import logging
import os
import sys
from discord.ext import commands

# project imports
import commands.music as Music
import commands.info as Info

# environment variables
dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')
guild_id = os.getenv('GUILD_ID')
activity = os.getenv('ACTIVITY')

# set up logging
logging.basicConfig(filename='bot.log', encoding='utf-8', level=logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
log = logging.getLogger('bot')
log.addHandler(handler)

bot = commands.Bot(command_prefix=Info.COMMAND_PREFIX, intents=discord.Intents.all(), activity=discord.Game(activity))

@bot.event
async def on_ready():
  try:
    commands = await bot.tree.sync(guild=discord.Object(id=guild_id))
    command_names = []
    for command in commands:
      command_names.append(f'{command.name}')
    log.info(f'Successfully synced {command_names}')
  except Exception as e:
    log.error(e)

async def load_cogs():
  cogs = [Music, Info]
  for cog in cogs:
    await cog.setup(bot, log, guild_id)

asyncio.run(load_cogs())
bot.run(token, reconnect=True, log_handler=handler)
