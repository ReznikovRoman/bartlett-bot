
import discord
from discord.ext import commands, tasks

import requests
import json
import re


def rank_formula(curr_rank, prev_rank):
    new_rank = (curr_rank + prev_rank*((prev_rank/curr_rank) + 0.1)) // 2
    return int(curr_rank) if curr_rank == prev_rank and new_rank != curr_rank else int(new_rank)


class R6Player(object):
    def __init__(self, player_url, platform=None):
        """
        :param player_nickname: string  --> Rainbow Six user's nickname
        :param platform: string  --> uplay  | psn  | xbl
        """
        self.url = player_url
        if platform is None:
            self.platform = "uplay"

    @property
    def player_id(self):
        pattern = re.compile('.*com/(.*)')
        r6_id = pattern.findall(self.url)
        if r6_id:
            return r6_id[0]
        else:
            return None

    def check_existence(self):
        if self.player_id:
            search_url = f"https://r6tab.com/api/player.php?p_id={self.player_id}"
            r = requests.get(search_url)
            response = json.loads(r.text)
            return response['playerfound']

    # def search_by_nickname(self):
    #     search_url = f"https://r6tab.com/api/search.php?platform={self.platform}&search={self.nickname}"
    #     r = requests.get(search_url)
    #     response = json.loads(r.text)
    #     return response['results']

    def search_by_id(self):
        if self.player_id:
            search_url = f"https://r6tab.com/api/player.php?p_id={self.player_id}"
            r = requests.get(search_url)
            response = json.loads(r.text)
            response['season17mmr'] = 2844
            return response

    def get_current_mmr(self):
        if self.player_id:
            response = self.search_by_id()
            return response['ranked']['mmr']

    def get_prev_mmr(self):
        if self.player_id:
            prev_season = ""
            response = self.search_by_id()
            for key, value in response.items():
                if str(key).startswith("season") and str(key).endswith("mmr"):
                    if value == self.get_current_mmr():
                        curr_season = key
                        prev_season = "season"+str(int(curr_season[6:8])-1)+"mmr"
                        break
                    else:
                        if value == 0:
                            continue
                        else:
                            prev_season = key
            return response[prev_season]

    def __str__(self):
        if self.player_id:
            return f"R6Tab URL: {self.url}, ID: {self.player_id};" \
                   f"\nBartlett MMR: {rank_formula(self.get_prev_mmr(), self.get_current_mmr())}\n"


class BartlettPlayer(object):
    """Class for discord server members, who participate in Bartlett Tournaments"""
    def __init__(self, member_id, user_nickname, tab_url, tab_id=None):
        """
        :param member_id: integer  --> discord Member id
        :param user_nickname: string  --> discord Member nickname
        :param tab_nickname: string  --> R6Tab user nickname
        :param tab_id: integer  --> Unique R6Tab player id
        """
        self.member_id = member_id
        self.user_nickname = user_nickname
        self.tab_url = tab_url
        # ===== Rainbow6 related fields ===============
        r6player = R6Player(tab_url)
        self.tab_id = r6player.player_id
        self.curr_mmr = r6player.get_current_mmr()
        self.prev_mmr = r6player.get_prev_mmr()
        self.bartlett_mmr = rank_formula(self.prev_mmr, self.curr_mmr)
        # ==============================================================
        self.curr_team = None  # Team, where user is going to play current tournament

    def __str__(self):
        return f"Member Nickname: {self.user_nickname}, Member Discord.id: {self.member_id};" \
               f"\nR6Tab URL: {self.tab_url}, R6Tab id: {self.tab_id}, Server MMR: {self.bartlett_mmr}\n"


def bot_text_channels(ctx):
    valid_channels = [688770023652589603,  # Test-Bot/bot-commands-open
                      688770173376659474,  # Test-Bot/bot-commands-close
                      688770413714473001  # Test-Bot/test-text
                      ]
    return ctx.channel.id in valid_channels


def bot_registration_channels(ctx):
    valid_registration_channels = [689166657020493885]  # Test-Bot/test-registration
    ctx: commands.Context
    return ctx.channel.id in valid_registration_channels


class RankedSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.__invalid_channel_msg = discord.Embed(title="Invalid text channel",
                                                   description="You can't use this channel for bot commands\n"
                                                               "Try to use '.help' command to learn more")

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):  # isinstance --> if <error> is <commands.CheckFailure>
            await ctx.send(content=None, embed=self.__invalid_channel_msg)

    @commands.command(name="sign-in")
    @commands.check(bot_registration_channels)
    async def sign_in(self, ctx: commands.Context, r6_url):
        r6player = R6Player(r6_url)
        print("test-main", r6player.check_existence())
        if r6player.player_id and r6player.check_existence():
            await ctx.send("Well done! You've successfully registered.")
        elif not r6player.player_id:
            await ctx.send("Please, check your nickname, I cannot find your profile\n"
                           "Enter your nickname once again (with __.sign-in__ command)")
        elif not r6player.check_existence():
            await ctx.send("Please, check your nickname, I cannot find your profile\n"
                           "Enter your nickname once again (with __.sign-in__ command)")
        else:
            await ctx.send("Ooops... Something went wrong\nPlease, try enter your nickname again or come back later")

        

    # =============== Cog's example =============
    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author == self.bot.user:
    #         return
    #
    #     author_id = str(message.author.id)
    #     print(f"""Member {author_id} has said: {message.content}""")

    # ===========================================


def setup(bot):
    bot.add_cog(RankedSystem(bot))
