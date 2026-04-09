import streamlit as st
import base64
import os
import json
import urllib.request
import urllib.parse
from dataclasses import dataclass
from typing import List

# ----------------------------
# 1. CONSTANTS, MODELS & DATA
# ----------------------------
BLOCK_300 = 300.0
BLOCK_600 = 600.0
RES_LIFELINE_MAX = 30.0
LEVY_RATE_STANDARD = 0.05
LEVY_RATE_ZERO = 0.00
LEVY_RATE_10 = 0.10
TAX_RATE_STANDARD = 0.20
TAX_RATE_REDUCED = 0.175
TAX_RATE_15 = 0.15
TAX_RATE_12_5 = 0.125
TAX_RATE_10 = 0.10

@dataclass
class BillResult:
    year: str
    quarter: str
    category: str
    energy_total: float
    demand_charge: float
    service_charge: float
    levies_taxes_total: float
    total_payable: float

# Official Tariff Data
# - 2026 Q1, Q2
# - 2025 Q2, Q3, Q4
# - 2024 Q1, Q2, Q3
# - 2023 Q1 (Feb), Q2 (Jun), Q3 (Sep), Q4 (Dec) Added
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "tariffs")

DEFAULT_TARIFFS = {
    "2026": {
        "QUARTER 2 (APR)": {
            "rates": {"RES_LIFELINE": 0.8690, "RES_B1": 1.968825, "RES_B2": 2.601481, "NONRES_B1": 1.777539, "NONRES_B2": 2.164873, "SLT_LV": 2.321130, "SLT_MV": 2.016000, "SLT_MV2": 1.320448, "SLT_HV": 1.821228},
            "service": {"Lifeline": 2.13, "Other": 10.730886, "NonRes": 12.428245, "SLT": 500.00}
        }, 
        "QUARTER 1 (JAN)": {
            "rates": {"RES_LIFELINE": 0.8837, "RES_B1": 2.0022, "RES_B2": 2.6456, "NONRES_B1": 1.8076, "NONRES_B2": 2.2465, "SLT_LV": 2.6978, "SLT_MV": 2.1534, "SLT_MV2": 1.3428, "SLT_HV": 2.1534},
            "service": {"Lifeline": 2.13, "Other": 10.7308, "NonRes": 12.4282, "SLT": 500.00}
        }
    },
    "2025": {
        "QUARTER 4 (OCT)": {
            "rates": {"RES_LIFELINE": 0.8043, "RES_B1": 1.8224, "RES_B2": 2.4080, "NONRES_B1": 1.6453, "NONRES_B2": 2.0448, "SLT_LV": 2.4555, "SLT_MV": 1.9601, "SLT_MV2": 1.2788, "SLT_HV": 1.9601},
            "service": {"Lifeline": 2.13, "Other": 10.7301, "NonRes": 12.428, "SLT": 500.00}
        },
        "QUARTER 3 (JUL)": {
            "rates": {
                "RES_LIFELINE": 0.795308, "RES_B1": 1.801867, "RES_B2": 2.380873,
                "NONRES_B1": 1.626801, "NONRES_B2": 2.021723,
                "SLT_LV": 2.427874, "SLT_MV": 1.937990, "SLT_MV2": 1.264423, "SLT_HV": 1.937990
            },
            "service": {"Lifeline": 2.13, "Other": 10.73088, "NonRes": 12.4282, "SLT": 500.00}
        },
        "QUARTER 2 (MAY)": {
            "rates": {
                "RES_LIFELINE": 0.776274, "RES_B1": 1.758743, "RES_B2": 2.323892,
                "NONRES_B1": 1.587868, "NONRES_B2": 1.973338,
                "SLT_LV": 2.369769, "SLT_MV": 1.891609, "SLT_MV2": 1.234162, "SLT_HV": 1.891609
            },
            "service": {"Lifeline": 2.13, "Other": 10.73088, "NonRes": 12.4182, "SLT": 500.00}
        }
    },
    "2024": {
        "QUARTER 3 (OCT)": {
            "rates": {
                "RES_LIFELINE": 67.6495 / 100,  "RES_B1": 153.2683 / 100, "RES_B2": 202.5190 / 100,
                "NONRES_B1": 138.3771 / 100,    "NONRES_B2": 171.9695 / 100,
                "SLT_LV": 206.5170 / 100,       "SLT_MV": 164.8471 / 100, "SLT_MV2": 107.5529 / 100, "SLT_HV": 164.8471 / 100
            },
            "service": {"Lifeline": 2.13, "Other": 10.7309, "NonRes": 12.4282, "SLT": 500.00}
        },
        "QUARTER 2 (JUL)": {
            "rates": {
                "RES_LIFELINE": 65.6664 / 100,  "RES_B1": 148.7753 / 100, "RES_B2": 196.5822 / 100,
                "NONRES_B1": 134.3206 / 100,    "NONRES_B2": 166.9293 / 100,
                "SLT_LV": 200.4630 / 100,       "SLT_MV": 160.0146 / 100, "SLT_MV2": 104.4000 / 100, "SLT_HV": 160.0146 / 100
            },
            "service": {"Lifeline": 2.13, "Other": 10.7309, "NonRes": 12.4282, "SLT": 500.00}
        },
        "QUARTER 1 (APR)": {
            "rates": {
                "RES_LIFELINE": 63.4792 / 100,  "RES_B1": 140.5722 / 100, "RES_B2": 185.7432 / 100,
                "NONRES_B1": 126.9145 / 100,    "NONRES_B2": 157.7242 / 100,
                "SLT_LV": 191.0709 / 100,       "SLT_MV": 152.5176 / 100, "SLT_MV2": 152.5176 / 100, "SLT_HV": 152.5176 / 100
            },
            "service": {"Lifeline": 2.13, "Other": 10.7309, "NonRes": 12.4282, "SLT": 500.00}
        }
    },
    "2023": {
        "QUARTER 4 (DEC)": {
             "rates": {
                # 3-Tier Block Structure for 2023 Q4
                "RES_LIFELINE": 63.4792 / 100,
                "RES_B1": 140.5722 / 100, # 0-300
                "RES_B2": 182.4354 / 100, # 301-600
                "RES_B3": 202.7060 / 100, # 601+
                
                "NONRES_B1": 126.9145 / 100, # 0-300
                "NONRES_B2": 135.0506 / 100, # 301-600
                "NONRES_B3": 201.6051 / 100, # 601+
                
                "SLT_LV": 200.8789 / 100,
                "SLT_MV": 152.5176 / 100,
                "SLT_HV": 160.0738 / 100,
                "SLT_HV_STEEL": 112.8988 / 100,
                "SLT_HV_MINES": 399.8573 / 100
            },
            "service": {
                "Lifeline": 213.0000 / 100,
                "Other": 1073.0886 / 100,
                "NonRes": 1242.8245 / 100,
                "SLT": 50000.0000 / 100
            }
        },
        "QUARTER 3 (SEP)": {
             "rates": {
                # 3-Tier Block Structure for 2023 Q3
                "RES_LIFELINE": 64.4620 / 100,
                "RES_B1": 142.7485 / 100, # 0-300
                "RES_B2": 185.2598 / 100, # 301-600
                "RES_B3": 205.8442 / 100, # 601+
                
                "NONRES_B1": 128.8793 / 100, # 0-300
                "NONRES_B2": 137.1414 / 100, # 301-600
                "NONRES_B3": 204.7263 / 100, # 601+
                
                "SLT_LV": 203.9889 / 100,
                "SLT_MV": 154.8788 / 100,
                "SLT_HV": 162.5521 / 100,
                "SLT_HV_STEEL": 114.6467 / 100,
                "SLT_HV_MINES": 406.0478 / 100
            },
            "service": {
                "Lifeline": 213.0000 / 100,
                "Other": 1073.0886 / 100,
                "NonRes": 1242.8245 / 100,
                "SLT": 50000.0000 / 100
            }
        },
        "QUARTER 2 (JUN)": {
             "rates": {
                # 3-Tier Block Structure for 2023 Q2
                "RES_LIFELINE": 64.4620 / 100,
                "RES_B1": 136.9676 / 100, # 0-300
                "RES_B2": 177.7574 / 100, # 301-600
                "RES_B3": 197.5082 / 100, # 601+
                
                "NONRES_B1": 128.8793 / 100, # 0-300
                "NONRES_B2": 137.1414 / 100, # 301-600
                "NONRES_B3": 204.7263 / 100, # 601+
                
                "SLT_LV": 203.9889 / 100,
                "SLT_MV": 154.8788 / 100,
                "SLT_HV": 162.5521 / 100,
                "SLT_HV_STEEL": 114.6467 / 100,
                "SLT_HV_MINES": 406.0478 / 100
            },
            "service": {
                "Lifeline": 213.0000 / 100,
                "Other": 1073.0886 / 100,
                "NonRes": 1242.8245 / 100,
                "SLT": 50000.0000 / 100
            }
        },
        "QUARTER 1 (FEB)": {
            "rates": {                # 3-Tier Block Structure for 2023 Q1
                "RES_LIFELINE": 54.4627 / 100,
                "RES_B1": 115.7212 / 100, # 0-300
                "RES_B2": 150.1837 / 100, # 301-600
                "RES_B3": 166.8708 / 100, # 601+
                
                "NONRES_B1": 108.8876 / 100, # 0-300
                "NONRES_B2": 115.8681 / 100, # 301-600
                "NONRES_B3": 172.9692 / 100, # 601+
                
                "SLT_LV": 172.3461 / 100,
                "SLT_MV": 130.8541 / 100,
                "SLT_HV": 137.3370 / 100,
                "SLT_HV_STEEL": 96.8627 / 100,
                "SLT_HV_MINES": 343.0618 / 100
            },
            "service": {
                "Lifeline": 213.0000 / 100,
                "Other": 1073.0886 / 100,
                "NonRes": 1242.8245 / 100,
                "SLT": 50000.0000 / 100
            }
        }
    },

    "2022": {
        "QUARTER 3 (SEP)": {
            "rates": {
                "RES_LIFELINE": 0.419065,
                "RES_B1": 0.890422,
                "RES_B2": 1.155595,
                "RES_B3": 1.283995,
                "NONRES_B1": 0.837841,
                "NONRES_B2": 0.891552,
                "NONRES_B3": 1.330919,
                "SLT_LV": 1.326125,
                "SLT_MV": 1.006863,
                "SLT_HV": 1.056746,
                "SLT_HV_STEEL": 0.745315,
                "SLT_HV_MINES": 2.639705
            },
            "service": {
                "Lifeline": 2.13,
                "Other": 10.730886,
                "NonRes": 12.428245,
                "SLT": 500.00
            }
        }
    },
    "2021": {
        "QUARTER 1 (JAN)": {
            "rates": {
                "RES_LIFELINE": 0.326060,
                "RES_B1": 0.654161,
                "RES_B2": 0.848974,
                "RES_B3": 0.943304,
                "NONRES_B1": 0.797943,
                "NONRES_B2": 0.797943,
                "NONRES_B3": 0.849097,
                "NONRES_B4": 1.339765,
                "SLT_LV": 1.047303,
                "SLT_MV": 0.795167,
                "SLT_HV": 0.834562,
                "SLT_HV_MINES": 2.639705
            },
            "service": {
                "Lifeline": 2.13,
                "Other": 7.456947,
                "NonRes": 12.428245,
                "SLT_LV": 49.712983,
                "SLT_MV": 69.598177,
                "SLT_HV": 69.598177,
                "SLT_HV_MINES": 69.598177
            }
        }
    },
    "2020": {
        "QUARTER 1 (JAN)": {
            "rates": {
                "RES_LIFELINE": 0.326060,
                "RES_B1": 0.654161,
                "RES_B2": 0.848974,
                "RES_B3": 0.943304,
                "NONRES_B1": 0.797943,
                "NONRES_B2": 0.797943,
                "NONRES_B3": 0.849097,
                "NONRES_B4": 1.339765,
                "SLT_LV": 1.047303,
                "SLT_MV": 0.795167,
                "SLT_HV": 0.834562,
                "SLT_HV_MINES": 2.639705
            },
            "service": {
                "Lifeline": 2.13,
                "Other": 7.456947,
                "NonRes": 12.428245,
                "SLT_LV": 49.712983,
                "SLT_MV": 69.598177,
                "SLT_HV": 69.598177,
                "SLT_HV_MINES": 69.598177
            }
        },
        "QUARTER 2 (APR)": {
            "rates": {
                "RES_LIFELINE": 0.326060,
                "RES_B1": 0.654161,
                "RES_B2": 0.848974,
                "RES_B3": 0.943304,
                "NONRES_B1": 0.797943,
                "NONRES_B2": 0.797943,
                "NONRES_B3": 0.849097,
                "NONRES_B4": 1.339765,
                "SLT_LV": 1.047303,
                "SLT_MV": 0.795167,
                "SLT_HV": 0.834562,
                "SLT_HV_MINES": 2.639705
            },
            "service": {
                "Lifeline": 2.13,
                "Other": 7.456947,
                "NonRes": 12.428245,
                "SLT_LV": 49.712983,
                "SLT_MV": 69.598177,
                "SLT_HV": 69.598177,
                "SLT_HV_MINES": 69.598177
            }
        },
        "QUARTER 3 (JUL)": {
            "rates": {
                "RES_LIFELINE": 0.326060,
                "RES_B1": 0.654161,
                "RES_B2": 0.848974,
                "RES_B3": 0.943304,
                "NONRES_B1": 0.797943,
                "NONRES_B2": 0.797943,
                "NONRES_B3": 0.849097,
                "NONRES_B4": 1.339765,
                "SLT_LV": 1.047303,
                "SLT_MV": 0.795167,
                "SLT_HV": 0.834562,
                "SLT_HV_MINES": 2.639705
            },
            "service": {
                "Lifeline": 2.13,
                "Other": 7.456947,
                "NonRes": 12.428245,
                "SLT_LV": 49.712983,
                "SLT_MV": 69.598177,
                "SLT_HV": 69.598177,
                "SLT_HV_MINES": 69.598177
            }
        },
        "QUARTER 4 (OCT)": {
            "rates": {
                "RES_LIFELINE": 0.326060,
                "RES_B1": 0.654161,
                "RES_B2": 0.848974,
                "RES_B3": 0.943304,
                "NONRES_B1": 0.797943,
                "NONRES_B2": 0.797943,
                "NONRES_B3": 0.849097,
                "NONRES_B4": 1.339765,
                "SLT_LV": 1.047303,
                "SLT_MV": 0.795167,
                "SLT_HV": 0.834562,
                "SLT_HV_MINES": 2.639705
            },
            "service": {
                "Lifeline": 2.13,
                "Other": 7.456947,
                "NonRes": 12.428245,
                "SLT_LV": 49.712983,
                "SLT_MV": 69.598177,
                "SLT_HV": 69.598177,
                "SLT_HV_MINES": 69.598177
            }
        }
    },
    "2019": {
    "QUARTER 3 (JUL)": {
        "rates": {
            "RES_LIFELINE": 0.307780,
            "RES_B1": 0.617488,
            "RES_B2": 0.801380,
            "RES_B3": 0.890422,
            "NONRES_B1": 0.753210,
            "NONRES_B2": 0.753210,
            "NONRES_B3": 0.801496,
            "NONRES_B4": 1.264657,
            "SLT_LV": 0.988591,
            "SLT_MV": 0.750589,
            "SLT_HV": 0.787776,
            "SLT_HV_MINES": 2.491721
        },
        "service": {
            "Lifeline": 2.13,
            "Other": 7.038906,
            "NonRes": 11.731511,
            "SLT_LV": 46.926045,
            "SLT_MV": 65.696464,
            "SLT_HV": 65.696464,
            "SLT_HV_MINES": 65.696464
        }

},
    "QUARTER 4 (OCT)": {
    "rates": {
        "RES_LIFELINE": 0.326060,
        "RES_B1": 0.654161,
        "RES_B2": 0.848974,
        "RES_B3": 0.943304,
        "NONRES_B1": 0.797943,
        "NONRES_B2": 0.797943,
        "NONRES_B3": 0.849097,
        "NONRES_B4": 1.339765,
        "SLT_LV": 1.047303,
        "SLT_MV": 0.795167,
        "SLT_HV": 0.834562,
        "SLT_HV_MINES": 2.639705
    },
    "service": {
        "Lifeline": 2.13,
        "Other": 7.456947,
        "NonRes": 12.428245,
        "SLT_LV": 49.712983,
        "SLT_MV": 69.598177,
        "SLT_HV": 69.598177,
        "SLT_HV_MINES": 69.598177
    }
}
},
    "2018": {
    "QUARTER 1 (MAR)": {
        "rates": {
            "RES_LIFELINE": 0.276858,
            "RES_B1": 0.555450,
            "RES_B2": 0.720866,
            "RES_B3": 0.800963,
            "NONRES_B1": 0.677536,
            "NONRES_B2": 0.677536,
            "NONRES_B3": 0.720971,
            "NONRES_B4": 1.137598,
            "SLT_LV": 0.756640,
            "SLT_MV": 0.585683,
            "SLT_HV": 0.538196,
            "SLT_HV_MINES": 1.025739
        },
        "service": {
            "Lifeline": 2.13,
            "Other": 6.331717,
            "NonRes": 10.552862,
            "SLT_LV": 42.211449,
            "SLT_MV": 59.096029,
            "SLT_HV": 59.096029,
            "SLT_HV_MINES": 59.096029
        }
    },

    "QUARTER 2 (JUL)": {
    "rates": {
        "RES_LIFELINE": 0.276858,
        "RES_B1": 0.555450,
        "RES_B2": 0.720866,
        "RES_B3": 0.800963,
        "NONRES_B1": 0.677536,
        "NONRES_B2": 0.677536,
        "NONRES_B3": 0.720971,
        "NONRES_B4": 1.137598,
        "SLT_LV": 0.756640,
        "SLT_MV": 0.585683,
        "SLT_HV": 0.538196,
        "SLT_HV_MINES": 1.025739
    },
    "service": {
        "Lifeline": 2.13,
        "Other": 6.331717,
        "NonRes": 10.552862,
        "SLT_LV": 42.211449,
        "SLT_MV": 59.096029,
        "SLT_HV": 59.096029,
        "SLT_HV_MINES": 59.096029
    }

},
    "QUARTER 3 (OCT)": {
    "rates": {
        "RES_LIFELINE": 0.276858,
        "RES_B1": 0.555450,
        "RES_B2": 0.720866,
        "RES_B3": 0.800963,
        "NONRES_B1": 0.677536,
        "NONRES_B2": 0.677536,
        "NONRES_B3": 0.720971,
        "NONRES_B4": 1.137598,
        "SLT_LV": 0.756640,
        "SLT_MV": 0.585683,
        "SLT_HV": 0.538196,
        "SLT_HV_MINES": 1.025739
    },
    "service": {
        "Lifeline": 2.13,
        "Other": 6.331717,
        "NonRes": 10.552862,
        "SLT_LV": 42.211449,
        "SLT_MV": 59.096029,
        "SLT_HV": 59.096029,
        "SLT_HV_MINES": 59.096029
    }
}
},
    "2017": {
        "QUARTER 1 (JAN)": {
            "rates": {
                "RES_LIFELINE": 0.335600,
                "RES_B1": 0.673300,
                "RES_B2": 0.873800,
                "RES_B3": 0.970900,
                "NONRES_B1": 0.967900,
                "NONRES_B2": 1.029900,
                "NONRES_B3": 1.625100,
                "SLT_LV": 1.008900,
                "SLT_MV": 0.780900,
                "SLT_HV": 0.717600,
                "SLT_HV_MINES": 1.139700,
                "SLT_LV_DEMAND": 59.096000,
                "SLT_MV_DEMAND": 50.653700,
                "SLT_HV_DEMAND": 50.653700,
                "SLT_HV_MINES_DEMAND": 59.096000
            },
            "service": {
                "Lifeline": 6.331700,
                "Other": 6.331700,
                "NonRes": 10.552900,
                "SLT_LV": 42.211500,
                "SLT_MV": 59.096000,
                "SLT_HV": 59.096000,
                "SLT_HV_MINES": 59.096000
            }
        }
    }
}
def _supabase_headers(prefer: str = ""):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _supabase_request(method: str, path: str, payload=None, query: str = ""):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if query:
        url = f"{url}?{query}"

    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url=url, data=body, method=method, headers=_supabase_headers())

    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        if not raw:
            return None
        return json.loads(raw)


def seed_supabase_if_empty():
    rows = _supabase_request("GET", SUPABASE_TABLE, query="select=year,quarter&limit=1")
    if rows:
        return

    payload = []
    for year, quarters in DEFAULT_TARIFFS.items():
        for quarter, data in quarters.items():
            payload.append({
                "year": year,
                "quarter": quarter,
                "rates_json": data["rates"],
                "service_json": data["service"],
            })

    if payload:
        req = urllib.request.Request(
            url=f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=_supabase_headers(prefer="resolution=merge-duplicates"),
        )
        with urllib.request.urlopen(req, timeout=15):
            pass


def load_tariffs_from_supabase():
    # Keep app functional even before env vars are configured.
    if not SUPABASE_URL or not SUPABASE_KEY:
        return DEFAULT_TARIFFS

    try:
        seed_supabase_if_empty()
        rows = _supabase_request(
            "GET",
            SUPABASE_TABLE,
            query=urllib.parse.urlencode({"select": "year,quarter,rates_json,service_json"}),
        )

        loaded = {year: {} for year in DEFAULT_TARIFFS.keys()}
        for row in rows or []:
            year = str(row["year"])
            quarter = row["quarter"]
            if year not in loaded:
                loaded[year] = {}
            loaded[year][quarter] = {
                "rates": row["rates_json"],
                "service": row["service_json"],
            }

        return loaded
    except Exception:
        return DEFAULT_TARIFFS


TARIFFS = load_tariffs_from_supabase()

# ----------------------------
# 2. ENGINES & HELPERS
# ----------------------------
def get_img_as_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_tax_rate(year: str, quarter: str) -> float:
    # VAT/NHIL/GETFund adjustments by period.
    try:
        y = int(year)
    except Exception:
        return TAX_RATE_STANDARD

    if 1998 <= y <= 1999:
        return TAX_RATE_10
    if 2000 <= y <= 2002:
        return TAX_RATE_12_5
    if 2003 <= y <= 2012:
        return TAX_RATE_15
    if 2013 <= y <= 2017:
        return TAX_RATE_REDUCED
    # 17.5% from Aug 2018 through 2022 tariffs.
    if 2019 <= y <= 2022:
        return TAX_RATE_REDUCED
    if y == 2018 and quarter in ["QUARTER 3 (OCT)", "QUARTER 4 (OCT)", "QUARTER 4 (DEC)"]:
        return TAX_RATE_REDUCED
    return TAX_RATE_STANDARD

def get_levy_rate(year: str) -> float:
    # Levy adjustments:
    # 1998-2014 => 0%, 2015 => 10%, 2016+ => 5%.
    try:
        y = int(year)
    except Exception:
        return LEVY_RATE_STANDARD

    if 1998 <= y <= 2014:
        return LEVY_RATE_ZERO
    if y == 2015:
        return LEVY_RATE_10
    return LEVY_RATE_STANDARD

def calculate_bill(year, quarter, category, kwh) -> BillResult:
    if year not in ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"] or quarter not in TARIFFS[year]:
        return None
    t = TARIFFS[year][quarter]
    if not t:
        return None

    r, s = t["rates"], t["service"]
    energy_total = 0.0
    service = 0.0

    if year == "2017":
        if category == "Residential":
            if kwh <= 50:
                energy_total = kwh * r["RES_LIFELINE"]
                service = s["Lifeline"]
            else:
                b1 = min(max(0, kwh - 50), 250)
                b2 = min(max(0, kwh - 300), 300)
                b3 = max(0, kwh - 600)
                energy_total = (50 * r["RES_LIFELINE"]) + (b1 * r["RES_B1"]) + (b2 * r["RES_B2"]) + (b3 * r["RES_B3"])
                service = s["Other"]
        elif category == "Non-Residential":
            b1 = min(kwh, 300)
            b2 = min(max(0, kwh - 300), 300)
            b3 = max(0, kwh - 600)
            energy_total = (b1 * r["NONRES_B1"]) + (b2 * r["NONRES_B2"]) + (b3 * r["NONRES_B3"])
            service = s["NonRes"]
        else:
            key = {
                "SLT-LV": ("SLT_LV", "SLT_LV", "SLT_LV_DEMAND"),
                "SLT-MV": ("SLT_MV", "SLT_MV", "SLT_MV_DEMAND"),
                "SLT-HV": ("SLT_HV", "SLT_HV", "SLT_HV_DEMAND"),
                "SLT-HV MINES": ("SLT_HV_MINES", "SLT_HV_MINES", "SLT_HV_MINES_DEMAND"),
            }.get(category, ("SLT_LV", "SLT_LV", "SLT_LV_DEMAND"))
            energy_total = kwh * r[key[0]]
            service = s[key[1]]
            demand_charge = max(0.0, max_demand_kva) * r.get(key[2], 0.0)

    # ----------------------------
    # 2018-2021 LOGIC (RES: 0-50, 51-300, 301-600, 601+ | NONRES: 0-100, 101-300, 301-600, 601+)
    # ----------------------------
    elif year in ["2018", "2019", "2020", "2021"]:
        if category == "Residential":
            if kwh <= 50:
                energy_total = kwh * r["RES_LIFELINE"]
                service = s["Lifeline"]
            else:
                b1 = min(max(0, kwh - 50), 250)
                b2 = min(max(0, kwh - 300), 300)
                b3 = max(0, kwh - 600)
                energy_total = (50 * r["RES_LIFELINE"]) + (b1 * r["RES_B1"]) + (b2 * r["RES_B2"]) + (b3 * r["RES_B3"])
                service = s["Other"]
        elif category == "Non-Residential":
            b1 = min(kwh, 100)
            b2 = min(max(0, kwh - 100), 200)
            b3 = min(max(0, kwh - 300), 300)
            b4 = max(0, kwh - 600)
            energy_total = (b1 * r["NONRES_B1"]) + (b2 * r["NONRES_B2"]) + (b3 * r["NONRES_B3"]) + (b4 * r["NONRES_B4"])
            service = s["NonRes"]
        else:
            rate_key = {
                "SLT-LV": "SLT_LV",
                "SLT-MV": "SLT_MV",
                "SLT-HV": "SLT_HV",
                "SLT-HV MINES": "SLT_HV_MINES"
            }.get(category, "SLT_LV")
            energy_total = kwh * r[rate_key]
            service_key = {
                "SLT-LV": "SLT_LV",
                "SLT-MV": "SLT_MV",
                "SLT-HV": "SLT_HV",
                "SLT-HV MINES": "SLT_HV_MINES"
            }.get(category, "SLT_LV")
            service = s[service_key]

    # ----------------------------
    # 2022-2023 LOGIC (3 BLOCKS: 0-300, 301-600, 601+)
    # ----------------------------
    elif year in ["2022", "2023"]:
        if category == "Residential":
            if kwh <= RES_LIFELINE_MAX:
                energy_total = kwh * r["RES_LIFELINE"]
                service = s["Lifeline"]
            else:
                b1 = min(kwh, 300)
                b2 = min(max(0, kwh - 300), 300)
                b3 = max(0, kwh - 600)
                energy_total = (b1 * r["RES_B1"]) + (b2 * r["RES_B2"]) + (b3 * r["RES_B3"])
                service = s["Other"]

        elif category == "Non-Residential":
            b1 = min(kwh, 300)
            b2 = min(max(0, kwh - 300), 300)
            b3 = max(0, kwh - 600)
            energy_total = (b1 * r["NONRES_B1"]) + (b2 * r["NONRES_B2"]) + (b3 * r["NONRES_B3"])
            service = s["NonRes"]

        else:
            rate_key = {
                "SLT-LV": "SLT_LV",
                "SLT-MV": "SLT_MV",
                "SLT-HV": "SLT_HV",
                "SLT-HV STEEL COMPANIES": "SLT_HV_STEEL",
                "SLT-MINES": "SLT_HV_MINES",
                "SLT-HV MINES": "SLT_HV_MINES"
            }.get(category, "SLT_LV")
            energy_total = kwh * r[rate_key]
            service = s["SLT"]

    # 2024-2026 logic
    else:
        if category == "Residential":
            if kwh <= RES_LIFELINE_MAX:
                energy_total = kwh * r["RES_LIFELINE"]
                service = s["Lifeline"]
            else:
                energy_total = (min(kwh, BLOCK_300) * r["RES_B1"]) + (max(0, kwh - BLOCK_300) * r["RES_B2"])
                service = s["Other"]
        elif category == "Non-Residential":
            energy_total = (min(kwh, BLOCK_300) * r["NONRES_B1"]) + (max(0, kwh - BLOCK_300) * r["NONRES_B2"])
            service = s["NonRes"]
        else:
            rate_key = {"SLT-LV": "SLT_LV", "SLT-MV": "SLT_MV", "SLT-MV2": "SLT_MV2", "SLT-HV": "SLT_HV"}.get(category, "SLT_LV")
            energy_total = kwh * r[rate_key]
            service = s["SLT"]

    levy_rate = get_levy_rate(year)
    subtotal_before_tax = energy_total + demand_charge + service
    levies = subtotal_before_tax * levy_rate
    tax_rate = get_tax_rate(year, quarter) if "get_tax_rate" in globals() else TAX_RATE_STANDARD
    taxes = subtotal_before_tax * tax_rate if category != "Residential" else 0.0

    return BillResult(
        year, quarter, category,
        energy_total, demand_charge, service, levies + taxes,
        subtotal_before_tax + levies + taxes
    )

def calculate_bill_compat(year, quarter, category, kwh, max_demand_kva: float = 0.0):
    """
    Call calculate_bill in a way that is compatible with both 4-arg and 5-arg
    calculate_bill signatures (to avoid runtime crashes during mixed deployments).
    """
    params = inspect.signature(calculate_bill).parameters
    if "max_demand_kva" in params:
        return calculate_bill(year, quarter, category, kwh, max_demand_kva)
    return calculate_bill(year, quarter, category, kwh)

def calculate_kwh_from_bill(year, quarter, category, target, max_demand_kva: float = 0.0) -> float:
    low, high = 0.0, 50000.0
    for _ in range(25):
        mid = (low + high) / 2
        res = calculate_bill_compat(year, quarter, category, mid, max_demand_kva)
        if res and res.total_payable < target:
            low = mid
        else:
            high = mid
    return round(mid, 2)

# ----------------------------
# 3. UI LAYOUT
# ----------------------------
st.set_page_config(page_title="PURC Pro", layout="wide", initial_sidebar_state="collapsed")
logo_b64 = get_img_as_base64("purc_logo.png")

st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
        background-color: #FFFFFF !important;
        color: black !important;
    }
    .block-container { padding-top: 1rem !important; max-width: 1200px !important; margin: auto; background-color: #FFFFFF !important;}
    h1 { text-align: center; font-weight: 950; color: black; margin-top: 5px; margin-bottom: 0px;}
    .sub-header { text-align: center; color: #38bdf8 !important; font-weight: 800; margin-top: -10px; margin-bottom: 30px;}
    [data-testid="stWidgetLabel"] p, .stRadio label p, label, .stSelectbox p, div[data-testid="stMarkdownContainer"] p {
        color: black !important;
        font-weight: 700 !important;
    }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #E0E0E0 !important;
        border: 1px solid #ccc !important;
        color: black !important;
        border-radius: 5px;
    }
    div[data-baseweb="select"] span, div[data-baseweb="input"] input {
        color: black !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="select"] svg { fill: black !important; }
    .divider { border-bottom: 1px solid #eee; margin: 2px 0; }
</style>
""", unsafe_allow_html=True)

if logo_b64:
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_b64}" width="220"></div>', unsafe_allow_html=True)

st.markdown("<h1>PUBLIC UTILITIES REGULATORY COMMISSION</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>GAZETTED TARIFFS</p>", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    sel_year = st.selectbox("Tariff Control Period:", sorted(list(TARIFFS.keys()), reverse=True))

with c2:
    q_list = list(TARIFFS[sel_year].keys()) if TARIFFS[sel_year] else ["NO DATA"]
    sel_quarter = st.selectbox("Tariff Quarter:", q_list)

with c3:
    val_input = st.number_input("Enter Value:", min_value=0.0, value=350.0)

with c4:
    if sel_year in ["2017", "2018", "2019", "2020", "2021"]:
        cat_options = ["Residential", "Non-Residential", "SLT-LV", "SLT-MV", "SLT-HV", "SLT-HV MINES"]
    elif sel_year in ["2022", "2023"]:
        cat_options = ["Residential", "Non-Residential", "SLT-LV", "SLT-MV", "SLT-HV", "SLT-HV STEEL COMPANIES", "SLT-MINES"]
    else:
        cat_options = ["Residential", "Non-Residential", "SLT-LV", "SLT-MV", "SLT-MV2", "SLT-HV"]
    category = st.selectbox("Customer Category:", cat_options)

with c5:
    st.markdown('<p style="margin-bottom:5px; color:black;">Preference</p>', unsafe_allow_html=True)
    calc_mode = st.radio("Mode", ["Bill from kWh", "kWh from Bill"], horizontal=True, label_visibility="collapsed")

is_slt = category.startswith("SLT-")
needs_max_demand = sel_year == "2017" and is_slt
max_demand_input = 0.0
if needs_max_demand:
    max_demand_input = st.number_input("Maximum Demand (kVA):", min_value=0.0, value=0.0, step=1.0)

valid_year = sel_year in ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
valid_selection = valid_year and sel_quarter != "NO DATA"

if valid_selection:
    if calc_mode == "Bill from kWh":
        res = calculate_bill(sel_year, sel_quarter, category, val_input, max_demand_input)
    else:
        display_val = calculate_kwh_from_bill(sel_year, sel_quarter, category, val_input)
        res = calculate_bill(sel_year, sel_quarter, category, display_val, max_demand_input)

    r1, r2 = st.columns([1, 1])
    with r1:
        title = "TOTAL BILL (GHS)" if calc_mode == "Bill from kWh" else "REQUIRED CONSUMPTION (kWh)"
        v = res.total_payable if calc_mode == "Bill from kWh" else display_val
        st.markdown(f'<div style="font-size: 20px; font-weight: 800; color: #ef4444; margin-top: 30px; margin-bottom: 10px;">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 4.5rem; font-weight: 950; color: black; line-height: 1;">{v:,.2f}</div>', unsafe_allow_html=True)

    with r2:
        st.markdown("<p style='font-weight:950; border-bottom:2px solid #38bdf8; font-size:1.2rem; padding-bottom:5px; margin-top:20px; color: black;'>🧾 BILL BREAKDOWN</p>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; padding: 8px 0; color: black;'>
            <span><b>ENERGY CHARGE</b> <small style='color:#666;'>(GH₵)</small></span>
            <span style='font-family:monospace; font-weight:700; font-size:1.1rem;'>{res.energy_total:,.2f}</span>
        </div><div class="divider"></div>""", unsafe_allow_html=True)

        if res.demand_charge > 0:
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; padding: 8px 0; color: black;'>
                <span><b>MAX DEMAND CHARGE</b> <small style='color:#666;'>(GH₵)</small></span>
                <span style='font-family:monospace; font-weight:700; font-size:1.1rem;'>{res.demand_charge:,.2f}</span>
            </div>
            <div class="divider"></div>
            """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; padding: 8px 0; color: black;'>
            <span><b>SERVICE CHARGE</b> <small style='color:#666;'>(GH₵)</small></span>
            <span style='font-family:monospace; font-weight:700; font-size:1.1rem;'>{res.service_charge:,.2f}</span>
        </div><div class="divider"></div>""", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; padding: 8px 0; color: black;'>
            <span><b>LEVIES AND TAXES</b> <small style='color:#666;'>(GH₵)</small></span>
            <span style='font-family:monospace; font-weight:700; font-size:1.1rem;'>{res.levies_taxes_total:,.2f}</span>
        </div><div class="divider"></div>""", unsafe_allow_html=True)
else:
    st.markdown("<br><br><h2 style='text-align:center; color:black;'>No data for selected year yet.</h2>", unsafe_allow_html=True)
