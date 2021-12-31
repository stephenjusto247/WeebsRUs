# package imports
import os
import dotenv
import discord
from discord.ext import commands

# project imports
import commands.music as music

# environment variables
dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')
server = os.getenv('DISCORD_GUILD')
server_id = os.getenv('SERVER_ID')
text_channel_id = os.getenv('TEXT_CHANNEL_ID')
voice_channel_id = os.getenv('VOICE_CHANNEL_ID')

cogs = [music]

client = commands.Bot(command_prefix='$', intents=discord.Intents.all())

for cog in cogs:
  cog.setup(client)

@client.event
async def on_ready():
  print('{} has joined the server'.format(client.user.name))

@client.event
async def on_message(message):
  if message.author == client.user: # ignore bot's own messages
    return
  print(c)
  '''
  embed = discord.Embed(description=message.content)
  await message.channel.send(embed=embed)
  '''

try:
  client.run(token)
except Exception as e:
  print('Failed to connect the bot to the server\n')
  print(e)