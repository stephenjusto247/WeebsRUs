import discord
from discord.ext import commands
from pprint import pprint
import youtube_dl

class music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def test(self, ctx):
    print(self.bot.cogs['data'].get_main_guild())

def setup(bot):
  try:
    bot.add_cog(music(bot))
    print('Successfully set up music commands')
  except Exception as e:
    print('Error occured when setting up music commands\n')
    print(e)