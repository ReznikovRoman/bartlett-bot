
import discord
from discord.ext import commands, tasks

import requests
import json
import re


class R6Player:
    """ R6Tab Player class."""
    def __init__(self, player_url, platform=None):
        """
        :param player_url: string  --> Rainbow Six user's link
        :param platform: string  --> uplay  | psn  | xbl
        """
        self.url = player_url
        if platform is None:
            self.platform = "uplay"

    @property
    def tab_id(self):
        pattern = re.compile('.*com/(.*)')
        r6_id = pattern.findall(self.url)
        if r6_id:
            return r6_id[0]
        else:
            return None

    def is_exist(self):
        if self.tab_id:
            search_url = f"https://r6tab.com/api/player.php?p_id={self.tab_id}"
            r = requests.get(search_url)
            response = json.loads(r.text)
            return response['playerfound']

    # def search_by_nickname(self):
    #     search_url = f"https://r6tab.com/api/search.php?platform={self.platform}&search={self.nickname}"
    #     r = requests.get(search_url)
    #     response = json.loads(r.text)
    #     return response['results']

    def search_by_id(self):
        if self.is_exist():
            search_url = f"https://r6tab.com/api/player.php?p_id={self.tab_id}"
            r = requests.get(search_url)
            response = json.loads(r.text)
            response['season17mmr'] = 2844
            return response

    @property
    def curr_mmr(self):
        if self.is_exist():
            response = self.search_by_id()
            return response['ranked']['mmr']

    @property
    def prev_mmr(self):
        if self.is_exist():
            # prev_season = ""
            # response = self.search_by_id()
            # for key, value in response.items():
            #     if str(key).startswith("season") and str(key).endswith("mmr"):
            #         if value == self.curr_mmr:
            #             curr_season = key
            #             prev_season = "season" + str(int(curr_season[6:8]) - 1) + "mmr"
            #             break
            #         else:
            #             if value == 0:
            #                 continue
            #             else:
            #                 prev_season = key
            response = self.search_by_id()
            prev_season = "season16mmr"
            return response[prev_season]

    def __str__(self):
        if self.is_exist():
            return f"R6Tab URL: {self.url}, ID: {self.tab_id};" \
                   f"\nCurrent MMR: {self.prev_mmr}, Previous MMR: {self.curr_mmr}\n"


class BartlettPlayer(R6Player):
    """ Class for discord server members, who participate in Bartlett Tournaments """

    @staticmethod
    def __rank_formula(curr_rank, prev_rank):
        if curr_rank and prev_rank:
            if curr_rank < prev_rank:
                new_rank = (curr_rank + prev_rank * ((curr_rank / prev_rank) + 0.1)) // 2
            else:
                new_rank = (curr_rank + prev_rank * ((prev_rank / curr_rank) + 0.1)) // 2
            return int(curr_rank) if curr_rank == prev_rank and new_rank != curr_rank else int(new_rank)
        elif curr_rank and not prev_rank:
            return curr_rank
        elif prev_rank and not curr_rank:
            return prev_rank

    def __init__(self, member_id, user_nickname, tab_url, platform=None):
        """
        :param member_id: integer  --> discord Member id
        :param user_nickname: string  --> discord Member nickname
        :param tab_url: string  --> R6Tab user link
        :param platform: string  --> uplay | psn | xbl  ('uplay' by default)
        """

        super(BartlettPlayer, self).__init__(tab_url, platform)
        self.member_id = member_id
        self.user_nickname = user_nickname
        # ===== Rainbow6 related fields ===============
        # self.tab_id
        # self.curr_mmr
        # self.prev_mmr
        self.bartlett_mmr = self.__rank_formula(self.prev_mmr, self.curr_mmr)
        # ==============================================================
        self.curr_team = None  # Team, where user is going to play current tournament

    def __str__(self):
        return f"\nMember Nickname: {self.user_nickname}, Member Discord.id: {self.member_id};" \
               f"\nR6Tab URL: {self.url}, R6Tab id: {self.tab_id}, Server MMR: {self.bartlett_mmr}\n"


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
    async def sign_in(self, ctx: commands.Context, r6_url, platform=None):
        await ctx.send("Wait for a few seconds. I have to check your profile...")
        player = BartlettPlayer(ctx.author.id, ctx.author.name, r6_url, platform)
        print("test-main", player.is_exist())
        if player.tab_id and player.is_exist():
            await ctx.send("Well done! You've successfully registered.")
        elif not player.tab_id:
            await ctx.send("Please, check your nickname, I cannot find your profile\n"
                           "Enter your nickname once again (with __.sign-in__ command)")
        elif not player.is_exist():
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

