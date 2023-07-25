from __future__ import annotations

from dotenv import dotenv_values

from league_stats_library import Champion, Match, PairwiseChampionData
from league_stats_file_writers import ChampPlacementWriter

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
        print('-' * 30)

    return None


def get_stats():
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")

    pairwise_data = PairwiseChampionData(champion_stats_reader.load())

    print("Best overall stats:")
    best_stats = pairwise_data.best_champs()
    print(best_stats.to_string())
    print('\n')
    print("Best champ pairs:")
    best_pairs = pairwise_data.best_pairs()
    print(best_pairs.to_string())
    print('-' * 30)
    champ_me = Champion(input("CHAMP? ").lower())

    placements_swain = pairwise_data.total_placements(champ_me)
    placement_average_swain = pairwise_data.average_placement(champ_me)

    print(champ_me, "placement statistics")
    print(placements_swain)
    print(placement_average_swain)
    print('-' * 30)

    print(f"Average placements by champ for {champ_me}")
    print(pairwise_data.average_placement_by_teammate(champ_me).to_string())
    print('-' * 30)

    print(f"Best average placements by champ for {champ_me}")
    print(pairwise_data.best_teammates_for(champ_me).to_string())
    print('-' * 30)


def make_empty():
    champion_stats_reader = ChampPlacementWriter("champion_placements.csv")
    champion_stats_reader.make_empty()


if __name__ == '__main__':
    save_recent_matches(1)
    get_stats(config["MY_SUMMONER_NAME"])
