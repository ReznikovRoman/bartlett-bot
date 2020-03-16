
def rank_formula(curr_rank, prev_rank):
    new_rank = (curr_rank + prev_rank*((prev_rank/curr_rank) + 0.1)) // 2
    return int(curr_rank) if curr_rank == prev_rank and new_rank != curr_rank else int(new_rank)


class Player(object):
    def __init__(self, discord_id, discord_nickname, tab_id, current_rank, prev_rank):
        """
        :param discord_id: int  --> user ID
        :param discord_nickname: string  --> user nickname
        :param tab_id: int  --> member r6tab ID
        :param current_rank: int  --> current MMR amount (r6tab API)
        :param prev_rank: int  --> MMR amount in the previous season (r6tab API)
        """
        self.discord_id = discord_id
        self.discord_nick = discord_nickname
        self.tab_id = tab_id
        self.curr_rank = current_rank
        self.prev_rank = prev_rank
        self.bartlett_rank = rank_formula(self.prev_rank, self.curr_rank)
        self.team_role = None

    def __str__(self):
        return f"""Nickname: {self.discord_nick}, R6Tab ID: {self.tab_id};
Current MMR: {self.curr_rank}, Previous MMR: {self.prev_rank}, Average MMR: {self.bartlett_rank}, Team: {self.team_role}\n"""

# =========================================


# =========CREATE PLAYERS==================
p1 = Player(448551164938551296, "salute.-", 1, 3000, 5000)
p2 = Player(122342434343232323, "Ivan", 2, 3000, 4000)
p3 = Player(765645434343555353, "Roman", 3, 2500, 2500)
p4 = Player(353547576785687655, "Jim", 4, 4500, 4300)
p5 = Player(122342434343, "Bill", 5, 3300, 3300)
p6 = Player(122342434343, "Stepan", 6, 5000, 5500)

p7 = Player(122342434343, "Egor", 7, 3600, 3550)
p8 = Player(122342434343, "Artem", 8, 3750, 3700)
p9 = Player(122342434343, "Zolto", 9, 3800, 4400)
p10 = Player(122342434343, "Makar", 10, 3200, 3500)
p11 = Player(122342434343, "Jane", 11, 2900, 3300)
p12 = Player(122342434343, "Nicolas", 12, 4700, 5000)

lobby = [p1, p2, p3, p4, p5, p6,
         p7, p8, p9, p10, p11, p12]


# =========CREATE MATCH==================
# for player in players:
#     print(player)

def sort_by_rank(a_player):
    return a_player.bartlett_rank


teamA = []
teamB = []

sorted_lobby = sorted(lobby, key=sort_by_rank, reverse=True)

# ======Test=======
for player in sorted_lobby:
    print(player.bartlett_rank)
# ==============================

for player_ind in range(len(sorted_lobby)):
    if player_ind % 2 == 0:
        sorted_lobby[player_ind].team_role = "role_Team_A_"
        teamA.append(sorted_lobby[player_ind])
    else:
        sorted_lobby[player_ind].team_role = "role_Team_B_"
        teamB.append(sorted_lobby[player_ind])
    # teamA.append(sorted_lobby[player_ind]) if player_ind % 2 == 0 else teamB.append(sorted_lobby[player_ind])

# ======-Test-1-========
# print()
# for playerA, playerB in zip(teamA, teamB):
#     print(playerA.bartlett_rank, end=" ")
#     print(playerB.bartlett_rank)

# ======-Test-2-========
print()

print("Team A: ")
for player in teamA:
    print(player)

print()
print("Team B: ")
for player in teamB:
    print(player)

# =======================================================




