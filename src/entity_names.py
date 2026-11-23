"""Shared entity spelling normalization; no issuer aliases or graph mutation."""
from __future__ import annotations
import re
import unicodedata

# USPS state names plus the District of Columbia. Company aliases take precedence
# over these tokens in scoring (e.g. a stock ticker can also be a postal code).
US_STATES = dict(zip(
    'AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split(),
    ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware',
     'Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana',
     'Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana',
     'Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina',
     'North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina',
     'South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia',
     'Wisconsin','Wyoming','District of Columbia'], strict=True))
_AMBIGUOUS_WORDS = {'IN', 'OR', 'ME', 'HI', 'ID', 'OK', 'AS'}


def entity_key(value: str, *, question: bool = False) -> str:
    """Normalize EXT IDs/display names, expanding postal codes token by token.

    In a whole question, words such as 'in' and 'or' require location context to
    become state mentions. Entity strings have no sentence grammar and accept
    lower-case postal abbreviations, including a final ', in' for Indiana.
    """
    value = re.sub(r'^EXT\s*:', '', unicodedata.normalize('NFKC', value), flags=re.I)
    words = list(re.finditer(r'[A-Za-z0-9]+', value))
    normalized = []
    for index, match in enumerate(words):
        word=match.group()
        code = word.upper()
        gap=value[words[index-1].end():match.start()] if index else ''
        location_context=',' in gap or '_' in gap or bool(re.search(r'\b(?:in|state of|jurisdiction of)\s*$',value[:match.start()],re.I))
        expand = code in US_STATES and (
            not question or code not in _AMBIGUOUS_WORDS or location_context)
        normalized.append(US_STATES[code].casefold() if expand else word.casefold())
    return ' '.join(normalized)
