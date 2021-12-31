import discord
from discord.ext import commands
from pprint import pprint
import youtube_dl

class music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  def _create_embed(self, message):
    embed = discord.Embed(description=message)
    return embed

  @commands.command()
  async def play(self, ctx):
    if ctx.author.voice is None:
      await ctx.send(self._create_embed('<@{}> Please connect to a voice channel first'.format(ctx.author.id)))
      return
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
      await voice_channel.connect()
    else:
      await ctx.voice_client.move_to(voice_channel)
  
  @commands.command()
  async def disconnect(self, ctx):
    if ctx.voice_client is None:
      await ctx.send(embed=self._create_embed('<@{}> I am not connected to a voice channel'.format(ctx.author.id)))
      return
    if ctx.author.voice is None:
      await ctx.send(embed=self._create_embed('<@{}> You are not connected to a voice channel'.format(ctx.author.id)))
      return
    if ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_client.channel:
      return await ctx.voice_client.disconnect()
    await ctx.send(embed=self._create_embed('<@{}> You must be in the same voice channel as me'.format(ctx.author.id)))

def setup(bot):
  try:
    bot.add_cog(music(bot))
    print('Successfully set up music commands')
  except Exception as e:
    print('Error occured when setting up music commands\n')
    print(e)