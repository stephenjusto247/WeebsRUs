import logging
import discord
from discord.ext import commands
from prettytable import PrettyTable

# set up logging
log = logging.getLogger('bot')

class info(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  def _create_embed(self, message):
    embed = discord.Embed(description=message)
    return embed

  @commands.command()
  async def help(self, ctx):
    try:
      table = PrettyTable()
      table.field_names = ['command', 'description']
      rows = [
        ['$play', 'Play music from YouTube source'],
        ['$stop', 'Stops music and disconnects bot'],
        ['$pause', 'Pauses music'],
        ['$resume', 'Resumes music'],
      ]
      for row in rows:
        table.add_row(row)
      response = table.get_string()
      await ctx.send(embed=self._create_embed('**command list**\n```\n{}\n```'.format(response)))
    except Exception as e:
      log.error(e)

def setup(bot):
  try:
    bot.remove_command('help')
    bot.add_cog(info(bot))
    log.info('Successfully set up info')
  except Exception as e:
    log.info('Error occured when setting up info\n')
    log.error(e)