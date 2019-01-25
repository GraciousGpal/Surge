import discord
from discord import Embed
from discord.ext import commands
from prettytable import PrettyTable
from datetime import datetime
from Core import transaction, search, Query, create_player, emb, emoji_norm


class Economy:
    def __init__(self, bot):
        self.bot = bot
        self.Description = "Moolah Runs the World!, Adds Economy to the Server."
        self.provision = self.bot.loop.create_task(self.VresourceDist())

    @commands.command()
    async def profile(self, ctx, member=None):
        """
        View your own data and that of others.
        """
        """
        Gets User Info
        """
        if member is None:
            member = ctx.author
        else:
            member = await search(ctx, member)
        User = Query(obj=member).get()
        Player = Query(types="player", obj=member).get()

        if member is not None:
            embed = Embed(title="{}".format(member.name), color=(member.top_role.color))
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="Nick", value=member.nick, inline=True)
            moolah = User.moolah if User is not None else "Error"
            embed.add_field(name="Moolah", value=moolah, inline=True)
            embed.set_footer(text="{}-{}".format(member.id, str(member.joined_at)[:16]))

            if Player is not None:
                embed.add_field(name="Stats", value="▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁", inline=False)
                embed.add_field(name="Level", value=Player.level, inline=True)
                embed.add_field(name="Exp", value=Player.exp, inline=True)
                embed.add_field(name="Power", value=Player.atk, inline=True)
                embed.add_field(name="Mind", value=Player.defence, inline=True)

            await ctx.send(embed=embed)

            if Player is None:
                await ctx.send("```You have not created a character! {}create to create a character```".format(
                    self.bot.master[ctx.guild.id]["prefix"][0]))
        else:
            await ctx.send("**{}** not found! , Contact your bruh .".format(member))

    @commands.command()
    async def create(self, ctx, class_m):
        await create_player(ctx, class_m)

    @commands.command()
    async def market(self, ctx, number=20):
        """
        Buy and sell your goods in the market.
        """
        x = PrettyTable()
        x.field_names = ["Name", "Quantity", "Price"]
        test = Query(types='auction').get(number, 'id', 'desc')
        for item in test:
            x.add_row([item.item.name, item.quantity, item.price])
        await ctx.send("```Most Recent {} Listings: \n{}```".format(number, x))

    @commands.command()
    async def send(self, ctx, player=None, amount=None, message=None):
        """
        Send moolah to other players.
        """
        player = await search(ctx, player)

        if player is None:
            await ctx.send("Enter Player name to send Moolah. \n e.g ``` {}send billy 100 message[Optional]```".format(
                self.bot.master[ctx.guild.id]["prefix"][0]))

        elif amount is None:
            await ctx.send("Enter amount of Moolah to send!. \n e.g ``` {}send billy 100 message[Optional]```".format(
                self.bot.master[ctx.guild.id]["prefix"][0]))
        else:
            author = transaction(self.bot, ctx.author)
            reciever = transaction(self.bot, player)
            author.remove(amount)
            reciever.add(amount)
            await ctx.send("{} Moolah sent to {}!".format(amount, player))
            # DEBUG# await ctx.send("Sender Balance : {} Receiver Balance : {}".format(Query('user', ctx.author).get().moolah, Query('user', player).get().moolah))

    @commands.command()
    async def profession(self, ctx):
        """
        Select your profession or view profession.
        """

        await ctx.send(emb())

    @commands.command()
    async def topdog(self, ctx):
        """
        Shows the Top 10 Holders of Moolah and your Position (Local or Global).
        """
        x = PrettyTable()
        x.field_names = ["Position", "Names", "Moolah"]
        test = Query(types='user').get(10, 'moolah', 'desc')
        lis_form = list(test)
        author = [x.id for x in lis_form]
        for item in test:
            if ctx.author.name == item.name:
                name = "->>" + emoji_norm(item.name, "_") + "<<-"
            else:
                name = emoji_norm(item.name, "_")
            x.add_row([int(lis_form.index(item) + 1), name, item.moolah])

        if ctx.author.id not in author:
            test1 = list(Query(types='user').get('all', 'moolah', 'desc'))
            author = [test1.index(x) for x in test1 if x.id == ctx.author.id][0]
            mini_list = test1[author - 3:author + 3]
            x.add_row(["..........", "..........", ".........."])
            for member in mini_list:
                if member.id == ctx.author.id:
                    x.add_row([int(author - 3 + mini_list.index(member)), "->>" + emoji_norm(member.name, "_") + "<<-",
                               member.moolah])
                else:
                    x.add_row([int(author - 3 + mini_list.index(member)), member.name, member.moolah])
        logo = ''' _____               _             
|_   _|             | |            
  | | ___  _ __   __| | ___   __ _ 
  | |/ _ \| '_ \ / _` |/ _ \ / _` |
  | | (_) | |_) | (_| | (_) | (_| |
  \_/\___/| .__/ \__,_|\___/ \__, |
          | |                 __/ |
          |_|                |___/ \n'''
        await ctx.send('```{}{}```'.format(logo, x))

    @commands.command()
    async def role(self, ctx, action=None, role_name=None):
        """
        Lobby Moolah to increase your status.
        """
        test = Query(types='role').get(number='special', orderby='price', order='desc').filter_by(guild_id=ctx.guild.id)
        if action is None and role_name is None:
            x = PrettyTable()
            x.field_names = ["Name", "Price"]
            for item in test:
                if item.price is not None:
                    x.add_row([discord.utils.get(ctx.message.guild.roles, id=item.id).name, item.price])
            await ctx.send("```{}```".format(x))

        elif action == "buy" and role_name is not None:
            role = discord.utils.get(ctx.message.guild.roles, name=role_name)
            author = transaction(self.bot, ctx.author)
            is_sale = [x.price for x in test if x.id == role.id][0]
            if is_sale is None:
                await ctx.send("{} is not for sale on this server!.".format(role_name))
            else:
                author.remove(is_sale)
                await ctx.message.author.add_roles(role,
                                                   reason="Purchased Time:{}".format(datetime.now()))
                await ctx.send("Congrats you have purchased {}!.".format(role_name))
        elif action == "sell" and role_name is not None:
            await ctx.send("IN PROGRESS")

    async def VresourceDist(self):
        """
        Continuous function that distributes moolah to the miners
        :return:
        """
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                x = "sss"

        pass

    async def on_message(self, message):
        amount = 2
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
