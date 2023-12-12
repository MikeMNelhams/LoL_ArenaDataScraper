from __future__ import annotations

from dotenv import dotenv_values

from league_stats_library import Champion, Match, PairwiseChampionData
from league_stats_file_writers import ChampPlacementWriter
from print_library import colour_print_string_header, print_row

from riotwatcher import LolWatcher

config = dotenv_values(".env")
FILE_PATH = "LoL_ArenaData.json"


def save_recent_matches(summoner_name: str, region: str = "euw1", num_matches: int = 1):
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")

    api_key = config["RIOT_DEV_KEY"]
    watcher = LolWatcher(api_key)
    player_data = watcher.summoner.by_name(region, summoner_name)
    puuid = player_data["puuid"]

    my_matches = watcher.match.matchlist_by_puuid(region, puuid)

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


def get_stats():
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")
    pairwise_data = PairwiseChampionData(champion_stats_reader.load())

    print_best_stats(pairwise_data)
    print_best_champ_pairs(pairwise_data)

    print_row()
    champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))

    print_champ_placement_stats(champ_input, pairwise_data)
    print_champ_average_pairwise_all(champ_input, pairwise_data)
    print_champ_average_pairwise_best(champ_input, pairwise_data)


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


def make_empty():
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")
    champion_stats_reader.make_empty()


def add_new_champ():
    champ_input = Champion(input("CHAMP? ").lower().replace(' ', ''))
    champion_stats_writer = ChampPlacementWriter("champion_placements.csv")
    champion_stats_writer.add_new_champion(champ_input)


if __name__ == '__main__':
    save_recent_matches(config["MY_SUMMONER_NAME"], num_matches=1)
    get_stats()
    # add_new_champ()
