# The website allows all public requests for scraping the champion icons.

import requests
import shutil
import json
import bs4


def main():

    icon_root_url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/"
    save_dir_path = "champion_icons"

    for i in range(1000):
        icon_url = f"{icon_root_url}/{i}.png"
        response = requests.get(icon_url, stream=True)
        if response.status_code != 200:
            continue
        print(f"Saving champion icon #{i+1}")
        save_path = f"{save_dir_path}/{i}.png"
        with open(save_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response


if __name__ == "__main__":
    main()
