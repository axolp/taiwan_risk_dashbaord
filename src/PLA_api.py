import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.mnd.gov.tw/"
LIST_URL = "https://www.mnd.gov.tw/en/news/PlaactList"


@dataclass(frozen=True)
class PlaDailyObservation:
    pla_aircraft: int
    median_line_crossings: int
    plan_ships: int
    official_ships: int


class PlaActivityClient:
    def __init__(self) -> None:
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
        })

    def fetch_latest_report_url(self) -> str:
        response = self.session.get(LIST_URL, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        container = soup.select_one("div.news_list_box")

        if not container:
            raise RuntimeError("Nie znaleziono news_list_box")

        first_link = container.select_one("a.news_list")

        if not first_link:
            raise RuntimeError("Nie znaleziono raportu")

        href = first_link.get("href")

        if not href:
            raise RuntimeError("Brak href")

        return urljoin(BASE_URL, href)

    @staticmethod
    def parse_int(pattern: str, text: str) -> int:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if not match:
            return 0

        return int(match.group(1))

    @staticmethod
    def extract_pla_activity_text(html: str) -> str:
        soup = BeautifulSoup(html, "lxml")

        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)

            normalized = text.lower().replace(" ", "")

            if "2.plaactivities:" in normalized:
                return text

        raise RuntimeError("Nie znaleziono sekcji PLA activities")

    def fetch_latest_observation(self) -> PlaDailyObservation:
        report_url = self.fetch_latest_report_url()

        response = self.session.get(report_url, timeout=20)
        response.raise_for_status()

        text = self.extract_pla_activity_text(response.text)

        aircraft = self.parse_int(
            r"(\d+)\s+sorties?\s+of\s+PLA\s+aircraft",
            text,
        )

        plan_ships = self.parse_int(
            r"(\d+)\s+PLAN\s+ships?",
            text,
        )

        official_ships = self.parse_int(
            r"(\d+)\s+official\s+ships?",
            text,
        )

        median_line_crossings = self.parse_int(
            r"(\d+)\s+out\s+of\s+\d+\s+sorties?\s+crossed\s+the\s+median\s+line",
            text,
        )

        return PlaDailyObservation(
            pla_aircraft=aircraft,
            median_line_crossings=median_line_crossings,
            plan_ships=plan_ships,
            official_ships=official_ships,
        )