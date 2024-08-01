from dotenv import dotenv_values

from src.arena_pipeline import ArenaPipeline

config = dotenv_values(".env")
DISPLAY_NUMBER = 30
NUMBER_OF_TEAMS = 8
CHAMPION_PLACEMENTS_FILE_PATH = f"champion_placements_team{NUMBER_OF_TEAMS}.csv"
RECORDED_GAMES_FILE_PATH = f"recorded_games_team{NUMBER_OF_TEAMS}.csv"
CHAMPION_ICONS_DIR_PATH = "src/champion_icons"


if __name__ == "__main__":
    arena_pipeline = ArenaPipeline(NUMBER_OF_TEAMS, CHAMPION_PLACEMENTS_FILE_PATH, RECORDED_GAMES_FILE_PATH)
    arena_pipeline.register_config(config)
    # arena_pipeline.save_matches_recent(config["MY_SUMMONER_NAME"], config["MY_TAGLINE"])
    # arena_pipeline.save_matches_recursive()
    arena_pipeline.plot_winrate_graph(DISPLAY_NUMBER, CHAMPION_ICONS_DIR_PATH)
