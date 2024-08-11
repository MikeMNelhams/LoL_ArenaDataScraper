from __future__ import annotations

import heapq
import random
import time

import seaborn

from src.print_library import print_row

from src.league_library import Champion, Match
from src.lol_api_library import get_puuid_matches, get_player_puuid, parse_match_puuids
from src.champ_placement_writer_factory import champ_placement_writer_factory, ChampPlacementWriter
from src.pairwise_analysis_library import PairwiseChampionData
import src.pairwise_analysis_print_library as papl


from riotwatcher import LolWatcher, ApiError

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


class UnregisteredConfigurationError(Exception):
    def __init__(self, pipeline: ArenaPipeline):
        message = f"No configuration has been registered for pipeline: \'{pipeline}\'"
        super().__init__(message)


class ArenaPipeline:
    ARENA_GAME_MODE_NAME = "CHERRY"

    def __init__(self, number_of_teams: int, champion_placements_file_name: str, recorded_games_file_name: str):
        self.__champ_placements_file_name = champion_placements_file_name
        self.champion_stats_reader = champ_placement_writer_factory(number_of_teams, champion_placements_file_name, recorded_games_file_name)
        self.number_of_teams = number_of_teams
        self.__config: dict = None

    def register_config(self, __config: dict) -> None:
        self.__config = __config
        return None

    @property
    def is_config_registered(self) -> bool:
        return self.__config is not None

    def make_empty(self) -> None:
        self.champion_stats_reader.make_empty()
        return None

    def add_new_champ(self) -> None:
        champ_input = Champion(input("Champion Name? ").lower().replace(' ', ''))
        self.champion_stats_reader.add_new_champion(champ_input)
        return None

    def get_stats(self, display_number: int) -> None:
        pd_data = self.champion_stats_reader.load()
        pairwise_data = PairwiseChampionData(pd_data, team_count=self.number_of_teams)
        papl.print_number_of_matches(pairwise_data)
        papl.print_pairwise_stats_best(pairwise_data, display_number)
        champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
        papl.print_champ_stats(champ_input, pairwise_data, display_number)
        return None

    def save_matches_recent(self, summoner_name: str, player_tagline: str, region: str = "euw1", num_matches: int = 1):
        watcher = LolWatcher(self.__config["RIOT_DEV_KEY"])
        puuid = get_player_puuid(summoner_name, player_tagline, self.__config["RIOT_DEV_KEY"])
        match_ids = get_puuid_matches(region, puuid, watcher, count=num_matches)

        for i in range(num_matches):
            last_match_id = match_ids[i]
            match_detail = watcher.match.by_id(region, last_match_id)
            if match_detail["info"]["gameMode"] != self.ARENA_GAME_MODE_NAME:
                print(f"Incorrect game mode for match {i}")
                return None

            match = Match.from_game_data(match_detail)
            print(match)
            self.champion_stats_reader.save(match)
            print_row()

        return None

    def save_matches_recursive(self, region: str = "euw1", target_number_of_matches: int = 1_000,
                               num_matches_to_check_per_player: int = 10) -> None:
        if not self.is_config_registered:
            raise UnregisteredConfigurationError(self)

        config_copy = self.__config.copy()
        config_copy["ARENA_GAME_MODE_NAME"] = self.ARENA_GAME_MODE_NAME
        config_copy["NUMBER_OF_PLAYERS"] = self.number_of_teams * 2

        match_data_scraper = MatchDataScraper(self.champion_stats_reader, config_copy)
        match_data_scraper.get_recursive(region=region, target_number_of_matches=target_number_of_matches,
                                         num_matches_to_check_per_player=num_matches_to_check_per_player)
        return None

    def plot_winrate_graph(self, display_number: int, champion_icons_dir_path: str) -> None:
        pd_data = self.champion_stats_reader.load()
        pairwise_data = PairwiseChampionData(pd_data, team_count=self.number_of_teams)

        best_champs = pairwise_data.best_champs(display_number)
        ranks = best_champs.iloc[0].tolist()
        sample_sizes = best_champs.iloc[1].tolist()
        champion_names = best_champs.columns.tolist()
        number_of_samples = pairwise_data.total_samples()

        fig, ax = plt.subplots()

        champion_names_labels = [f"{str(round(sample_size, 0))[:-2]} - {champion_name}" + " " * 8
                                 for sample_size, champion_name in zip(sample_sizes, champion_names)]
        ax.scatter(champion_names_labels, ranks, marker='x')
        fig.suptitle(f"Best champions for {self.number_of_teams}-team Arena (Sample size: {number_of_samples})")
        ax.set_ylabel("Average placement")
        ax.tick_params(axis='x', rotation=90)
        y_offset, _ = ax.get_ylim()

        for i, champion_name in enumerate(champion_names):
            icon = plt.imread(f"{champion_icons_dir_path}/{champion_name}.png")
            icon_box = OffsetImage(icon, zoom=.2)
            icon_box.image.axes = ax
            position = [i, y_offset]
            ab = AnnotationBbox(icon_box,
                                position,
                                frameon=False,
                                box_alignment=(0.5, 1.2)
                                )
            ax.add_artist(ab)

        ax.set_xlabel("Champion (Sample sizes below)")
        fig.tight_layout()
        fig.set_size_inches(11.5, 5.5)
        fig.savefig(f"{display_number} best champions in arena{self.number_of_teams}.png")
        plt.show()
        return None

    def plot_champion_confusion_matrix(self, display_number: int, champion_icons_dir_path: str) -> None:
        pd_data = self.champion_stats_reader.load()
        pairwise_data = PairwiseChampionData(pd_data, team_count=self.number_of_teams)
        pairwise_data.data.drop(columns=["champion_names"], inplace=True)
        print(f"Number of samples: {pairwise_data.total_samples()}")

        number_of_champs = pairwise_data.data.shape[0]
        # This should be a weighted sum AVERAGE (arithmetic mean)
        weights = np.array(list(range(1, 9)))
        columns = tuple(np.dot(pairwise_data.data.iloc[:, i * self.number_of_teams: (i + 1) * self.number_of_teams].to_numpy(), weights) / np.maximum(np.sum(pairwise_data.data.iloc[:, i * self.number_of_teams: (i + 1) * self.number_of_teams].to_numpy(), axis=1), 1) for i in range(number_of_champs))

        champion_names_all = self.champion_stats_reader.champion_names.columns
        sorted_placements = tuple(sorted(((np.mean(x), i, champion_names_all[i]) for i, x in enumerate(columns))))
        print(sorted_placements)
        best_column_indices = {sorted_placements[i][1] for i in range(display_number) if sorted_placements[i][1] != 0}

        champion_names = champion_names_all.tolist()
        best_champion_names = [name for i, name in enumerate(champion_names) if i in best_column_indices]

        x = np.column_stack(tuple(columns[i] for i in range(len(columns)) if i in best_column_indices))
        x = np.triu([row for i, row in enumerate(x) if i in best_column_indices])

        x_masked = np.logical_not(np.bool8(x))

        ax = seaborn.heatmap(x, mask=x_masked, linewidths=0.5, xticklabels=best_champion_names, yticklabels=best_champion_names, annot=True, cmap="crest")
        ax.set_ylabel("Champion 1")
        ax.set_xlabel("Champion 2")
        ax.set_title("Best champion pairwise average winrates matrix")
        plt.show()


class MatchDataScraper:

    def __init__(self, champion_stats_reader: ChampPlacementWriter, config: dict[str, str]):
        self.__config = config
        self.champion_stats_reader = champion_stats_reader
        self.ARENA_GAME_MODE_NAME = config["ARENA_GAME_MODE_NAME"]
        self.watcher = LolWatcher(self.__config["RIOT_DEV_KEY"])

        self.matches: dict[str, Match] = {}

        self.match_ids_to_request = set()

        self.match_ids_to_save = set()
        self.match_ids_saved = set(self.champion_stats_reader.recorded_games.columns.tolist())
        self.match_ids_invalid_type = set()

        self.match_ids_to_check_for_players = set()
        self.match_ids_checked_for_players = set()

        self.player_ids_to_check_for_matches = set()
        self.player_ids_checked_for_matches = set()

    def get_recursive(self, region: str, target_number_of_matches: int, num_matches_to_check_per_player: int,
                      thread_limit: int=5) -> None:

        puuid_seed = get_player_puuid(self.__config["MY_SUMMONER_NAME"], self.__config["MY_TAGLINE"],
                                      self.__config["RIOT_DEV_KEY"])

        self.player_ids_to_check_for_matches.add(puuid_seed)
        rate_limit_delay = 1 / 3

        i = 0
        max_iterations = 100_000
        c = 0
        while i < target_number_of_matches or c >= max_iterations:
            while self.match_ids_to_save:
                c += 1
                # Randomised to prevent recency bias
                match_id = self.match_ids_to_save.pop()

                if match_id not in self.matches:
                    if not self.__add_match(match_id, region, rate_limit_delay):
                        continue

                if match_id in self.match_ids_invalid_type:
                    print(f"Invalid match details for match_id: {match_id}")
                    continue

                match = Match.from_game_data(self.matches[match_id])

                if match_id in self.match_ids_saved:
                    print(f"Match: {match} already saved")
                    continue

                print(f"Saving match #{i}: \'{match}\'. Number of matches recorded: {len(self.match_ids_saved) + 1}")
                print_row()
                self.champion_stats_reader.save(match)
                self.match_ids_saved.add(match_id)
                del self.matches[match_id]
                i += 1

            while not self.match_ids_to_save and (self.player_ids_to_check_for_matches or self.match_ids_to_check_for_players):
                c += 1
                if self.player_ids_to_check_for_matches:
                    player_id = self.player_ids_to_check_for_matches.pop()
                    if player_id in self.player_ids_checked_for_matches:
                        continue

                    print(f"Found new player puuid: \'{player_id}\'. checking the past {num_matches_to_check_per_player} from their match history.")
                    self.player_ids_checked_for_matches.add(player_id)
                    time.sleep(rate_limit_delay)  # Rate limiting as to not time-out (Max 5 requests per 3 seconds)
                    match_ids = set(get_puuid_matches(region, player_id, self.watcher, start=1,
                                                       count=num_matches_to_check_per_player))
                    self.match_ids_to_save |= match_ids - self.match_ids_saved
                    self.match_ids_to_check_for_players |= match_ids - self.match_ids_checked_for_players

                else:
                    match_id = self.match_ids_to_check_for_players.pop()
                    if match_id in self.match_ids_checked_for_players:
                        continue
                    if match_id in self.match_ids_invalid_type:
                        continue

                    print(f"Checking for new players in match with id: {match_id}")
                    if match_id not in self.matches:
                        if not self.__add_match(match_id, region, rate_limit_delay):
                            continue
                    self.__add_player_ids_in_match(match_id)

                print_row()

            if not self.player_ids_to_check_for_matches and not self.match_ids_to_check_for_players:
                raise SystemExit("No more matches or players could be found. Try a new seed player puuid.")

    def __is_valid_match_detail(self, match_detail: dict) -> bool:
        if match_detail["info"]["gameMode"] != self.ARENA_GAME_MODE_NAME:
            return False

        player_count = len(match_detail["info"]["participants"])
        if player_count != self.__config["NUMBER_OF_PLAYERS"]:
            return False
        return True

    def __save_match(self, match: Match) -> None:
        self.champion_stats_reader.save(match)
        return None

    def __add_match(self, match_id: str, region: str, rate_limit_delay: float= 1 / 3) -> bool:
        time.sleep(rate_limit_delay)  # Rate limiting as to not time-out (Max 5 requests per 3 seconds)
        try:
            match_detail = self.watcher.match.by_id(region, match_id)
        except ApiError as e:
            print(f"Error occurred for match id: \'{match_id}\'")
            print(e)
            print(f"Skipping match id: \'{match_id}\'")
            return False

        if match_detail is None:
            return False

        if self.__is_valid_match_detail(match_detail):
            self.matches[match_id] = match_detail
        else:
            self.match_ids_invalid_type.add(match_id)

        return True

    def __add_player_ids_in_match(self, match_id: str) -> None:
        self.match_ids_checked_for_players.add(match_id)

        match_puuids = set(parse_match_puuids(self.matches[match_id]))
        valid_player_ids = match_puuids - self.player_ids_checked_for_matches
        print(f"Found {len(valid_player_ids)} valid NEW player ids")
        self.player_ids_to_check_for_matches |= valid_player_ids
        print(f"Number of player ids to check for matches: {len(self.player_ids_to_check_for_matches)}")
        return True
