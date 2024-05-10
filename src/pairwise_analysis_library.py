import itertools

import pandas as pd
import numpy as np


from src.league_library import Champion


class PairwiseChampionData:
    def __init__(self, pairwise_data: pd.DataFrame, player_count: int = 4):
        self.data = pairwise_data
        self.player_count = player_count

    def __placements(self, champion: Champion) -> pd.DataFrame:
        return self.data.loc[champion.name]

    def __placement_pairwise(self, champion1: Champion, champion2: Champion) -> list[int]:
        placements = self.__placements(champion2)
        return [int(placements[f"{champion1.name}_{i}"]) for i in range(1, self.player_count + 1)]

    def total_matches(self) -> int:
        return self.data.to_numpy().sum() // self.player_count

    def total_placements(self, champion: Champion) -> np.array:
        placements = self.__placements(champion)
        placement_numbers = tuple(np.sum(placements.iloc[i::self.player_count].to_numpy()) for i in range(self.player_count))
        return np.array(placement_numbers)

    def average_placement(self, champion: Champion) -> float:
        average_placement, _ = self.__average_placement_with_n(champion)
        return average_placement

    def __average_placement_with_n(self, champion: Champion) -> (float, int):
        placements = self.total_placements(champion)
        placements = np.array(placements, dtype=np.float32)
        num_placements = np.sum(placements)

        for i in range(1, self.player_count):
            placements[i] *= i + 1
        if num_placements == 0:
            return 0.0, 0
        return float(sum(placements) / num_placements), num_placements

    def average_placement_by_teammate(self, champion: Champion) -> pd.DataFrame:
        placements = self.__placements(champion)
        champ_names = self.data.index
        num_champs = self.data.shape[0]

        average_placements_list = [0 for _ in range(num_champs)]
        sample_sizes = [0 for _ in range(num_champs)]

        for i in range(num_champs):
            champ_name = champ_names[i]

            placement_counts = tuple(placements[f"{champ_name}_{j}"] for j in range(1, self.player_count + 1))
            total_num_placements = sum(placement_counts)
            sample_sizes[i] = total_num_placements
            if total_num_placements == 0:
                continue

            average_placement = sum(placement * j for j, placement in enumerate(placement_counts, 1)) / total_num_placements
            average_placements_list[i] = average_placement

        index_labels = [f"Average placement for \'{champion.name}\'", "Sample size (n)"]

        return pd.DataFrame([average_placements_list, sample_sizes], columns=champ_names, index=pd.Index(index_labels))

    def average_pairwise_placement(self, champion1: Champion, champion2: Champion) -> float:
        placements = self.__placement_pairwise(champion1, champion2)
        number_of_placements = sum(placements)

        if number_of_placements == 0:
            return 0.0, 0

        for i in range(1, self.player_count + 1):
            placements[i - 1] *= i

        return sum(placements) / number_of_placements

    def __average_pairwise_placement_with_n(self, champion1: Champion, champion2: Champion) -> (float, int):
        placements = self.__placement_pairwise(champion1, champion2)
        number_of_placements = sum(placements)

        if number_of_placements == 0:
            return 0.0, 0

        for i in range(1, self.player_count + 1):
            placements[i - 1] *= i

        return sum(placements) / number_of_placements, number_of_placements

    def pairwise_placements(self, champion1: Champion, champion2: Champion) -> np.array:
        return np.array(self.__placement_pairwise(champion1, champion2))

    def best_teammates_for(self, champion: Champion, max_display_number_of_teammates: int = 10) -> pd.DataFrame:
        average_placements = self.average_placement_by_teammate(champion).copy()
        average_placements[average_placements == 0] = np.nan
        sorted_placements = average_placements.sort_values(by=average_placements.index.tolist(), axis=1, ascending=[True, False])
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
