from __future__ import annotations

import random
import time

from dotenv import dotenv_values

from src.league_library import Champion
from src.team4.league_stats_library import Match
from src.pairwise_analysis_library import PairwiseChampionData
from src.team4.league_stats_file_writers import ChampPlacementWriter
from src.lol_api_library import get_player_puuid, get_puuid_matches, parse_match_puuids
from src.print_library import colour_print_string_header, print_row

from riotwatcher import LolWatcher

config = dotenv_values(".env")
ARENA_GAME_MODE_NAME = "CHERRY"
DISPLAY_NUMBER = 20


def read_api_key() -> str:
    return config["RIOT_DEV_KEY"]


def save_recent_matches(summoner_name: str, player_tagline: str, region: str = "euw1", num_matches: int = 1):
    champion_stats_reader = ChampPlacementWriter("champion_placements_team4.csv")
    watcher = LolWatcher(read_api_key())

    puuid = get_player_puuid(summoner_name, player_tagline, read_api_key)
    match_ids = get_puuid_matches(region, puuid, watcher, count=num_matches)

    for i in range(num_matches):
        last_match_Id = match_ids[i]
        match_detail = watcher.match.by_id(region, last_match_Id)
        if match_detail["info"]["gameMode"] != ARENA_GAME_MODE_NAME:
            print(f"Incorrect game mode for match {i}")
            return None

        match = Match.from_game_data(match_detail)
        print(match)
        champion_stats_reader.save(match)
        print_row()

    return None


def print_best_stats(pairwise_data: PairwiseChampionData) -> None:
    print(colour_print_string_header("Best overall stats:"))
    best_stats = pairwise_data.best_champs(DISPLAY_NUMBER)
    print(best_stats.to_string())
    return None


def print_best_champ_pairs(pairwise_data: PairwiseChampionData) -> None:
    print(f"\n{colour_print_string_header('Best champ pairs:')}")
    best_pairs = pairwise_data.best_pairs(DISPLAY_NUMBER)
    print(best_pairs.to_string())
    return None


def print_champ_stats(champ_input: Champion, pairwise_data: PairwiseChampionData) -> None:
    print_champ_placement_stats(champ_input, pairwise_data)
    print_champ_average_pairwise_all(champ_input, pairwise_data)
    print_champ_average_pairwise_best(champ_input, pairwise_data)
    return None


def print_pairwise_stats_best(pairwise_data: PairwiseChampionData) -> None:
    print_best_stats(pairwise_data)
    print_best_champ_pairs(pairwise_data)
    print_row()
    return None


def print_champ_average_pairwise_best(champ_input: Champion, pairwise_data: PairwiseChampionData) -> None:
    print(colour_print_string_header(f"Best average placements by champ for \'{champ_input}\'"))
    print(pairwise_data.best_teammates_for(champ_input).to_string())
    print_row()
    return None


def print_champ_average_pairwise_all(champ_input: Champion, pairwise_data: PairwiseChampionData) -> None:
    print(colour_print_string_header(f"Average placements by champ for \'{champ_input}\'"))
    print(pairwise_data.average_placement_by_teammate(champ_input).to_string())
    return None


def print_champ_placement_stats(champ_input: Champion, pairwise_data: PairwiseChampionData) -> None:
    placements = pairwise_data.total_placements(champ_input)
    placement_average = pairwise_data.average_placement(champ_input)
    print(colour_print_string_header(f"Placement Statistics for: \'{champ_input}\'"))
    print(placements)
    print(placement_average)
    print_row()
    return None


def print_number_of_matches(pairwise_data: PairwiseChampionData) -> None:
    print(f"Total number of matches recorded: {pairwise_data.total_matches()}")
    print_row()
    return None


def get_stats() -> None:
    champion_stats_reader = ChampPlacementWriter("champion_placements_team4.csv")
    pairwise_data = PairwiseChampionData(champion_stats_reader.load())

    print_number_of_matches(pairwise_data)
    print_pairwise_stats_best(pairwise_data)
    champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
    print_champ_stats(champ_input, pairwise_data)
    return None


def make_empty() -> None:
    champion_stats_reader = ChampPlacementWriter("champion_placements_team4.csv")
    champion_stats_reader.make_empty()
    return None


def add_new_champ() -> None:
    champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
    champion_stats_writer = ChampPlacementWriter("champion_placements_team4.csv")
    champion_stats_writer.add_new_champion(champ_input)
    return None


def save_matches_recursive(summoner_name_seed: str, tagline_seed: str, region: str = "euw1", target_number_of_matches: int=1_000,
                           num_matches_to_check_per_player: int=10) -> None:
    champion_stats_reader = ChampPlacementWriter("champion_placements_team4.csv")

    watcher = LolWatcher(read_api_key())

    puuid_seed = get_player_puuid(summoner_name_seed, tagline_seed, read_api_key)
    match_ids = get_puuid_matches(region, puuid_seed, watcher, count=num_matches_to_check_per_player)

    i = 1
    player_puuids_checked = {puuid_seed}
    match_ids_to_check = match_ids
    match_ids_checked = set(match_ids_to_check)
    recorded_games = set(champion_stats_reader.recorded_games.columns.tolist())
    while i < target_number_of_matches or not match_ids_to_check:
        pop_index = random.randint(0, max(len(match_ids_to_check) - 1, 1))  # Randomised to prevent recency bias
        current_match_id = match_ids_to_check.pop(pop_index)
        match_ids_checked.add(current_match_id)
        match_detail = watcher.match.by_id(region, current_match_id)

        if match_detail["info"]["gameMode"] != ARENA_GAME_MODE_NAME:
            print(f"Incorrect game mode for match {i}")
            continue

        time.sleep(3)  # Rate limiting as to not time-out (Max 1 requests per 3 seconds)
        match_puuids = parse_match_puuids(match_detail)
        match = Match.from_game_data(match_detail)

        for puuid in match_puuids:
            if puuid not in player_puuids_checked:
                print(f"Found new player puuid: \'{puuid}\'")
                player_puuids_checked.add(puuid)
                # Even though possible not, it's likely the 0th index match is the match you searched by.
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
            champion_stats_reader.save(match)
            recorded_games.add(current_match_id)
            i += 1

    return None


def main():
    # save_recent_matches(config["MY_SUMMONER_NAME"], config["MY_TAGLINE"])
    # save_matches_recursive(config["MY_SUMMONER_NAME"], config["MY_TAGLINE"])
    get_stats()

    # add_new_champ()


if __name__ == '__main__':
    main()
