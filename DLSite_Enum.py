from enum import Enum, auto


class DLSite_Rate(Enum):
    UNKNOWN = 0
    ALL_AGE = auto()
    R15 = auto()
    R18 = auto()


DLSite_Rate_Info = {
    DLSite_Rate.UNKNOWN: {"name": None, "keyword": {None: None}},
    DLSite_Rate.ALL_AGE: {"name": "全年龄", "keyword": {"GEN": "全年龄"}},
    DLSite_Rate.R15: {"name": "R-15", "keyword": {"R15": "R-15"}},
    DLSite_Rate.R18: {"name": "18禁", "keyword": {"ADL": "18禁"}},
}


class DLSite_Type(Enum):
    UNKNOWN = 0
    GAME = auto()
    COMIC = auto()
    CG_ART = auto()
    NOVEL = auto()
    ANIMATION = auto()
    VOICE = auto()
    MUSIC = auto()
    MATERIAL = auto()
    OTHER = auto()
    ALL = auto()


DLSite_Type_Info = {
    DLSite_Type.UNKNOWN: {"name": None, "keyword": {None: None}},
    DLSite_Type.GAME: {
        "name": "ゲーム",
        "keyword": {
            "ETC": "その他ゲーム",
            "ACN": "アクション",
            "QIZ": "クイズ",
            "ADV": "アドベンチャー",
            "RPG": "ロールプレイング",
            "TBL": "テーブル",
            "DNV": "デジタルノベル",
            "SLN": "シミュレーション",
            "TYP": "タイピング",
            "STG": "シューティング",
            "PZL": "パズル",
            "_GAME": "ゲーム・動画",
        },
    },
    DLSite_Type.COMIC: {"name": "マンガ", "keyword": {"MNG": "マンガ", "_COMIC": "マンガ・CG"}},
    DLSite_Type.CG_ART: {"name": "CG・イラスト", "keyword": {"ICG": "CG・イラスト"}},
    DLSite_Type.NOVEL: {"name": "ノベル", "keyword": {"NRE": "ノベル"}},
    DLSite_Type.ANIMATION: {"name": "動画", "keyword": {"MOV": "動画"}},
    DLSite_Type.VOICE: {
        "name": "ボイス・ASMR",
        "keyword": {"SOU": "ボイス・ASMR", "_VOICE": "ボイス・ASMR"},
    },
    DLSite_Type.MUSIC: {"name": "音楽", "keyword": {"MUS": "音楽"}},
    DLSite_Type.MATERIAL: {
        "name": "ツール/アクセサリ",
        "keyword": {"TOL": "ツール/アクセサリ", "IMT": "画像素材", "AMT": "音素材"},
    },
    DLSite_Type.OTHER: {"name": "その他", "keyword": {"ET3": "その他", "VCM": "ボイスコミック"}},
    DLSite_Type.ALL: {"name": "総合", "keyword": {"_ALL": "総合"}},
}
