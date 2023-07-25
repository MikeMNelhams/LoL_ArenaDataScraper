from abc import ABC, abstractmethod
import json
import os
import pandas as pd


class FileReader(ABC):
    def __init__(self, file_path: str, *args):
        self.file_path = file_path

    @abstractmethod
    def save(self, data) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self):
        raise NotImplementedError


class JSON_FileReader(FileReader):
    def __init__(self, file_path: str):
        super(JSON_FileReader, self).__init__(file_path)

    def save(self, data: dict) -> None:
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return None

    def load(self) -> dict:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data


class CSV_FileReader(FileReader):
    def __init__(self, file_path: str, header_enabled=True):
        super(CSV_FileReader, self).__init__(file_path)
        self._headerEnabled = header_enabled

    def save(self, data: pd.DataFrame) -> None:
        data.to_csv(self.file_path, header=self._headerEnabled)

    def load(self) -> pd.DataFrame:
        if os.stat(self.file_path).st_size == 0:
            return pd.DataFrame()
        return pd.read_csv(self.file_path, sep=',')
