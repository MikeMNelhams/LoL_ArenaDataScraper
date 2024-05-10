from __future__ import annotations

import random
import time

from src.print_library import print_row

from src.league_library import Champion
from src.lol_api_library import get_puuid_matches, get_player_puuid, parse_match_puuids
from src.champ_placement_writer_factory import champ_placement_writer_factory
from src.pairwise_analysis_library import PairwiseChampionData
import src.pairwise_analysis_print_library as papl

from src.team8.league_stats_library import Match

from riotwatcher import LolWatcher, ApiError


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
        pairwise_data = PairwiseChampionData(pd_data, player_count=self.number_of_teams)
        papl.print_number_of_matches(pairwise_data)
        papl.print_pairwise_stats_best(pairwise_data, display_number)
        champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
        papl.print_champ_stats(champ_input, pairwise_data)
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
        watcher = LolWatcher(self.__config["RIOT_DEV_KEY"])

        if not self.is_config_registered:
            raise UnregisteredConfigurationError(self)

        puuid_seed = get_player_puuid(self.__config["MY_SUMMONER_NAME"], self.__config["MY_TAGLINE"], self.__config["RIOT_DEV_KEY"])
        match_ids = get_puuid_matches(region, puuid_seed, watcher, count=num_matches_to_check_per_player)

        i = 1  # Even though possible not, it's likely the 0th index match is the match you searched by, so start at 1
        player_puuids_checked = {puuid_seed}
        match_ids_to_check = match_ids
        match_ids_checked = set(match_ids_to_check)
        recorded_games = set(self.champion_stats_reader.recorded_games.columns.tolist())
        while i < target_number_of_matches or not match_ids_to_check:
            pop_index = random.randint(0, max(len(match_ids_to_check) - 1, 1))  # Randomised to prevent recency bias
            current_match_id = match_ids_to_check.pop(pop_index)
            match_ids_checked.add(current_match_id)
            try:
                match_detail = watcher.match.by_id(region, current_match_id)
            except ApiError as e:
                print(f"Error occurred for match id: \'{current_match_id}\'")
                print(e)
                print(f"Skipping match id: \'{current_match_id}\'")
                continue

            if match_detail["info"]["gameMode"] != self.ARENA_GAME_MODE_NAME:
                print(f"Incorrect game mode for match #{i}")
                continue
            player_count = len(match_detail["info"]["participants"])
            if player_count != 16:
                print(
                    f"Match with id: \'{current_match_id}\' is a game of arena, but has {player_count} players in it!")
                continue

            time.sleep(3)  # Rate limiting as to not time-out (Max 1 requests per 3 seconds)
            match_puuids = parse_match_puuids(match_detail)
            match = Match.from_game_data(match_detail)

            for puuid in match_puuids:
                if puuid not in player_puuids_checked:
                    print(f"Found new player puuid: \'{puuid}\'. "
                          f"Checking the past {num_matches_to_check_per_player} from their match history.")
                    player_puuids_checked.add(puuid)
                    # Even though possible not, it's likely the 0th index match is the match you searched by, so start at 1
                    player_matches = get_puuid_matches(region, puuid, watcher,
                                                       start=1, count=num_matches_to_check_per_player)
                    time.sleep(6)  # Rate limiting as to not time-out (Max 2 requests per 6 seconds)
                    for match_id in player_matches:
                        if match_id not in match_ids_checked:
                            match_ids_to_check.append(match_id)
                            match_ids_checked.add(match_id)
                    print_row()

            if current_match_id in recorded_games:
                print(f"Match: {match} already saved")
            else:
                print(f"Saving match #{i}: \'{match}\'")
                self.champion_stats_reader.save(match)
                recorded_games.add(current_match_id)
                i += 1

        return None
