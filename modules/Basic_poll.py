import asyncio

from discord.ext import commands

settings = {"POLL_DURATION": 36000}


class Pollplus(commands.Cog):
    """Poll+ commands."""

    def __init__(self, bot):
        self.bot = bot
        self.poll_sessions = []

    @commands.command(pass_context=True, no_pm=True)
    async def poll(self, ctx, *text):
        """Starts/stops a poll
        Usage example:
        poll Is this a poll?;Yes;No;Maybe
        poll stop
        This is modified poll with a varible minutes poll period."""
        message = ctx.message
        if len(text) == 1:
            if text[0].lower() == "stop":
                await self.endpoll(message)
                return
        if not self.getPollByChannel(message):
            check = " ".join(text).lower()
            if "@everyone" in check or "@here" in check:
                await ctx.send("Nice try.")
                return
            p = NewPoll(message, self)
            if p.valid:
                self.poll_sessions.append(p)
                await p.start()
            else:
                await ctx.send("poll question;option1;option2 (...)")
        else:
            await ctx.send("A poll is already ongoing in this channel.")

    async def endpoll(self, message):
        if self.getPollByChannel(message):
            p = self.getPollByChannel(message)
            if p.author == message.author.id:  # or isMemberAdmin(message)
                await self.getPollByChannel(message).endPoll()
            else:
                await message.channel.send("Only admins and the author can stop the poll.")
        else:
            await message.channel.send("There's no poll ongoing in this channel.")

    def getPollByChannel(self, message):
        for poll in self.poll_sessions:
            if poll.channel == message.channel:
                return poll
        return False

    async def check_poll_votes(self, message):
        if message.author.id != self.bot.user.id:
            if self.getPollByChannel(message):
                await self.getPollByChannel(message).checkAnswer(message)


class NewPoll():
    def __init__(self, message, main):
        self.channel = message.channel
        self.author = message.author.id
        self.client = main.bot
        self.poll_sessions = main.poll_sessions
        msg = message.content[6:]
        msg = msg.split(";")
        if len(msg) < 2:  # Needs at least one question and 2 choices
            self.valid = False
            return None
        else:
            self.valid = True
        self.already_voted = []
        self.question = msg[0]
        msg.remove(self.question)
        self.answers = {}
        i = 1
        for answer in msg:  # {id : {answer, votes}}
            self.answers[i] = {"ANSWER": answer, "VOTES": 0}
            i += 1

    async def start(self):
        msg = "**POLL STARTED!**\n\n{}\n\n".format(self.question)
        for id, data in self.answers.items():
            msg += "{}. *{}*\n".format(id, data["ANSWER"])
        msg += "\nType the number to vote!"
        await self.channel.send(msg)
        await asyncio.sleep(settings["POLL_DURATION"])
        if self.valid:
            await self.endPoll()

    async def endPoll(self):
        self.valid = False
        msg = "**POLL ENDED!**\n\n{}\n\n".format(self.question)
        for data in self.answers.values():
            msg += "*{}* - {} votes\n".format(
                data["ANSWER"], str(data["VOTES"]))
        await self.channel.send(msg)
        self.poll_sessions.remove(self)

    async def checkAnswer(self, message):
        try:
            i = int(message.content)
            if i in self.answers.keys():
                if message.author.id not in self.already_voted:
                    data = self.answers[i]
                    data["VOTES"] += 1
                    self.answers[i] = data
                    self.already_voted.append(message.author.id)
            await message.delete()
        except ValueError:
            pass


def setup(bot):
    n = Pollplus(bot)
    bot.add_listener(n.check_poll_votes, "on_message")
    bot.add_cog(n)
