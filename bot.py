# package imports
import os
import sys
import dotenv
import discord
import logging
from discord.ext import commands

# project imports
import commands.music as Music
import commands.info as Info

# environment variables
dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# set up logging
logging.basicConfig(filename='bot.log', encoding='utf-8', level=logging.INFO)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
log = logging.getLogger('bot')
log.addHandler(consoleHandler)

cogs = [Music, Info]
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all(), activity=discord.Game('with Corey\'s heart'))
for cog in cogs:
  cog.setup(bot)

@bot.event
async def on_message(message):
  if message.author == bot.user: # ignore bot's own messages
    return

  if message.guild:
    await bot.process_commands(message) # process bot commands if message is not a dm

try:
  bot.run(token)
except Exception as e:
  log.debug('Failed to connect the bot to the server\n')
  log.error(e)
