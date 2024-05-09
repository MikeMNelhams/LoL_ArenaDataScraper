from typing import Callable

import requests


from riotwatcher import ApiError


def get_puuid_matches(region, puuid, watcher, start: int=0, count: int=20):
    matches = []
    try:
        matches = watcher.match.matchlist_by_puuid(region, puuid, start=start, count=count)
    except ApiError as e:
        print("Most likely the RIOT_DEV_KEY is expired or invalid.")
        raise e

    return matches


def get_player_puuid(game_name: str, tag_line: str, api_key_generator: Callable[[], str], region: str = "europe") -> str:
    request_url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={api_key_generator()}"
    response = requests.get(request_url)
    data = response.json()
    if "puuid" not in data:
        raise KeyError("Bad response from server. " + response)
    return data["puuid"]


def parse_match_puuids(match_detail: dict) -> list[str]:
    return match_detail["metadata"]["participants"]
