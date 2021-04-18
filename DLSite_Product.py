from typing import Tuple, Union

import requests
from bs4 import BeautifulSoup

from DLSite_Enum import DLSite_Rate, DLSite_Type
from DLSite_Maker import DLSite_Maker

from . import util

BASE_URL = "www.dlsite.com"


class DLSite_Product:
    def __init__(self, url: str, lazy: bool = True) -> None:
        self.id_prefix = "RJ"
        self.id = util.get_id_code(url, self.id_prefix)
        self.id_num = util.get_id_num(url, self.id_prefix)

        self.name = ""
        self.maker = None

        self.date = None
        self.size = -1
        self.type = DLSite_Type.UNKNOWN
        self.rate = DLSite_Rate.UNKNOWN

        self.description = ""
        self.tags = []
        self.img_links = []
        self.rank = {}
        self.info = {}
        self.update = []

        self.soup_cache = None

    def get_name(self) -> str:
        if not self.name:
            self.name = self.extract_name()
        return self.name

    def extract_name(self) -> str:
        soup = self.get_soup()
        name_soup = soup.find(id="work_name")
        name = name_soup.get_text(strip=True) if name_soup else ""
        return name

    def get_maker(self) -> Union[DLSite_Maker, None]:
        if not self.maker:
            maker_url, maker_name = self.extract_maker()
            if maker_url and maker_name:
                self.maker = DLSite_Maker(maker_url)
                self.maker.name = maker_name
        return self.maker

    def extract_maker(self) -> Tuple[str, str]:
        soup = self.get_soup()
        maker_soup = soup.find(class_="maker_name")
        try:
            maker_url = maker_soup.find("a", href=True)["href"]
        except (AttributeError, KeyError):
            maker_url = ""

        try:
            maker_name = maker_soup.get_text(strip=True)
        except AttributeError:
            maker_name = ""

        return maker_url, maker_name

    def get_maker_name(self) -> str:
        if not self.maker:
            self.maker = self.get_maker()
        return self.maker.name if self.maker else ""

    def get_content(self) -> bytes:
        url = f"{BASE_URL}/maniax/work/=/product_id/{self.id}.html"
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
