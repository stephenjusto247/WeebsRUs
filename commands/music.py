import os
import dotenv
import discord
from discord.ext import commands
import youtube_dl

# environment variables
dotenv.load_dotenv()
voice_channel_id = os.getenv('VOICE_CHANNEL_ID')

class music(commands.Cog):
  def __init__(self, client):
    self.client = client

def setup(client):
  try:
    client.add_cog(music(client))
    print('Successfully set up music commands')
  except Exception as e:
    print('Error occured when setting up music commands\n')
    print(e)