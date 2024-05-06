from src.league_library import Champion, Team


class Match:
    def __init__(self, teams: list[Team], scoreboard: list, game_id: str):
        assert len(teams) == 8, TypeError
        self.__match_info = self.__generate_match_info(teams, scoreboard, game_id)
        self.teams = teams
        self.scoreboard = scoreboard
        self.game_id = game_id

    def __repr__(self):
        return f"Match({self.game_id}, {self.teams}, {self.scoreboard})"

    @staticmethod
    def __generate_match_info(teams: list[Team], scoreboard: list, game_id: str) -> dict:
        info_dict = {f"team{i + 1}": team.data for i, team in enumerate(teams)}
        info_dict["scoreboard"] = scoreboard
        return {game_id: info_dict}

    @classmethod
    def from_game_data(cls, game_data: dict):
        new_match = cls.__new__(cls)

        participants = list(game_data["info"]["participants"])
        champions = [[] for _ in range(8)]
        scoreboard = [-1 for _ in range(16)]
        for player in participants:
            champions[player["playerSubteamId"] - 1].append(Champion(player["championName"]))
            scoreboard[player["playerSubteamId"] * 2 - 2] = player["placement"]
            scoreboard[player["playerSubteamId"] * 2 - 1] = player["placement"]
        try:
            teams = tuple(Team(champions[i][0], champions[i][1]) for i in range(8))
        except IndexError as e:
            print(champions, participants, scoreboard)
            raise e
        game_id = game_data["metadata"]["matchId"]
        new_match.teams = teams
        new_match.scoreboard = scoreboard[::2]
        new_match.game_id = game_id
        new_match.__match_info = cls.__generate_match_info(teams, scoreboard, game_id)
        return new_match
