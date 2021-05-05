import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

import requests
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify

import util
from DLSite_Enum import DLSite_Rate, DLSite_Rate_Info, DLSite_Type, DLSite_Type_Info
from DLSite_Maker import DLSite_Maker

BASE_URL = "https://www.dlsite.com"


class DLSite_Product:
    def __init__(self, url: str, lazy: bool = False) -> None:
        self.id_prefix = "RJ"
        self.id = util.get_id_code(url, self.id_prefix)
        self.id_num = util.get_id_num(url, self.id_prefix)

        self._name = ""
        self._maker = None

        self._date = None
        self._size = -1
        self._type = DLSite_Type.UNKNOWN
        self._type_kw = ""
        self._rate = DLSite_Rate.UNKNOWN

        self._description = ""
        self._tags = []
        self._img_links = []
        self._rank = {}
        self._info = {}
        self._update_logs = []

        self._soup = None
        self._product_rest = {}

        if not lazy:
            self.update()

    def update(self):
        self._soup = self.get_soup(update=True)

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

    @property
    def maker_name(self) -> str:
        return self.get_maker_name()

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
            year, month, day = re.match(r"(\d{4})年(\d{2})月(\d{2})日", date_str).groups()
            return datetime(year=int(year), month=int(month or 1), day=int(day or 1))
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
        if self._type == DLSite_Type.UNKNOWN:
            self._type, self._type_kw = self.extract_type()
        return self._type

    @product_type.setter
    def product_type(self, product_type: DLSite_Type):
        self._type, self._type_kw = (
            product_type,
            str(list(DLSite_Type_Info[product_type]["keyword"].gets())[0]),
        )

    @property  # of self.product_type_keyword
    def product_type_keyword(self) -> str:
        if not self._type:
            self._type, self._type_kw = self.extract_type()
        return self._type_kw

    @product_type_keyword.setter
    def product_type_keyword(self, product_type_keyword: str):
        self._type, self._type_kw = self._extract_type(product_type_keyword)

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

    @property  # of description
    def description(self) -> str:
        if not self._description:
            self._description = self.extract_description()
        return self._description

    @description.setter
    def description(self, desc_md: str):
        self._description = desc_md

    def extract_description(self) -> str:
        soup = self.get_soup()
        desc_soup = soup.find(class_="work_parts_container")
        desc_soup_list: List[BeautifulSoup] = []
        for child in desc_soup.children:
            if type(child) is NavigableString and child.strip() == "":
                continue
            desc_soup_list += self._unpack_div(child)
        desc_markdown_list: List[str] = []
        for d_soup in desc_soup_list:
            md = markdownify(str(d_soup))
            md = md.replace("(//", "(https://")
            desc_markdown_list.append(md)
        desc_markdown = "".join(desc_markdown_list)
        return desc_markdown

    @property  # of tags
    def tags(self) -> List[Dict[str, Union[int, str]]]:
        if not self._tags:
            self._tags = self.extract_tags()
        return self._tags

    @tags.setter
    def tags(self, tags: List[Dict[str, Union[int, str]]]):
        self._tags = tags

    def extract_tags(self) -> List[Dict[str, Union[int, str]]]:
        soup = self.get_soup()
        tags_soup = self._get_select_work_outline_soup(soup, "ジャンル")
        tags = []
        for a in tags_soup.find_all("a") if tags_soup else []:
            try:
                tag_name: str = a.get_text(strip=True)
                tag_id: int = int(re.findall(r"\d{3}", a["href"])[0])
                tags.append({"id": tag_id, "name": tag_name})
            except (KeyError, IndexError, AttributeError):
                continue

        return tags

    @property  # of img_links
    def img_links(self) -> List[str]:
        if not self._img_links:
            self._img_links = self.extract_img_links()
        return self._img_links

    @img_links.setter
    def img_links(self, img_links: List[str]):
        self._img_links = img_links

    def extract_img_links(self) -> List[str]:
        soup = self.get_soup()
        img_links_soup = soup.find(class_="product-slider-data")
        img_links = []
        for div in img_links_soup.find_all("div") if img_links_soup else []:
            try:
                link: str = div["data-src"].strip("//")
                img_links.append("https://" + link)
            except (KeyError, AttributeError):
                continue

        return img_links

    @property  # of rank
    def rank(self) -> Dict[str, Any]:
        if not self._rank:
            self._rank = self.extract_rank()
        return self._rank

    @rank.setter
    def rank(self, rank: Dict[str, Any]):
        self._rank = rank

    def extract_rank(self) -> Dict[str, Any]:
        product_rest = self.get_product_rest()

        rate: float = product_rest["rate_average_2dp"] or 0.0
        rate_detail = [
            {"star": s["review_point"], "count": s["count"]}
            for s in product_rest["rate_count_detail"]
        ]

        rankings = []
        for r in product_rest["rank"] if product_rest["rank"] else []:
            _type, _ = self._extract_type("_" + r["category"])
            year, month, day = re.match(
                r"(\d{4})-?(\d{2})?-?(\d{2})?", r["rank_date"]
            ).groups()
            rankings.append(
                {
                    "term": r["term"],
                    "category": _type,
                    "rank_date": datetime(
                        year=int(year), month=int(month or 1), day=int(day or 1)
                    ),
                }
            )

        rank = {"rankings": rankings, "rate": rate, "rate_detail": rate_detail}
        return rank

    @property  # of info
    def info(self) -> Dict[str, Any]:
        if not self._info:
            self._info = self.extract_info()
        return self._info

    @info.setter
    def info(self, info: Dict[str, Any]):
        self._info = info

    def extract_info(self) -> Dict[str, Any]:
        product_info = {}

        product_rest = self.get_product_rest()
        price: int = product_rest["price"]
        price_without_tax: int = product_rest["price_without_tax"]
        original_price: int = product_rest.get("official_price", price)
        is_sale = bool(product_rest["on_sale"])
        sale_count = int(product_rest["dl_count"] or 0)
        wishlist_count = int(product_rest["wishlist_count"] or 0)
        product_info.update(
            {
                "is_sale": is_sale,
                "price": price,
                "price_without_tax": price_without_tax,
                "original_price": original_price,
                "sale_count": sale_count,
                "wishlist_count": wishlist_count,
            }
        )

        product_info.update({"addition_info": self.extract_addition_info()})

        return product_info

    def extract_addition_info(self) -> Dict[str, list]:
        def get_link(soup: BeautifulSoup) -> Tuple[str, str]:
            if type(soup) is NavigableString:
                link = soup.strip(), ""
            elif soup.name == "a":
                link = soup.get_text(strip=True), soup["href"]
            else:
                link = get_link(next(soup.children))
            return link

        soup = self.get_soup()
        work_outline_soup = self._get_work_outline_soup(soup)
        add_info = {}
        for kw, s_soup in work_outline_soup.items():
            if kw in ["販売日", "ファイル容量", "作品形式", "年齢指定", "ジャンル"]:
                continue
            kw_info = []
            for div in s_soup.children:
                if type(div) is NavigableString and div.strip() == "":
                    continue
                for info_soup in self._unpack_div(div):
                    link_title, link = get_link(info_soup)
                    if link_title in ["/"]:
                        continue
                    kw_info.append(
                        {
                            "title": re.sub(r"^[/ ]*|[/ ]*$", "", link_title),
                            "link": link,
                        }
                    )

            add_info.update({kw: kw_info})

        return add_info

    @property  # of update_log
    def update_logs(self) -> List[Dict[str, Any]]:
        if not self._update_logs:
            self._update_logs = self.extract_update_logs()
        return self._update_logs

    @update_logs.setter
    def update_logs(self, update_logs: List[Dict[str, Any]]):
        self._update_logs = update_logs

    def extract_update_logs(self) -> List[Dict[str, Any]]:
        update_logs = []
        # For first update logs page
        soup = self.get_soup()
        update_soup = soup.find(class_="work_article version_up")
        for li in update_soup.find_all("li") if update_soup else []:
            if not li:
                continue
            try:
                _log = li.dl.find_all(re.compile(r"^d"))
                year, month, day = re.match(
                    r"(\d{4})年(\d{2})月(\d{2})日", _log[0].get_text(strip=True)
                ).groups()
                update_date = datetime(
                    year=int(year), month=int(month or 1), day=int(day or 1)
                )
                update_type = [s.get_text(strip=True) for s in _log[1].find_all("span")]
                update_detail = _log[2].get_text(strip=True)
            except (KeyError, IndexError, AttributeError):
                continue
            update_logs.append(
                {"date": update_date, "type": update_type, "detail": update_detail}
            )

        # For next update log page
        if soup.find(class_="version_up_more"):
            update_logs += self.extract_update_more_logs()

        return update_logs

    def extract_update_more_logs(self) -> List[Dict[str, Any]]:
        update_logs = []
        url = "https://www.dlsite.com/maniax/product/revision/ajax"
        page = 2
        while True:
            params = {"act": "show", "product_id": self.id, "page": page}
            content = self.get_content(url, method="POST", params=params)
            content_json = json.loads(content)
            for _log in content_json["list"]:
                year, month, day = re.match(
                    r"(\d{4})年(\d{2})月(\d{2})日", _log["release_date"]
                ).groups()
                update_date = datetime(
                    year=int(year), month=int(month or 1), day=int(day or 1)
                )
                update_type = _log["content_update_type"]
                update_detail = _log["info"]
                update_logs.append(
                    {
                        "date": update_date,
                        "type": update_type,
                        "detail": update_detail,
                    }
                )

            if not content_json["more"]:
                break
            page += 1

        return update_logs

    # TODO
    def get_content(
        self,
        url: str,
        method: str = "GET",
        headers: dict = {},
        params: dict = {},
    ) -> bytes:
        resp = requests.request(method, url, headers=headers, params=params)
        if resp.ok and resp.content:
            return resp.content
        else:
            raise ValueError

    def get_product_rest(self, update: bool = False) -> dict:
        if not (self._product_rest) or update:
            url = f"{BASE_URL}/maniax/product/info/ajax?product_id={self.id}"
            content = self.get_content(url)
            product_json = json.loads(content)
            self._product_rest: dict = product_json[self.id]
        return self._product_rest

    def get_soup(self, content: bytes = None, update: bool = False) -> BeautifulSoup:
        if not (self._soup) or content or update:
            url = f"{BASE_URL}/maniax/work/=/product_id/{self.id}"
            content = content if content else self.get_content(url)
            self._soup = BeautifulSoup(content, "lxml")
        return self._soup

    def _get_select_work_outline_soup(
        self, soup: BeautifulSoup, select_keyword: str
    ) -> Union[BeautifulSoup, None]:
        return self._get_work_outline_soup(soup).get(select_keyword, None)

    def _get_work_outline_soup(self, soup: BeautifulSoup) -> Dict[str, BeautifulSoup]:
        work_outline_soup = {}
        for tr in soup.find(id="work_outline").find_all("tr"):
            work_outline_soup.update({tr.th.get_text(strip=True): tr.td})
        return work_outline_soup

    def _unpack_div(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        if type(soup) is NavigableString:
            return [soup]
        children_list = []
        for child in soup.children:
            if type(child) is NavigableString:
                if child.strip() == "":
                    continue
                children_list.append(child)
            elif child.name != "div":
                children_list.append(child)
            else:
                children_list += self._unpack_div(child)
        return children_list
