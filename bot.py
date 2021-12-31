# package imports
import os
import dotenv
import discord
from discord.ext import commands

# project imports
import commands.data as data
import commands.music as music

# environment variables
dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')

cogs = [data, music]

bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

for cog in cogs:
  cog.setup(bot)

@bot.event
async def on_message(message):
  if message.author == bot.user: # ignore bot's own messages
    return
  await bot.process_commands(message)

try:
  bot.run(token)
except Exception as e:
  print('Failed to connect the bot to the server\n')
  print(e)