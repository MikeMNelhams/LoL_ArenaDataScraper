from src.team4.league_stats_file_writers import ChampPlacementWriterTeam4
from src.team8.league_stats_file_writers import ChampPlacementWriterTeam8
from src.champ_placement_writer import ChampPlacementWriter


__valid_numbers_of_teams = frozenset((4, 8))


class InvalidTeamCountError(Exception):
    def __init__(self, team_count: int):
        message = f"An arena game-mode with \'{team_count}\' players is invalid (or has yet to implemented with this stats tracker)."
        super().__init__(message)


def champ_placement_writer_factory(number_of_teams: int, champion_placements_file_name: str, recorded_games_file_name: str) -> ChampPlacementWriter:
    if number_of_teams not in __valid_numbers_of_teams:
        raise InvalidTeamCountError(number_of_teams)
    if number_of_teams == 4:
        return ChampPlacementWriterTeam4(champion_placements_file_name, recorded_games_file_name)
    if number_of_teams == 8:
        return ChampPlacementWriterTeam8(champion_placements_file_name, recorded_games_file_name)
    raise TypeError
