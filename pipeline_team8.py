from dotenv import dotenv_values

from src.arena_pipeline import ArenaPipeline

config = dotenv_values(".env")
DISPLAY_NUMBER = 20
NUMBER_OF_TEAMS = 8
CHAMPION_PLACEMENTS_FILE_NAME = "champion_placements_team8.csv"
RECORDED_GAMES_FILE_NAME = "recorded_games_team8.csv"


if __name__ == "__main__":
    arena_pipeline = ArenaPipeline(NUMBER_OF_TEAMS, CHAMPION_PLACEMENTS_FILE_NAME, RECORDED_GAMES_FILE_NAME)
    arena_pipeline.register_config(config)
    # arena_pipeline.save_matches_recent(config["MY_SUMMONER_NAME"], config["MY_TAGLINE"])
    arena_pipeline.save_matches_recursive()
    # arena_pipeline.get_stats(DISPLAY_NUMBER)
