import os
import dotenv
from discord.ext import commands

# environment variables
dotenv.load_dotenv()
server_id = os.getenv('SERVER_ID')
text_channel_id = os.getenv('TEXT_CHANNEL_ID')
voice_channel_id = os.getenv('VOICE_CHANNEL_ID')

class data(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  def get_main_guild(self):
    return self.guild

  def get_main_text_channel(self):
    return self.text_channel

  def get_main_voice_channel(self):
    return self.voice_channel

  @commands.Cog.listener()
  async def on_ready(self):
    bot = self.bot
    try:
      guild = bot.get_guild(int(server_id))
      text_channel = bot.get_channel(int(text_channel_id))
      voice_channel = bot.get_channel(int(voice_channel_id))
      if guild is not None:
        self.guild = guild
        print('{} has joined {}'.format(bot.user.name, guild.name))
      if text_channel is not None:
        self.text_channel = text_channel
      if voice_channel is not None:
        self.voice_channel = voice_channel
    except Exception as e:
      print(e)

def setup(bot):
  try:
    bot.add_cog(data(bot))
    print('Successfully set up data')
  except Exception as e:
    print('Error occured when setting up data\n')
    print(e)