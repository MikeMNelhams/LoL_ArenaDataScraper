import numpy as np
from bisect import insort, bisect

from file_writers_library import FileReader, CSV_FileReader
from league_stats_library import Match, Champion
import pandas as pd


class ChampPlacementWriter(FileReader):
    champion_names_file_path = "champion_names.csv"
    champion_names_with_placements_file_path = "champion_names_with_placements.csv"

    def __init__(self, file_path: str, recorded_games_file_path: str = "recorded_games.csv"):
        super(ChampPlacementWriter, self).__init__(file_path)
        self._recorded_games_file_path = recorded_games_file_path
        self._recorded_games_reader = CSV_FileReader(recorded_games_file_path)
        self.__champ_names_file_reader = CSV_FileReader(self.champion_names_file_path)
        self.__champ_names_with_placements_file_reader = CSV_FileReader(self.champion_names_with_placements_file_path)

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

    def add_new_champion(self, champion: Champion) -> None:
        self.add_new_champion_name(champion)
        self.add_new_champion_name_with_placements(champion)
        self.add_new_champion_to_placements(champion)
        return None

    def add_new_champion_to_placements(self, champion: Champion) -> None:
        placement_data = self.load()
        insert_index = bisect(placement_data.columns.tolist(), f"{champion.name}_1")
        zeroes = [0 for _ in range(placement_data.shape[0])]
        for i in range(1, 5):
            placement_data.insert(loc=insert_index + i - 1, column=f"{champion.name}_{i}",
                                  value=zeroes.copy())
        index_names = placement_data.index.tolist()

        insert_index = bisect(index_names, champion.name)
        dataframe_above = placement_data.iloc[:insert_index, :]
        dataframe_below = placement_data.iloc[insert_index:, :]

        zeroes = [0 for _ in range(placement_data.shape[1])]

        new_row = pd.DataFrame([zeroes], columns=placement_data.columns.tolist(), index=[champion.name])
        placement_data = pd.concat((dataframe_above, new_row, dataframe_below))

        placement_data.to_csv(self.file_path)
        return None

    def add_new_champion_name(self, champion: Champion) -> None:
        champion_names_reader = self.__champ_names_file_reader
        champion_names = champion_names_reader.load()
        champion_names.columns = champion_names.columns.str.lower()
        champion_names_list = champion_names.columns.tolist()

        if champion.name in champion_names_list:
            print(f"The champion: \'{champion.name}\' is already added!")
            return None

        insort(champion_names_list, champion.name)

        champion_names = pd.DataFrame(columns=champion_names_list)
        champion_names_reader.save(champion_names)
        return None

    def add_new_champion_name_with_placements(self, champion: Champion) -> None:
        champion_names_with_placements_reader = self.__champ_names_with_placements_file_reader
        champion_names_with_placements = champion_names_with_placements_reader.load()
        champion_names_with_placements_list = champion_names_with_placements.columns.tolist()

        if f"{champion.name}_1" in champion_names_with_placements_list:
            print(f"The champion: \'{champion.name}\' is already added!")
            return None

        for i in range(1, 5):
            insort(champion_names_with_placements_list, f"{champion.name}_{i}")

        champion_names_with_placements = pd.DataFrame(columns=champion_names_with_placements_list)
        champion_names_with_placements_reader.save(champion_names_with_placements)
        return None
