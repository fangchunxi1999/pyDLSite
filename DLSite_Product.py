from datetime import datetime
from typing import List, Tuple, Union

import requests
from bs4 import BeautifulSoup

from DLSite_Enum import DLSite_Rate, DLSite_Rate_Info, DLSite_Type, DLSite_Type_Info
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

        self.date = datetime.utcfromtimestamp(0)
        self.size = -1
        self.type = DLSite_Type.UNKNOWN
        self.type_keyword = ""
        self.rate = DLSite_Rate.UNKNOWN

        self.description = ""
        self.tags = []
        self.img_links = []
        self.rank = {}
        self.info = {}
        self.update_log = []

        self.soup = None

    def update(self):
        self.soup = self.get_soup(update=True)

        self.name = self.extract_name()
        _maker_url, _maker_name = self.extract_maker()
        self.maker = DLSite_Maker(_maker_url)
        self.maker.name = _maker_name

        self.date = self.extract_date()
        self.size = self.extract_size()
        self.type, self.type_keyword = self.extract_type()
        self.rate = self.extract_rate()

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

    def get_maker_name(self) -> str:
        if not self.maker:
            self.maker = self.get_maker()
        return self.maker.name if self.maker else ""

    def extract_maker(self) -> Tuple[str, str]:
        soup = self.get_soup()
        maker_soup = soup.find(class_="maker_name")
        maker_url = maker_name = ""
        try:
            maker_url = maker_soup.find("a", href=True)["href"]
        except (AttributeError, KeyError):
            pass
        try:
            maker_name = maker_soup.get_text(strip=True)
        except AttributeError:
            pass

        return maker_url, maker_name

    def get_date(self) -> datetime:
        if not self.date:
            self.date = self.extract_date()
        return self.date

    def extract_date(self) -> datetime:
        soup = self.get_soup()
        date_soup = [
            tr.td
            for tr in soup.find(id="work_outline").find_all("tr")
            if tr.th.get_text(strip=True) == "販売日"
        ]
        if date_soup:
            date_str = date_soup[-1].get_text(strip=True)
            if date_str:
                return datetime.strptime(date_str, "%Y年%m月%d日")
        return datetime.utcfromtimestamp(0)

    def get_size(self) -> int:
        if self.size < 0:
            self.size = self.extract_size()
        return self.size

    def extract_size(self) -> int:
        soup = self.get_soup()
        size_soup = [
            tr.td
            for tr in soup.find(id="work_outline").find_all("tr")
            if tr.th.get_text(strip=True) == "ファイル容量"
        ]
        size_str: str = size_soup[-1].get_text(strip=True) if size_soup else ""
        return util.get_byte_humanread_str(size_str)

    def get_type(self, as_keyword: bool = False) -> Union[DLSite_Type, str]:
        if not self.type:
            self.type, self.type_keyword = self.extract_type()
        if as_keyword:
            return self.type_keyword
        return self.type

    def extract_type(self) -> Tuple[DLSite_Type, str]:
        soup = self.get_soup()
        type_soup = [
            tr.td
            for tr in soup.find(id="work_outline").find_all("tr")
            if tr.th.get_text(strip=True) == "作品形式"
        ]
        type_ = DLSite_Type.UNKNOWN
        type_keyword = ""
        if type_soup:
            try:
                type_keyword: str = (
                    type_soup[-1].span["class"][0].split("_")[-1].strip()
                )
            except (KeyError, IndexError, AttributeError):
                return type_, type_keyword

            type_ = DLSite_Type.OTHER
            for ty, info in DLSite_Type_Info.items():
                if type_keyword in info["keyword"]:
                    type_ = ty
                    break
        return type_, type_keyword

    def get_rate(self) -> DLSite_Rate:
        if not self.rate:
            self.rate = self.extract_rate()
        return self.rate

    def extract_rate(self) -> DLSite_Rate:
        soup = self.get_soup()
        rate_soup = [
            tr.td
            for tr in soup.find(id="work_outline").find_all("tr")
            if tr.th.get_text(strip=True) == "年齢指定"
        ]
        rate = DLSite_Rate.UNKNOWN
        if rate_soup:
            try:
                rate_keyword: str = (
                    rate_soup[-1].span["class"][0].split("_")[-1].strip()
                )
            except (KeyError, IndexError, AttributeError):
                return rate

            for rt, info in DLSite_Rate_Info.items():
                if rate_keyword in info["keyword"]:
                    rate = rt
                    break
        return rate

    def get_description(self) -> str:
        return self.description

    def get_tags(self) -> list:
        return self.tags

    def get_img_links(self) -> List[str]:
        return self.img_links

    def get_content(self) -> bytes:
        url = f"{BASE_URL}/maniax/work/=/product_id/{self.id}.html"
        resp = requests.get(url)
        if resp.ok and resp.content:
            return resp.content
        else:
            raise ValueError

    def get_soup(self, content: bytes = None, update: bool = False) -> BeautifulSoup:
        if not (self.soup) or content or update:
            content = content if content else self.get_content()
            self.soup = BeautifulSoup(content, "lxml")
        return self.soup
