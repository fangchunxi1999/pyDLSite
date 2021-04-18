from typing import Union
from bs4 import BeautifulSoup
import requests

from . import util

BASE_URL = "www.dlsite.com"


class DLSite_Maker:
    def __init__(self, url: str) -> None:
        self.id_prefix = "RG"
        self.id = util.get_id_code(url, self.id_prefix)
        self.id_num = util.get_id_num(url, self.id_prefix)

        self.name = ""

        self.soup_cache = None

    def get_name(self) -> str:
        if not self.name:
            self.name = self.extract_name()
        return self.name

    def extract_name(self) -> str:
        soup = self.get_soup()
        name_soup = soup.find(class_="prof_maker_name")
        name = name_soup.get_text(strip=True) if name_soup else ""
        return name

    def get_content(self) -> bytes:
        url = f"{BASE_URL}/maniax/circle/profile/=/maker_id/{self.id}.html"
        resp = requests.get(url)
        if resp.ok and resp.content:
            return resp.content
        else:
            raise ValueError

    def get_soup(self, content: bytes = None, update: bool = False) -> BeautifulSoup:
        if not (self.soup_cache) or content or update:
            content = content if content else self.get_content()
            self.soup_cache = BeautifulSoup(content, "lxml")
        return self.soup_cache