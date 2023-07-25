import numpy as np

from file_writers_library import FileReader, CSV_FileReader
from league_stats_library import Match
import pandas as pd


class ChampPlacementWriter(FileReader):
    def __init__(self, file_path: str, recorded_games_file_path: str = "recorded_games.csv"):
        super(ChampPlacementWriter, self).__init__(file_path)
        self._recorded_games_reader = CSV_FileReader(recorded_games_file_path)
        self._recorded_games_file_path = recorded_games_file_path

    def save(self, match: Match) -> None:
        recorded_games = self._recorded_games_reader.load()
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
            data[champion1.name + f"_{placement}"][champion2.name] += 1
            data[champion2.name + f"_{placement}"][champion1.name] += 1

        data.to_csv(self.file_path, header=True)
        return None

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.file_path, index_col=0)

    def make_empty(self) -> None:
        user_confirmation = input("Are you sure? Y/N ")
        if user_confirmation.lower() != 'y':
            print("Cancelling making empty.")
            return None

        champion_names_with_placements_reader = CSV_FileReader("champion_names_with_placements.csv")
        champion_names_with_placements = champion_names_with_placements_reader.load()

        champion_names_reader = CSV_FileReader("champion_names.csv")
        champion_names = champion_names_reader.load()
        champion_names.columns = champion_names.columns.str.lower()

        num_entries = champion_names_with_placements.columns.size
        num_champions = champion_names.columns.size

        non_column_data = np.zeros((num_champions, num_entries), dtype=np.int)

        empty_data = pd.DataFrame(non_column_data, columns=champion_names_with_placements.columns, index=champion_names.columns)

        empty_data.to_csv(self.file_path)

        with open(self._recorded_games_file_path, 'w'):
            pass
        print(f"Files: {self.file_path} and {self._recorded_games_file_path} have been reset to default empty.")
        return None
