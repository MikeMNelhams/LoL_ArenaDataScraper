import numpy as np
import pandas as pd

from src.file_writers_library import FileReader, CSV_FileReader
from src.team8.league_stats_library import Champion, Match


class ChampPlacementWriter(FileReader):
    champion_names_file_path = "champion_names.csv"
    champion_names_with_placements_file_path = "champion_names_with_placements_team8.csv"

    def __init__(self, file_path: str, recorded_games_file_path: str = "recorded_games_team8.csv"):
        super(ChampPlacementWriter, self).__init__(file_path)
        self._recorded_games_file_path = recorded_games_file_path
        self._recorded_games_reader = CSV_FileReader(recorded_games_file_path)
        self.__champ_names_file_reader = CSV_FileReader(self.champion_names_file_path)
        self.__champ_names_with_placements_file_reader = CSV_FileReader(self.champion_names_with_placements_file_path)

    @property
    def recorded_games(self) -> pd.DataFrame:
        return self._recorded_games_reader.load()

    def save(self, match: Match) -> None:
        recorded_games = self.recorded_games
        game_id = match.game_id

        if game_id in recorded_games.columns:
            print(f"GameId: {game_id} already recorded. Data is not saved.")
            return None

        recorded_games_data: list = recorded_games.columns.tolist()

        recorded_games_data.append(game_id)
        recorded_games = pd.DataFrame([], columns=recorded_games_data)

        recorded_games.to_csv(self._recorded_games_file_path, index=False)
        data = self.load()

        for i, team in enumerate(match.teams):
            champion1 = team.champions[0]
            champion2 = team.champions[1]
            placement = match.scoreboard[i]
            data[f"{champion1.name}_{placement}"][champion2.name] += 1
            data[f"{champion2.name}_{placement}"][champion1.name] += 1

        data.to_csv(self.file_path, header=True)

    def load(self):
        return pd.read_csv(self.file_path, index_col=0)

    @property
    def champion_names(self) -> pd.DataFrame:
        champion_names_reader = self.__champ_names_file_reader
        champion_names = champion_names_reader.load()
        champion_names.columns = champion_names.columns.str.lower()
        return champion_names

    @property
    def champion_names_with_placements(self) -> pd.DataFrame:
        champion_names_with_placements_reader = self.__champ_names_with_placements_file_reader
        champion_names_with_placements = champion_names_with_placements_reader.load()
        return champion_names_with_placements

    def make_empty(self) -> None:
        user_confirmation = input("Are you sure? Y/N: ")
        if user_confirmation.lower() != 'y':
            print("Cancelling making empty.")
            return None

        champion_names = self.champion_names
        champion_names_with_placements = self.champion_names_with_placements

        num_entries = champion_names_with_placements.columns.size
        num_champions = champion_names.columns.size

        non_column_data = np.zeros((num_champions, num_entries), dtype=np.int)

        empty_data = pd.DataFrame(non_column_data, columns=champion_names_with_placements.columns, index=champion_names.columns)
        empty_data.to_csv(self.file_path)

        with open(self._recorded_games_file_path, 'w'):
            pass
        print(f"Files: {self.file_path} and {self._recorded_games_file_path} have been reset to default empty.")
        return None
