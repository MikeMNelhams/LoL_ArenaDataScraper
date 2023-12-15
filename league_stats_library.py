from __future__ import annotations

import itertools

import pandas as pd
import numpy as np


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


class PairwiseChampionData:
    def __init__(self, pairwise_data: pd.DataFrame):
        self.data = pairwise_data

    def __placements(self, champion: Champion) -> pd.DataFrame:
        return self.data.loc[champion.name]

    def __placement_pairwise(self, champion1: Champion, champion2: Champion) -> list[int]:
        placements = self.__placements(champion2)
        return [int(placements[f"{champion1.name}_{i}"]) for i in range(1, 5)]

    def total_matches(self) -> int:
        return self.data.to_numpy().sum() // 8

    def total_placements(self, champion: Champion) -> np.array:
        placements = self.__placements(champion)
        placement_numbers = tuple(np.sum(placements.iloc[i::4].to_numpy()) for i in range(4))
        return np.array(placement_numbers)

    def average_placement(self, champion: Champion) -> float:
        placements = self.total_placements(champion)
        placements = np.array(placements, dtype=np.float)
        num_placements = np.sum(placements)
        placements[1] *= 2
        placements[2] *= 3
        placements[3] *= 4
        if num_placements == 0:
            return 0.0
        return float(sum((placements[0], placements[1], placements[2], placements[3])) / num_placements)

    def __average_placement_with_n(self, champion: Champion) -> (float, int):
        placements = self.total_placements(champion)
        placements = np.array(placements, dtype=np.float)
        num_placements = np.sum(placements)
        placements[1] *= 2
        placements[2] *= 3
        placements[3] *= 4
        if num_placements == 0:
            return 0.0, 0
        return float(sum((placements[0], placements[1], placements[2], placements[3])) / num_placements), num_placements

    def average_placement_by_teammate(self, champion: Champion):
        placements = self.__placements(champion)
        champ_names = self.data.index
        num_champs = self.data.shape[0]

        average_placements_list = [0 for _ in range(num_champs)]

        for i in range(num_champs):
            champ_name = champ_names[i]

            num_firsts = placements[f"{champ_name}_1"]
            num_seconds = placements[f"{champ_name}_2"]
            num_thirds = placements[f"{champ_name}_3"]
            num_fourths = placements[f"{champ_name}_4"]
            total_num_placements = sum((num_firsts, num_seconds, num_thirds, num_fourths))

            if total_num_placements == 0:
                continue

            average_placement = sum((num_firsts, num_seconds*2, num_thirds*3, num_fourths*4)) / total_num_placements
            average_placements_list[i] = average_placement

        return pd.DataFrame([average_placements_list], columns=champ_names, index=pd.Index([champion.name]))

    def average_pairwise_placement(self, champion1: Champion, champion2: Champion) -> float:
        placements = self.__placement_pairwise(champion1, champion2)
        number_of_placements = sum(placements)

        if number_of_placements == 0:
            return 0.0, 0

        for i in range(1, 5):
            placements[i - 1] *= i

        return sum(placements) / number_of_placements

    def __average_pairwise_placement_with_n(self, champion1: Champion, champion2: Champion) -> (float, int):
        placements = self.__placement_pairwise(champion1, champion2)
        number_of_placements = sum(placements)

        if number_of_placements == 0:
            return 0.0, 0

        for i in range(1, 5):
            placements[i - 1] *= i

        return sum(placements) / number_of_placements, number_of_placements

    def pairwise_placements(self, champion1: Champion, champion2: Champion) -> np.array:
        placements = self.__placement_pairwise(champion1, champion2)
        return np.array(placements)

    def best_teammates_for(self, champion: Champion, max_display_number_of_teammates: int = 10) -> pd.DataFrame:
        average_placements = self.average_placement_by_teammate(champion).copy()
        average_placements[average_placements == 0] = np.nan
        sorted_placements = average_placements.sort_values(by=champion.name, axis=1, ascending=True)
        sorted_placements.dropna(axis=1, inplace=True)
        return sorted_placements.iloc[:, :max_display_number_of_teammates]

    def best_champs(self, max_display_number_of_teammates: int = 10) -> pd.DataFrame:
        champion_names = self.data.index
        number_of_champs = champion_names.size
        average_placements = [0.0 for _ in range(number_of_champs)]
        sample_sizes = [0 for _ in range(number_of_champs)]
        index_labels = ["Average placement", "Sample size (n)"]
        for i, champion_name in enumerate(champion_names):
            average_placements[i], sample_sizes[i] = self.__average_placement_with_n(Champion(champion_name))

        top_champions = pd.DataFrame([average_placements, sample_sizes],
                                     columns=champion_names,
                                     index=index_labels)
        sorted_champions = top_champions.sort_values(by=index_labels,
                                                     axis=1,
                                                     ascending=[True, False])
        sorted_champions = sorted_champions.loc[:, (sorted_champions != 0).any(axis=0)]
        return sorted_champions.iloc[:, :max_display_number_of_teammates]

    def best_pairs(self, max_display_number_of_pairs: int = 10) -> pd.DataFrame:
        champion_names = self.data.index
        number_of_champs = champion_names.size
        num_unique_champ_pairs = (number_of_champs * (number_of_champs - 1)) // 2
        average_placements = [0.0 for _ in range(num_unique_champ_pairs)]
        sample_sizes = [0 for _ in range(num_unique_champ_pairs)]
        index_labels = ["Average placement", "Sample size (n)"]

        unique_champ_pairs = list(itertools.combinations(champion_names, 2))

        for i, champ_pair in enumerate(unique_champ_pairs):
            c1 = Champion(champ_pair[0])
            c2 = Champion(champ_pair[1])
            average_placements[i], sample_sizes[i] = self.__average_pairwise_placement_with_n(c1, c2)

        pairwise_champion_names = [f"{pair[0]} + {pair[1]}" for pair in unique_champ_pairs]

        top_champions = pd.DataFrame([average_placements, sample_sizes],
                                     columns=pairwise_champion_names,
                                     index=index_labels)
        sorted_champions = top_champions.loc[:, (top_champions != 0).any(axis=0)]
        sorted_champions = sorted_champions.sort_values(by=index_labels,
                                                        axis=1,
                                                        ascending=[True, False])

        return sorted_champions.iloc[:, :max_display_number_of_pairs]


def parse_match_puuids(match_detail: dict) -> list[str]:
    return match_detail["metadata"]["participants"]


def main():
    print("This is a library file. Do not run as main.")


if __name__ == "__main__":
    main()
