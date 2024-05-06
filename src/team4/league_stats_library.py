from __future__ import annotations


from src.league_library import Champion, Team


class Match:
    def __init__(self, teams: list[Team], scoreboard: list, game_id: str):
        assert len(teams) == 4, TypeError
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
        champions = [Champion(player["championName"]) for player in participants]
        scoreboard = [player["placement"] for player in participants]

        team1 = Team(champions[0], champions[1])
        team2 = Team(champions[2], champions[3])
        team3 = Team(champions[4], champions[5])
        team4 = Team(champions[6], champions[7])

        teams = (team1, team2, team3, team4)
        game_id = game_data["metadata"]["matchId"]
        new_match.teams = teams
        new_match.scoreboard = scoreboard[::2]
        new_match.game_id = game_id
        new_match.__match_info = cls.__generate_match_info(teams, scoreboard, game_id)
        return new_match


def main():
    print("This is a library file. Do not run as main.")


if __name__ == "__main__":
    main()
