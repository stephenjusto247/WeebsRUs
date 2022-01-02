import logging
from discord.ext import commands
from prettytable import PrettyTable

# project imports
from lib.utils import create_embed

# set up logging
log = logging.getLogger('bot')

class Info(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

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
        ['$currentsong', 'Display current song'],
        ['$skip', 'Skips the current song'],
        ['$queue', 'Get queue info']
      ]
      for row in rows:
        table.add_row(row)
      response = table.get_string()
      await ctx.send(embed=create_embed('**command list**\n```\n{}\n```'.format(response)))
    except Exception as e:
      log.error(e)

def setup(bot):
  try:
    bot.remove_command('help')
    bot.add_cog(Info(bot))
    log.info('Successfully set up help command')
  except Exception as e:
    log.info('Error occured when setting up info\n')
    log.error(e)