# encoding: utf-8
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from codecs import open

engine = create_engine('postgresql:///veekun2012')
Session = sessionmaker(bind=engine)
session = Session()

from pokedex.db import identifier_from_name
from pokedex.db.tables import Language
from pokedex.db.tables import Location, LocationGameIndex

en = session.query(Language).filter_by(identifier='en').one() # English
ja = session.query(Language).filter_by(identifier='ja').one() # Japanese

en_names = [
    "Aspertia City", #
    "Virbank City", #
    "Humilau City", #"Seigaiha City",
    "PokéStar Studios", #"PokéWood",
    "Join Avenue", #
    "Floccesy Town", #"Sangi Town",
    "Lentimas Town", #"Yamaji Town",
    "Route 19",
    "Route 20",
    "Route 21",
    "Route 22",
    "Route 23",
    "Castelia Sewers", #
    "Floccesy Ranch", #"Sangi Ranch",
    "Virbank Complex", #"Virbank Industrial Complex",
    "Reversal Mountain", #"Reverse Mountain",
    "Strange House", #"Stranger's House",
    "Victory Road",
    "Plasma Frigate", #
    "Relic Passage", #"Ancient Path",
    "Clay Tunnel", #"Clay Road",
    "",
    "White Treehollow", #"White Tree Hollow",
    "Black Tower", #"Black Skyscraper",
    "Seaside Cave", #"Seaside Grotto",
    "Cave of Being", #"Heart Hollow",
    "Hidden Grotto", #"Hidden Cave",
    "Marine Tube", #
    "Virbank Gate",
    "Aspertia Gate",
    "Nature Sanctuary",
    "Medal Secretariat",
    "Underground Ruins",
    "Rocky Mountain Room",
    "Glacier Room",
    "Iron Room",
    "Pledge Grove", #"Oath Forest",
]

ja_names = [
    "ヒオウギシティ",
    "タチワキシティ",
    "セイガイハシティ",
    "ポケウッド",
    "ジョインアベニュー",
    "サンギタウン",
    "ヤマジタウン",
    "１９番道路",
    "２０番道路",
    "２１番水道",
    "２２番道路",
    "２３番道路",
    "ヒウン下水道",
    "サンギ牧場",
    "タチワキコンビナート",
    "リバースマウンテン",
    "ストレンジャーハウス",
    "チャンピオンロード",
    "プラズマフリゲート",
    "古代の抜け道",
    "ヤーコンロード",
    "－－－－－－－－－－",
    "白の樹洞",
    "黒の摩天楼",
    "海辺の洞穴",
    "心の空洞",
    "隠し穴",
    "マリンチューブ",
    "タチワキゲート",
    "ヒオウギゲート",
    "自然保護区",
    "メダル事務局",
    "地底遺跡",
    "岩山の間",
    "氷山の間",
    "鉄の間",
    "誓いの林",
]

locations = {}
for i, name in enumerate(zip(en_names, ja_names)):
    i += 117

    en_name, ja_name = name
    if not en_name:
        continue

    if name in locations:
        loc = locations[name]
    else:
        loc = Location()
        if en_name:
            loc.name_map[en] = en_name
        if ja_name:
            loc.name_map[ja] = ja_name
        loc.region_id = 5 # Unova
        loc.identifier = identifier_from_name(en_name)
        if loc.identifier == 'victory-road':
            loc.identifier = 'unova-victory-road-2'

        locations[name] = loc

    lgi = LocationGameIndex()
    lgi.location = loc
    lgi.generation_id = 5 # Gen 5
    lgi.game_index = i

    session.add(loc)
    session.add(lgi)

session.commit()

