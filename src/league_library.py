class InvalidNumberOfParticipantsError(Exception):
    def __init__(self, number_of_players: int):
        message = f"An arena match must have 2 players per team, so cannot have {number_of_players}"
        super().__init__(message)


class Champion:
    def __init__(self, name: str):
        name_lower = name.lower()
        self.name = name_lower
        if name_lower == "nunu":
            self.name = "nunu&willump"  # The RIOT backend is bugged, they use 2 names for Nunu.

    def __repr__(self):
        return self.name

    @property
    def data(self) -> str:
        return self.name


class Team:
    def __init__(self, *champions: Champion):
        assert len(champions) == 2, TypeError
        self.champions: list[Champion] = [*champions]

    def __repr__(self):
        return str(self.champions)

    @property
    def data(self) -> dict:
        return {"champions": [champion.data for champion in self.champions]}


class Match:
    def __init__(self, teams: list[Team], scoreboard: list, game_id: str):
        self.__match_info = self.__generate_match_info(teams, scoreboard, game_id)
        self.teams = teams
        self.scoreboard = scoreboard
        self.game_id = game_id

    def __repr__(self) -> str:
        return f"Match({self.teams}, {self.scoreboard}, {self.game_id})"

    @staticmethod
    def __generate_match_info(teams: list[Team], scoreboard: list, game_id: str) -> dict:
        info_dict = {f"team{i + 1}": team.data for i, team in enumerate(teams)}
        info_dict["scoreboard"] = scoreboard
        return {game_id: info_dict}

    @classmethod
    def from_game_data(cls, game_data: dict):
        new_match = cls.__new__(cls)

        participants = list(game_data["info"]["participants"])
        number_of_players = len(participants)
        if number_of_players & 1:
            raise InvalidNumberOfParticipantsError

        number_of_teams = number_of_players // 2
        champions = [[] for _ in range(number_of_teams)]
        scoreboard = [-1 for _ in range(number_of_players)]
        for player in participants:
            champions[player["playerSubteamId"] - 1].append(Champion(player["championName"]))
            scoreboard[player["playerSubteamId"] * 2 - 2] = player["placement"]
            scoreboard[player["playerSubteamId"] * 2 - 1] = player["placement"]
        teams = tuple(Team(champions[i][0], champions[i][1]) for i in range(number_of_teams))
        game_id = game_data["metadata"]["matchId"]

        new_match.teams = teams
        new_match.scoreboard = scoreboard[::2]
        new_match.game_id = game_id
        new_match.__match_info = cls.__generate_match_info(teams, scoreboard, game_id)
        return new_match
