from abc import ABC, abstractmethod

from bisect import insort, bisect

import numpy as np
import pandas as pd

from src.file_writers_library import FileReader, CSV_FileReader
from src.team8.league_stats_library import Champion, Match


class ChampPlacementWriter(FileReader, ABC):
    champion_names_file_path = "champion_names.csv"

    def __init__(self, file_path: str, recorded_games_file_path: str):
        super(ChampPlacementWriter, self).__init__(file_path)
        self._recorded_games_file_path = recorded_games_file_path

        self._recorded_games_reader = CSV_FileReader(recorded_games_file_path)
        self.__champ_names_file_reader = ChampionNamesReader(self.champion_names_file_path)

        if self.exists and not self.is_empty:
            self.validate_configuration()

    @abstractmethod
    def number_of_teams(self) -> int:
        raise NotImplementedError

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

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.file_path, index_col=[0])

    @property
    def champion_names(self) -> pd.DataFrame:
        return self.__champ_names_file_reader.champion_names

    @property
    def champion_names_with_placements(self) -> pd.DataFrame:
        return self.__champ_names_file_reader.champion_names_with_placements

    def make_empty(self) -> None:
        user_confirmation = input(f"Are you sure you want to OVERWRITE the files: \'{self.file_path}\' and \'{self._recorded_games_file_path}\' empty? Y/N: ")
        if user_confirmation.lower() != 'y':
            print("Cancelling making empty.")
            return None

        champion_names = self.champion_names
        champion_names_with_placements = self.champion_names_with_placements
        column_names = ["champion_names"] + champion_names_with_placements.values.tolist()

        num_entries = champion_names_with_placements.columns.size
        num_champions = champion_names.columns.size

        non_column_data = np.zeros((num_champions, num_entries), dtype=np.int32)

        empty_data = pd.DataFrame(non_column_data, columns=column_names, index=champion_names.columns)
        empty_data.to_csv(self.file_path)

        with open(self._recorded_games_file_path, 'w'):
            pass
        print(f"Files: {self.file_path} and {self._recorded_games_file_path} have been reset to default empty.")
        return None

    def add_new_champion(self, champion: Champion) -> None:
        self.add_new_champion_name(champion)
        self.add_new_champion_to_placements(champion)
        return None

    def add_new_champion_name(self, champion: Champion) -> None:
        champion_names = self.champion_names
        champion_names.columns = champion_names.columns.str.lower()
        champion_names_list = champion_names.columns.tolist()

        if champion.name in champion_names_list:
            print(f"The champion: \'{champion.name}\' is already added!")
            return None

        insort(champion_names_list, champion.name)

        champion_names = pd.DataFrame(columns=champion_names_list)
        self.__champ_names_file_reader.save_new_champion_names(champion_names)
        return None

    def add_new_champion_to_placements(self, champion: Champion) -> None:
        placement_data = self.load()
        insert_index = bisect(placement_data.columns.tolist(), f"{champion.name}_1")
        zeroes = [0 for _ in range(placement_data.shape[0])]
        for i in range(1, self.number_of_teams() + 1):
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

    @abstractmethod
    def validate_configuration(self) -> None:
        raise NotImplementedError


class ChampionNamesReader:
    def __init__(self, champion_names_file_path: str = "champion_names.csv"):
        self.champion_names_file_path = champion_names_file_path
        self.__champion_names_reader = CSV_FileReader(champion_names_file_path)

    def save_new_champion_names(self, new_names: pd.DataFrame) -> None:
        self.__champion_names_reader.save(new_names)
        return None

    @property
    def champion_names(self) -> pd.DataFrame:
        champion_names = self.__champion_names_reader.load()
        champion_names.columns = champion_names.columns.str.lower()
        return champion_names

    @property
    def champion_names_with_placements(self, number_of_teams: int = 8) -> pd.DataFrame:
        new_names = [f"{champion_name}_{i}" for champion_name in self.champion_names
                     for i in range(1, number_of_teams + 1)]
        return pd.DataFrame(columns=new_names)
