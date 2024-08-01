import requests
from requests import Response
import shutil
from threading import Thread, local
from queue import Queue
from contextlib import ExitStack


class GroupURLs:
    def __init__(self, icon_url: str, champion_details_url: str):
        self.icon_url = icon_url
        self.champion_details_url = champion_details_url


def attempt_to_save(responses: list[Response], save_dir_path: str) -> None:
    if any(response.status_code != 200 for response in responses):
        return
    champion_details = responses[1].json()
    if "name" not in champion_details:
        return

    champion_name = champion_details["name"].replace('.', '').replace('\'', '').replace(' ', '').lower()
    save_path = f"{save_dir_path}/{champion_name}.png"
    print(f"Saving champion icon for {champion_name}...")

    with open(save_path, 'wb') as out_file:
        shutil.copyfileobj(responses[0].raw, out_file)

    return None


def download_link(queue: Queue, save_dir_path: str, thread_local: local) -> None:
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    session = thread_local.session
    while True:
        groupURLs = queue.get()

        with ExitStack() as stack:
            responses = [stack.enter_context(session.get(groupURLs.icon_url, stream=True)),
                         stack.enter_context(session.get(groupURLs.champion_details_url))]
            try:
                attempt_to_save(responses, save_dir_path)
            except Exception as e:
                print(e)
                raise ZeroDivisionError

        queue.task_done()


def download_all(queue: Queue, save_dir_path: str, thread_local: local, thread_count: int=10) -> None:
    def download() -> None:
        download_link(queue, save_dir_path, thread_local)

    for i in range(thread_count):
        thread_worker = Thread(target=download)
        thread_worker.daemon = True
        thread_worker.start()
    queue.join()

    return None


def main():
    # The website allows all public requests for scraping the champion icons.
    icon_root_url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/"
    champion_details_root_url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champions/"
    save_dir_path = "champion_icons"

    max_champ_id = 1_000

    queue = Queue()

    for i in range(max_champ_id):
        urls = GroupURLs(f"{icon_root_url}/{i}.png", f"{champion_details_root_url}/{i}.json")
        queue.put(urls)

    thread_local = local()

    download_all(queue, save_dir_path, thread_local, thread_count=5)


if __name__ == "__main__":
    main()
