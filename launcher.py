import asyncio
import glob
import random
import sys

import discord
import numpy as np
import pandas
from discord.ext import commands
from flask import Flask, render_template_string

from Core import dataCheck, Guild, session, emb, create_full_table, Player
from Core.preboot import *

# Initialize our app and the bot itself
app = Flask(__name__)


def load_ProfData():  # Level-Location-Profession
    dt = pandas.read_csv('Core/Game/Profession_Item_drop.csv',
                         names=["Level", "Location", "Lumberjack", "Miner", "Herbalism"],
                         skiprows=1).T.to_dict()

    lvl_dt = pandas.read_csv('Core/Game/Profession_xp.csv', names=["Level", "Xp Requirement"],
                             skiprows=1).T.to_dict()
    lvl_data = {x: lvl_dt[x]['Xp Requirement'] for x in lvl_dt if lvl_dt[x]['Xp Requirement'] is not np.nan}
    dt = {x: dt[x] for x in dt if dt[x]['Location'] is not np.nan}
    dt['level_data'] = lvl_data
    return dt


# print(load_ProfData())
# sys.exit()
def get_prefix(bot, message):
    """This allows custom prefix per server."""

    # Notice how you can use spaces in prefixes. Try to keep them simple though.
    prefixz = bot.master[message.guild.id]["prefix"]
    # prefixz = [session.query(Guild).filter_by(id=message.guild.id).first().prefix]
    if prefixz[0] is None:
        prefixz = ['+']

    # Check to see if we are outside of a guild. e.g DM's etc.
    if not message.guild:
        # Only allow + to be used in DMs
        return ['+']

    # If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixz)(bot, message)


def load_mods(extension: str, self):
    try:
        bot.load_extension(extension)
        logging.info("[{}] Loaded!.".format(extension))
        self.loaded = [f for f in self.cogs]
        return [True, None]
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        logging.error('Failed to load extension {}\n{}'.format(extension, exc))
        return [False, e]


# Main Bot Class
class MyClient(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = {}
        self.Settings = {}  # Bot Settings
        self.master["ProfData"] = load_ProfData()
        self.loaded = []  # Lists loaded modules

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.statuschange())

    async def statuschange(self):
        await self.wait_until_ready()
        message_list = [" {} people!.", "Ping pong with {} the crew", "Laser Tag with {} People"]
        while True:
            await self.change_presence(
                activity=discord.Game(name=random.choice(message_list).format(session.query(Player).count())))
            # logging.info(self.loaded)
            await asyncio.sleep(10)

    async def on_ready(self):

        create_full_table(self)
        checksettings(self)

        # Initial module Loading..
        plist = [f for f in os.listdir('modules') if ".py" in f]
        if '__init__.py' in plist:
            plist.remove("__init__.py")

        # load backup first
        plist.insert(0, plist.pop(plist.index('dropstorage.py')))
        [load_mods('modules' + "." + f.replace(".py", ""), self) for f in plist]

        # Check Data integrity
        dataCheck(self)

        logging.info("______________________________________________")
        logging.info(f'Logged in as: {bot.user.name} - {bot.user.id}')
        logging.info(f"Framework Version: {discord.__version__}")
        logging.info("______________________________________________")
        logging.info(f'Successfully logged in and booted...!')

    async def on_command_error(self, ctx, error):
        if "The global check functions for command" in str(error):
            await ctx.send(
                "```Python\n Install {} package to use this command ! \n Request your server admin to install this module.```".format(
                    ctx.command.cog_name))
        else:
            await ctx.message.channel.send("```" + str(error) + "```")


# Declaring Client & command prefixes/descriptions..
bot = MyClient(command_prefix=get_prefix, description='Get Some when you need it!')


@bot.command(hidden=True)
async def set_prefix(ctx, message):
    """
    Set the prefix for bot commands.
    :param ctx:
    :param message:
    :return:
    """
    row = session.query(Guild).filter(
        Guild.id == ctx.guild.id).first()
    row.prefix = message
    session.commit()
    try:
        bot.master[ctx.guild.id]["prefix"] = message
    except Exception as e:
        bot.master[ctx.guild.id] = {}
        bot.master[ctx.guild.id]["prefix"] = message
    await ctx.send('```Bot Command Prefix set to  : {}```'.format(message))


@bot.command(hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    """
    Save SQL Data and turn off the bot
    :param ctx:
    :return:
    """
    logging.warning('{} with id {} in server : {} has initiated bot shutdown!.'.format(ctx.author.name, ctx.author.id,
                                                                                       ctx.guild.id))
    await ctx.send(emb('Shutting Down....I will see you on the other side.'))
    session.commit()
    session.close()
    sys.exit()


@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.reload_extension("modules." + extension)
        await ctx.message.channel.send("Module [{}] reloaded!".format(extension))
    except (AttributeError, ImportError) as e:
        await ctx.message.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))


@bot.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension("modules." + extension)
        await ctx.message.channel.send("Module [{}] loaded!".format(extension))
    except (AttributeError, ImportError) as e:
        await ctx.message.channel.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))


@bot.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension("modules." + extension)
        await ctx.message.channel.send("Module [{}] unloaded!".format(extension))
    except  ModuleNotFoundError as e:
        logging.error(e)


@bot.command(hidden=True)
@commands.is_owner()
async def reboot(ctx):
    logging.warning(
        '{} with id {} in server : {} has initiated bot Reboot!.'.format(ctx.author.name, ctx.author.id, ctx.guild.id))
    session.commit()
    session.close()
    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)


# Set up the 'index' route
@app.route("/")
def hello():
    try:
        text = "<p>______________________________________________<br />" + f'Logged in as: {bot.user.name} - {bot.user.id}<br />' + f"Framework Version: {discord.__version__} <br />" + f'Successfully logged in and booted...!</p>'
        return text
    except Exception as e:
        return "None"


@app.route("/logs")
def logs():
    list_of_files = glob.glob('data/logs/console/*')  # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, "r") as f:
        text = ""
        for line in f:
            text += line + "<br/>"
        return render_template_string('''<html>
    <head>
        <title>HTML in 10 Simple Steps or Less</title>
        <meta http-equiv="refresh" content="5" >
    </head>
    <p>{}</p></html>'''.format(text), mimetype='text/plain')


# Make a partial app.run to pass args/kwargs to it
partial_run = partial(app.run, host="0.0.0.0", port=os.environ['PORT'], debug=True, use_reloader=False)

# Run the Flask app in another thread.
# Unfortunately this means we can't have hot reload
# (We turned it off above)
# Because there's no signal support.
t = Thread(target=partial_run)
t.start()



bot.run(os.environ['DISCORDAPI'], bot=True, reconnect=True)
