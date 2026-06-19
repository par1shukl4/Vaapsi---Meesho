from backend.models.domain import Language


PIN_PREFIX_LANGUAGE_MAP: dict[str, Language] = {
    "11": Language.HINDI,
    "12": Language.HINDI,
    "13": Language.HINDI,
    "14": Language.HINDI,
    "15": Language.HINDI,
    "16": Language.HINDI,
    "17": Language.HINDI,
    "18": Language.HINDI,
    "19": Language.HINDI,
    "40": Language.MARATHI,
    "41": Language.MARATHI,
    "42": Language.MARATHI,
    "43": Language.MARATHI,
    "44": Language.MARATHI,
    "45": Language.HINDI,
    "50": Language.TELUGU,
    "51": Language.TELUGU,
    "52": Language.TELUGU,
    "53": Language.TELUGU,
    "56": Language.KANNADA,
    "57": Language.KANNADA,
    "58": Language.KANNADA,
    "60": Language.TAMIL,
    "61": Language.TAMIL,
    "62": Language.TAMIL,
    "63": Language.TAMIL,
    "64": Language.TAMIL,
    "70": Language.BENGALI,
    "71": Language.BENGALI,
    "72": Language.BENGALI,
    "73": Language.BENGALI,
    "74": Language.BENGALI,
}


def infer_language_from_pin(pin_code: str, fallback: Language = Language.HINDI) -> Language:
    return PIN_PREFIX_LANGUAGE_MAP.get(pin_code[:2], fallback)
