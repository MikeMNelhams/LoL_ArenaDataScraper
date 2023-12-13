from __future__ import annotations

import random
import time

from dotenv import dotenv_values

from league_stats_library import Champion, Match, PairwiseChampionData, parse_match_puuids
from league_stats_file_writers import ChampPlacementWriter
from print_library import colour_print_string_header, print_row

from riotwatcher import LolWatcher

config = dotenv_values(".env")
FILE_PATH = "LoL_ArenaData.json"


def read_api_key() -> str:
    return config["RIOT_DEV_KEY"]


def get_summoners_matches(region, summoner_name, watcher, start: int=0, count: int=20):
    player_data = watcher.summoner.by_name(region, summoner_name)
    puuid = player_data["puuid"]
    return get_puuid_matches(region, puuid, watcher, start=start, count=count)


def get_puuid_matches(region, puuid, watcher, start: int=0, count: int=20):
    my_matches = watcher.match.matchlist_by_puuid(region, puuid, start=start, count=count)
    return my_matches


def save_recent_matches(summoner_name: str, region: str = "euw1", num_matches: int = 1):
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")

    watcher = LolWatcher(read_api_key())

    my_matches = get_summoners_matches(region, summoner_name, watcher)

    for i in range(num_matches):
        last_match_Id = my_matches[i]
        match_detail = watcher.match.by_id(region, last_match_Id)
        if match_detail["info"]["gameMode"] != "CHERRY":
            print(f"Incorrect game mode for match {i}")
            return None

        match = Match.from_game_data(match_detail)
        print(match)
        champion_stats_reader.save(match)
        print_row()

    return None


def print_best_stats(pairwise_data: PairwiseChampionData) -> None:
    print(colour_print_string_header("Best overall stats:"))
    best_stats = pairwise_data.best_champs()
    print(best_stats.to_string())
    return None


def print_best_champ_pairs(pairwise_data: PairwiseChampionData) -> None:
    print(f"\n{colour_print_string_header('Best champ pairs:')}")
    best_pairs = pairwise_data.best_pairs()
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
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")
    pairwise_data = PairwiseChampionData(champion_stats_reader.load())

    print_number_of_matches(pairwise_data)
    print_pairwise_stats_best(pairwise_data)
    champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
    print_champ_stats(champ_input, pairwise_data)
    return None


def make_empty() -> None:
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")
    champion_stats_reader.make_empty()
    return None


def add_new_champ() -> None:
    champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
    champion_stats_writer = ChampPlacementWriter("champion_placements.csv")
    champion_stats_writer.add_new_champion(champ_input)
    return None


def save_matches_recursive(summoner_name_seed: str, region: str = "euw1", target_number_of_matches: int=100,
                           num_matches_to_check_per_player: int=10) -> None:
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")

    watcher = LolWatcher(read_api_key())

    my_match_ids = get_summoners_matches(region, summoner_name_seed, watcher, count=num_matches_to_check_per_player)
    my_puuid = watcher.summoner.by_name(region, summoner_name_seed)["puuid"]

    i = 1
    player_puuids_checked = {my_puuid}
    match_ids_to_check = my_match_ids
    match_ids_checked = set(match_ids_to_check)
    recorded_games = set(champion_stats_reader.recorded_games.columns.tolist())
    while i < target_number_of_matches or not match_ids_to_check:
        pop_index = random.randint(0, max(len(match_ids_to_check) - 1, 1))  # Randomised to prevent recency bias
        current_match_id = match_ids_to_check.pop(pop_index)
        match_ids_checked.add(current_match_id)
        match_detail = watcher.match.by_id(region, current_match_id)

        if match_detail["info"]["gameMode"] != "CHERRY":
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
            print(match_detail)
            champion_stats_reader.save(match)
            recorded_games.add(current_match_id)
            i += 1

    return None


if __name__ == '__main__':
    # save_recent_matches(config["MY_SUMMONER_NAME"])
    # get_stats()

    save_matches_recursive(config["MY_SUMMONER_NAME"])

    # add_new_champ()
