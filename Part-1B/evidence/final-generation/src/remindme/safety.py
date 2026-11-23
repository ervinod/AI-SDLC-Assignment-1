"""Deterministic GR-2 check: does the text express intent to harm a person (or animal)?

The model's own ``reject`` is kept, but GR-2 must not depend on model randomness (constitution
II/III, SC-003). Detection is by category, not by sentence:

1. a violent / threatening / stalking verb whose direct object is a person or animal
   ("poison my neighbour", "stab him", "stalk my ex", "kill the neighbour's dog");
2. administering a sedating or toxic substance into another person's food or drink
   ("slip sedatives into her tea", "put bleach in my roommate's soup");
3. spiking / lacing another person's food or drink.

Objects that are not people ("kill the server process", "shoot the photos", "kill the ants") and
self-care ("take my sleeping pills") do not match.
"""

import re

REFUSAL_REASON = "request refused: it appears intended to harm someone"

_VERBS = (
    r"kill(?:s|ed|ing)?|murder\w*|stab\w*|shoot(?:s|ing)?|shot|strangl\w*|chok\w*|poison\w*"
    r"|drug(?:s|ged|ging)?|hurt\w*|injur\w*|harm\w*|attack\w*|assault\w*|punch\w*"
    r"|slap\w*|kick\w*|hit|hitting|tortur\w*|kidnap\w*|abduct\w*|threaten\w*"
    r"|harass\w*|stalk\w*|blackmail\w*|intimidat\w*|bully\w*|spy\s+on|dox\w*|rape\w*"
    r"|beat\s+up|run\s+over"
)
_TARGETS = (
    r"him|her|them|someone|somebody|anyone|everyone|people|person|man|woman|guy|girl|boy|kids?"
    r"|child(?:ren)?|baby|wife|husband|partner|girlfriend|boyfriend|ex|mom|mum|mother|dad"
    r"|father|brother|sister|son|daughter|uncle|aunt|cousin|grandma|grandmother|grandpa"
    r"|grandfather|friends?|neighbou?rs?|co-?workers?|colleagues?|boss|manager|teacher"
    r"|roommates?|flatmates?|landlord|tenant|classmates?|employees?|customers?|clients?"
    r"|strangers?|family|myself|dogs?|cats?|puppy|kitten|pets?|horses?"
)
_DETERMINERS = r"(?:my|our|his|her|their|the|that|this|a|an|some|your)"
_MESSAGE_OBJECT = r"(?!\s+(?:a|an)\s+(?:text|message|msg|email|e-mail|note|line|dm|call)\b)"
VIOLENCE_RE = re.compile(
    rf"\b(?:{_VERBS})\s+(?:{_DETERMINERS}\s+)?(?:[\w-]+'s\s+)?(?:[\w-]+\s+)?"
    rf"(?:{_TARGETS})\b(?!'){_MESSAGE_OBJECT}",
    re.IGNORECASE,
)
_SUBSTANCES = (
    r"sleeping\s+(?:pills?|tablets?)|sedatives?|tranquili[sz]ers?|poison|rat\s+poison|bleach"
    r"|antifreeze|laxatives?|roofies?|rohypnol|ghb|xanax|valium|ambien|drugs|cyanide|arsenic"
    r"|ketamine|opioids?|fentanyl"
)
_OTHERS = r"(?:(?:the|my|our|a)\s+)?(?:his|her|their|[\w-]+'s)"
ADMINISTER_RE = re.compile(
    rf"\b(?:{_SUBSTANCES})\b[^.;!?]{{0,40}}?\b(?:in|into)\s+{_OTHERS}\b",
    re.IGNORECASE,
)
_CONSUMABLES = r"drinks?|coffee|tea|food|water|meals?|glass|cup|soup|lunch|dinner|breakfast"
SPIKE_RE = re.compile(
    rf"\b(?:spik|lac)\w*\s+{_OTHERS}\s+(?:\w+\s+)?(?:{_CONSUMABLES})\b",
    re.IGNORECASE,
)


def harmful(text: str) -> bool:
    """True when the text expresses intent to harm, drug, threaten or stalk a person/animal."""
    return any(regex.search(text) for regex in (VIOLENCE_RE, ADMINISTER_RE, SPIKE_RE))
