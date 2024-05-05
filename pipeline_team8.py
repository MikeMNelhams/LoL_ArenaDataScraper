from __future__ import annotations

from dotenv import dotenv_values

from riotwatcher import LolWatcher

from src.team8.league_stats_library import Match
from src.lol_api_library import get_puuid_matches, get_player_puuid

config = dotenv_values(".env")
ARENA_GAME_MODE_NAME = "CHERRY"


def read_api_key() -> str:
    return config["RIOT_DEV_KEY"]


def get_recent_matches(summoner_name: str, player_tagline: str, region: str = "euw1", num_matches: int = 1):
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

    return None


if __name__ == "__main__":
    get_recent_matches(config["MY_SUMMONER_NAME"], config["MY_TAGLINE"])
