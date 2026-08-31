import configparser

from utils.paths import LAUNCHER_CONFIG
from utils.settings_store import load, write_atomic

INI_FILE = LAUNCHER_CONFIG

REGIONS = {
    "North America": {
        "url": "https://www.missionchief.com",
        "code": "US",
        "language": "en",
    },
    "United Kingdom": {
        "url": "https://www.missionchief.co.uk",
        "code": "GB",
        "language": "en",
    },
    "Germany": {
        "url": "https://www.leitstellenspiel.de",
        "code": "DE",
        "language": "de",
    },
    "Netherlands": {
        "url": "https://www.meldkamerspel.com",
        "code": "NL",
        "language": "nl",
    },
    "Australia": {
        "url": "https://www.missionchief-australia.com",
        "code": "AU",
        "language": "en",
    },
    "Italy": {
        "url": "https://www.operatore112.it",
        "code": "IT",
        "language": "it",
    },
    "Portugal": {
        "url": "https://www.operador193.com",
        "code": "PT",
        "language": "pt",
    },
    "Turkey": {
        "url": "https://www.intikam112.com",
        "code": "TR",
        "language": "tr",
    },
    "Poland": {
        "url": "https://www.operatorratunkowy.pl",
        "code": "PL",
        "language": "pl",
    },
    "France": {
        "url": "https://www.operateur112.fr",
        "code": "FR",
        "language": "fr",
    },
    "Spain": {
        "url": "https://www.centro-de-mando.es",
        "code": "ES",
        "language": "es",
    },
    "Sweden": {
        "url": "https://www.larmcentralen-spansen.se",
        "code": "SE",
        "language": "sv",
    },
    "Norway": {
        "url": "https://www.nodsentralspansen.com",
        "code": "NO",
        "language": "no",
    },
    "Denmark": {
        "url": "https://www.alarmcentralen-spansen.dk",
        "code": "DK",
        "language": "da",
    },
    "South Korea": {
        "url": "https://www.missionchief-korea.com",
        "code": "KR",
        "language": "ko",
    },
    "Japan": {
        "url": "https://www.missionchief-japan.com",
        "code": "JP",
        "language": "ja",
    },
    "Romania": {
        "url": "https://www.jocdispecerat112.com",
        "code": "RO",
        "language": "ro",
    },
    "Russia": {
        "url": "https://www.dispetcher112.ru",
        "code": "RU",
        "language": "ru",
    },
    "Czech Republic": {
        "url": "https://www.operacni-stredisko.cz",
        "code": "CZ",
        "language": "cs",
    },
    "Mexico": {
        "url": "https://www.centro-de-mando.mx",
        "code": "MX",
        "language": "es",
    },
    "Brazil": {
        "url": "https://www.operador193.com",
        "code": "BR",
        "language": "pt",
    },
}


def list_regions():
    return list(REGIONS.keys())


def get_region_data(region_name=None):
    if region_name is None:
        region_name = get_selected_region()

    return REGIONS.get(region_name, REGIONS["North America"])


def get_region_url(region_name=None):
    return get_region_data(region_name)["url"]


def get_region_code(region_name=None):
    return get_region_data(region_name)["code"]


def get_region_language(region_name=None):
    return get_region_data(region_name)["language"]


def get_selected_region():
    config = load(INI_FILE)
    region = config.get("Launcher", "region", fallback="").strip()
    return region if region in REGIONS else ""


def select_region(region_name):
    if region_name not in REGIONS:
        raise ValueError(f"Unknown region: {region_name}")

    config = load(INI_FILE)

    if not config.has_section("Launcher"):
        config.add_section("Launcher")

    config.set("Launcher", "region", region_name)

    write_atomic(config, INI_FILE)


def is_region_selected():
    return bool(get_selected_region())
