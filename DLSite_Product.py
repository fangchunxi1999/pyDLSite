from datetime import datetime
from typing import List, Tuple, Union

import requests
from bs4 import BeautifulSoup

from DLSite_Enum import DLSite_Rate, DLSite_Rate_Info, DLSite_Type, DLSite_Type_Info
from DLSite_Maker import DLSite_Maker

import util

BASE_URL = "www.dlsite.com"


class DLSite_Product:
    def __init__(self, url: str, lazy: bool = False) -> None:
        self.id_prefix = "RJ"
        self.id = util.get_id_code(url, self.id_prefix)
        self.id_num = util.get_id_num(url, self.id_prefix)

        self._name = ""
        self._maker = None

        self._date = datetime.utcfromtimestamp(0)
        self._size = -1
        self._type = (DLSite_Type.UNKNOWN, "")
        self._rate = DLSite_Rate.UNKNOWN

        self._description = ""
        self._tags = []
        self._img_links = []
        self._rank = {}
        self._info = {}
        self._update_log = []

        self.soup = None

        if not lazy:
            self.update()

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

    @property  # of self.name
    def name(self) -> str:
        if not self._name:
            self._name = self.extract_name()
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def extract_name(self) -> str:
        soup = self.get_soup()
        name_soup = soup.find(id="work_name")
        name = name_soup.get_text(strip=True) if name_soup else ""
        return name

    @property  # of self.maker
    def maker(self) -> Union[DLSite_Maker, None]:
        if not self._maker:
            maker_url, maker_name = self.extract_maker()
            if maker_url and maker_name:
                self._maker = DLSite_Maker(maker_url)
                self._maker.name = maker_name
        return self._maker

    @maker.setter
    def maker(self, maker: DLSite_Maker):
        self._maker = maker

    def get_maker_name(self) -> str:
        return self.maker.get_name() if self.maker else ""

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

    @property  # of self.date
    def date(self) -> datetime:
        if not self._date:
            self._date = self.extract_date()
        return self._date

    @date.setter
    def date(self, date: datetime):
        self._date = date

    def extract_date(self) -> datetime:
        soup = self.get_soup()
        date_soup = self._get_select_work_outline_soup(soup, "販売日")
        date_str = date_soup.get_text(strip=True) if date_soup else ""
        if date_str:
            return datetime.strptime(date_str, "%Y年%m月%d日")
        return datetime.utcfromtimestamp(0)

    @property  # of self.size
    def size(self) -> int:
        if self._size < 0:
            self._size = self.extract_size()
        return self._size

    @size.setter
    def size(self, size: int):
        self._size = size

    def extract_size(self) -> int:
        soup = self.get_soup()
        size_soup = self._get_select_work_outline_soup(soup, "ファイル容量")
        size_str: str = size_soup.get_text(strip=True) if size_soup else ""
        return util.get_byte_humanread_str(size_str)

    @property  # of self.product_type
    def product_type(self) -> DLSite_Type:
        if self._type[0] == DLSite_Type.UNKNOWN:
            self._type = self.extract_type()
        return self._type[0]

    @product_type.setter
    def product_type(self, product_type: DLSite_Type):
        self._type = (
            product_type,
            str(list(DLSite_Type_Info[product_type]["keyword"].gets())[0]),
        )

    @property  # of self.product_type_keyword
    def product_type_keyword(self) -> str:
        if not self._type[1]:
            self._type = self.extract_type()
        return self._type[1]

    @product_type_keyword.setter
    def product_type_keyword(self, product_type_keyword: str):
        self._type = self._extract_type(product_type_keyword)

    def extract_type(self) -> Tuple[DLSite_Type, str]:
        soup = self.get_soup()
        type_soup = self._get_select_work_outline_soup(soup, "作品形式")
        type_ = DLSite_Type.UNKNOWN
        type_keyword = ""
        if type_soup:
            try:
                type_keyword: str = type_soup.span["class"][0].split("_")[-1].strip()
            except (KeyError, IndexError, AttributeError):
                return type_, type_keyword
            type_, type_keyword = self._extract_type(type_keyword)
        return type_, type_keyword

    def _extract_type(self, type_keyword: str) -> Tuple[DLSite_Type, str]:
        type_ = DLSite_Type.OTHER
        for ty, info in DLSite_Type_Info.items():
            if type_keyword.upper() in info["keyword"]:
                type_ = ty
                break
        return type_, type_keyword.upper()

    @property  # of rate
    def rate(self) -> DLSite_Rate:
        if self._rate == DLSite_Rate.UNKNOWN:
            self._rate = self.extract_rate()
        return self._rate

    @rate.setter
    def rate(self, rate: DLSite_Rate):
        self._rate = rate

    def extract_rate(self) -> DLSite_Rate:
        soup = self.get_soup()
        rate_soup = self._get_select_work_outline_soup(soup, "年齢指定")
        rate = DLSite_Rate.UNKNOWN
        if rate_soup:
            try:
                rate_keyword: str = rate_soup.span["class"][0].split("_")[-1].strip()
            except (KeyError, IndexError, AttributeError):
                return rate

            for rt, info in DLSite_Rate_Info.items():
                if rate_keyword in info["keyword"]:
                    rate = rt
                    break
        return rate

    # TODO
    @property  # of description
    def description(self) -> str:
        return self._description

    @property  # of tags
    def tags(self) -> list:
        return self._tags

    def extract_tags(self):
        soup = self.get_soup()
        tags_soup = self._get_select_work_outline_soup(soup, "ジャンル")

    @property  # of img_links
    def img_links(self) -> List[str]:
        return self._img_links

    @property  # of rank
    def rank(self):
        return self._rank

    @property  # of info
    def info(self):
        return self._info

    @property  # of update_log
    def update_log(self):
        return self._update_log

    def get_content(self) -> bytes:
        url = f"https://{BASE_URL}/maniax/work/=/product_id/{self.id}"
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

    def _get_select_work_outline_soup(
        self, soup: BeautifulSoup, select_keyword: str
    ) -> Union[BeautifulSoup, None]:
        select_soup = None
        for tr in soup.find(id="work_outline").find_all("tr"):
            if tr.th.get_text(strip=True) == select_keyword:
                select_soup = tr.td
        return select_soup
