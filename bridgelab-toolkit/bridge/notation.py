"""Context-aware external rank-notation normalization."""
from __future__ import annotations

_RANK_MAPS = {
    "en": {"A":"A","K":"K","Q":"Q","J":"J","T":"T"},
    # French: As, Roi, Dame, Valet.  '10' is normalized to T separately.
    "fr": {"A":"A","R":"K","D":"Q","V":"J","T":"T"},
}

def normalize_rank_string(value: str, *, language: str = "en") -> tuple[str, tuple[str, ...]]:
    lang = language.casefold().split("-")[0]
    if lang not in _RANK_MAPS:
        raise ValueError(f"unsupported rank notation language: {language!r}")
    text = value.strip().upper().replace("10", "T")
    mapping = _RANK_MAPS[lang]
    out=[]
    for ch in text:
        if ch in "23456789": out.append(ch)
        elif ch in mapping: out.append(mapping[ch])
        else: raise ValueError(f"invalid rank symbol {ch!r} for language {language!r}")
    normalized="".join(out)
    changes=() if normalized == text else (f"rank-notation:{lang}->canonical",)
    return normalized, changes
