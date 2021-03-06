
import discord
from discord.ext import commands, tasks

import requests
import json
import re

import aiohttp
import asyncpg
from async_property import async_property
import asyncio


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

    async def search_by_id(self):
        search_url = f"https://r6tab.com/api/player.php?p_id={self.tab_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as r:
                response_text = await r.text()
                response = json.loads(response_text)
        return response

    async def is_exist(self):
        if self.tab_id:
            # search_url = f"https://r6tab.com/api/player.php?p_id={self.tab_id}"
            # async with aiohttp.ClientSession() as session:
            #     async with session.get(search_url) as r:
            #         response_text = await r.text  # response_text = await r.text()
            #         response = json.loads(response_text)
            #
            #         return response['playerfound']
            response = await self.search_by_id()
            return response['playerfound']

    # def search_by_nickname(self):
    #     search_url = f"https://r6tab.com/api/search.php?platform={self.platform}&search={self.nickname}"
    #     r = requests.get(search_url)
    #     response = json.loads(r.text)
    #     return response['results']

    @async_property
    async def curr_mmr(self):
        response = await self.search_by_id()
        return response['ranked']['mmr']

    @async_property
    async def prev_mmr(self):
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
        response = await self.search_by_id()
        prev_season = "season16mmr"  # TODO: find previous mmr --> rn can cause bugs in the next R6 Season
        return response[prev_season]

    def __str__(self):
        return f"R6Tab URL: {self.url}, ID: {self.tab_id};" \
               f"\nCurrent MMR: {self.prev_mmr}, Previous MMR: {self.curr_mmr}\n"


class BartlettPlayer(R6Player):
    """ Class for discord server members, who participate in Bartlett Tournaments """

    @staticmethod
    async def __rank_formula(curr_rank, prev_rank):  # TODO: (not urgent) - change 'Bartlett MMR' formula
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

        # self.bartlett_mmr = self.__rank_formula(self.prev_mmr, self.curr_mmr)

        # ==============================================================

        # self.curr_team = None  # Team, where user is going to play current tournament

    @async_property
    async def bartlett_mmr(self):
        return await self.__rank_formula(await self.prev_mmr, await self.curr_mmr)

    def __str__(self):
        return f"\nMember Nickname: {self.user_nickname}, Member Discord.id: {self.member_id};" \
               f"\nR6Tab URL: {self.url}, R6Tab id: {self.tab_id}, Server MMR: {self.bartlett_mmr}\n"


class PostgresDb:
    """
    Class for PostgresSQL
    For more info go to the documentation of 'asyncpg' : https://magicstack.github.io/asyncpg/current/api/index.html
    """
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def is_exist(self, table, bartlett_player: BartlettPlayer):
        """
        Checks (by a given  instance of 'BartlettPlayer' class), whether there is a <Player> in the <table> or not

        :param table: string  --> name of the table in the Postgres DB
        :param bartlett_player:  'BartlettPlayer'  --> object
        :return bool  --> True | False
        """
        p_query = f"SELECT * FROM {table} WHERE tab_id = $1 OR member_id = $2"
        result = await self.conn.fetchrow(p_query, bartlett_player.tab_id, bartlett_player.member_id)
        return True if result else False

    async def is_exist_id(self, table, member_id):
        """
        Checks (by a given 'discord.Member.id'), whether there is user in the <table> or not
        :param table: str  --> Table in the database
        :param member_id: int  --> unique 'discord Member id'
        :return: bool  --> True | False
        """
        p_query = f"SELECT * FROM {table} WHERE member_id = $1"
        result = await self.conn.fetchrow(p_query, member_id)
        return True if result else False

    async def insert_user(self, table, bartlett_player: BartlettPlayer):
        """
        Insert <Player> to the table (if he hadn't registered before)
        :param table: table_name: string  --> name of the table in the Postgres DB
        :param bartlett_player: 'BartlettPlayer'  --> player, that has to be inserted to the <table>
        :return: "insert player to the <table>" or "you've already registered"
        """

        print("Inserting...")

        p_query = f"INSERT INTO {table} (user_nickname, prev_mmr, curr_mmr, member_id, tab_id, bartlett_mmr) VALUES ($1, $2, $3, $4, $5, $6)"

        await self.conn.execute(p_query,
                                bartlett_player.user_nickname, await bartlett_player.prev_mmr,
                                await bartlett_player.curr_mmr, bartlett_player.member_id,
                                bartlett_player.tab_id, await bartlett_player.bartlett_mmr)
        print("Done!\n")
        # await self.conn.close()

    async def get_user(self, table, bartlett_id: str):
        """
        Returns member info from the <table> by a given <'bartlett_id' (discord.Member.id)>
        :param table: table_name: string  --> name of the table in the Postgres DB
        :param bartlett_id: str  --> unique discord id
        :return: <Record> user_nickname, prev_mmr, curr_mmr, member_id, tab_id, bartlett_mmr
        """

        print("DB - getting user info, id")

        p_query = f"SELECT * FROM {table} WHERE member_id = $1"
        result = await self.conn.fetchrow(p_query, int(bartlett_id))

        print("Done!\n")
        return result

    async def get_everyone(self, table):
        """
        Returns all <Records> from the given <table>
        :param table: str  --> name of the table in the DB
        :return: list of <Records>
        """
        print("Getting everything from", table)

        p_query = f"SELECT * FROM {table}"
        result = await self.conn.fetch(p_query)
        return result

    async def delete_by_id(self, table, member_id):
        """
        Deletes user from a given table by <discord.User.id>
        :param table: str  --> Table, from where you want to delete a user
        :param member_id: int  --> discord.User.id
        """
        print("Trying to delete a user...")

        # is_exist = await self.is_exist_id(table, member_id)

        p_query = f"DELETE FROM {table} WHERE member_id = $1"
        await self.conn.execute(p_query, int(member_id))  # 644099729096966146

        # await self.conn.close()
        print("Deleted!\n")


def bot_text_channels(ctx):
    """ Valid text channels for the 'Ranked System' """
    valid_channels = [688770023652589603,  # Test-Bot/bot-commands-open
                      688770173376659474,  # Test-Bot/bot-commands-close
                      688770413714473001  # Test-Bot/test-text
                      ]
    return ctx.channel.id in valid_channels


def bot_registration_channels(ctx):
    """ Valid channels for Registration in the 'Ranked System' """
    valid_registration_channels = [689166657020493885,  # Test-Bot/test-registration
                                   689939689892741298]  # "Bot Commands"/регистрация

    ctx: commands.Context
    return ctx.channel.id in valid_registration_channels


class RankedSystem(commands.Cog):
    """ Bartlett Ranked System """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__invalid_channel_msg = discord.Embed(title="Invalid text channel",
                                                   description="You can't use this channel for bot commands\n"
                                                               "Use '.help' command to learn more")

    async def cog_command_error(self, ctx: commands.Context, error):
        """ Handles 'commands.check()' errors """

        if isinstance(error, commands.CheckFailure):  # isinstance --> if <error> is <commands.CheckFailure>
            await ctx.send(content=None, embed=self.__invalid_channel_msg)

    @commands.command(name="sign-in")
    @commands.check(bot_registration_channels)
    async def sign_in(self, ctx: commands.Context, r6_url, platform=None):
        """ Add user to the db.user_info """

        await ctx.send("Wait for a few seconds. I have to check your profile...")
        player = BartlettPlayer(ctx.author.id, ctx.author.name, r6_url, platform)

        is_exist = await player.is_exist()

        print("test-main", is_exist)
        if player.tab_id and is_exist:
            print("Nickname: ", player.user_nickname)
            print("DataBase Test\n")

            conn = self.bot.pg_con
            registration_table = "user_info"
            db = PostgresDb(conn)

            if not await db.is_exist(registration_table, player):

                await db.insert_user(registration_table, player)
                await ctx.send("Well done! You've successfully registered.")
            else:
                await ctx.send("Oops...It seems that you're already registered.")

        # TODO: (not urgent) add errors handling instead of 'if statements'
        elif not player.tab_id:
            await ctx.send("Please, check your nickname, I cannot find your profile\n"
                           "Enter your nickname once again (with __.sign-in__ command)")
        elif not player.is_exist():
            await ctx.send("Please, check your nickname, I cannot find your profile\n"
                           "Enter your nickname once again (with __.sign-in__ command)")
        else:
            await ctx.send("Ooops... Something went wrong\nPlease, try enter your nickname again or come back later")

    @commands.command(name='get-user-id')  # get-player-id
    @commands.check(bot_text_channels)
    async def get_player(self, ctx, member_id):
        """ Get player info (<Record> from the db) by the given 'discord id' """

        print("test-get_player", ctx.author.id)

        conn = self.bot.pg_con
        registration_table = "user_info"
        db = PostgresDb(conn)

        player_info = await db.get_user(registration_table, member_id)

        if player_info:
            await ctx.send(str(player_info))
        else:
            await ctx.send("There is no registered user with such discord id.")

    @commands.command(name='get-everyone')  # get-all
    @commands.check(bot_text_channels)
    async def get_all_from_db(self, ctx):
        """ Get everyone from the db (so, get each registered User) """

        print("test-get_all", ctx.author.id)

        conn = self.bot.pg_con
        registration_table = "user_info"
        db = PostgresDb(conn)

        await ctx.send("Looking for each registered user...")
        users = await db.get_everyone(registration_table)
        for user in users:
            user: asyncpg.Record
            await ctx.send(str(user))
        print("Done!\n")

    @commands.command(name='delete-by-id')  # delete-by-id
    @commands.check(bot_text_channels)
    async def delete_user_from_db(self, ctx, member_id, table=None):
        """ Deletes user from the <table> by the given 'discord id' """

        print("test-delete_user with id: ", int(member_id))
        conn = self.bot.pg_con

        if table is None:
            table = "user_info"
        db = PostgresDb(conn)

        if await db.is_exist_id(table, int(member_id)):
            await db.delete_by_id(table, member_id)
            await ctx.send("User was deleted.")
        else:
            await ctx.send("There is no **registered** user with such discord id")

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

