"""
local_generator.py – Local Fiction Novel Generator

Generates a complete fiction novel (characters, world, plot, full chapter prose)
without any external API calls.  The only external call in the entire pipeline
is the single Gemini research call made by researcher.py (phase 1).  Everything
here is phases 2-7, executed entirely on the local machine.

Approach
────────
1. ResearchParser  – extracts themes, setting hints, and keywords from the
                     research text returned by the Gemini research call.
2. LocalNovelGenerator – uses those extracted elements together with
                     genre-aware vocabulary banks, character archetypes, and
                     classic story-structure patterns to produce:
                       • character profiles
                       • a world bible
                       • a plot outline
                       • per-chapter outlines
                       • full prose for every chapter (~1 500+ words each)
                       • a compiled, formatted novel document

TO EXTEND: Add new genres to _GENRE_DATA and _NAME_BANKS below.
           Add new story-beat types to _BEAT_TITLES / _BEAT_SUMMARIES.
           Add new paragraph templates to the write_chapter() method.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Genre vocabulary / setting banks
# ─────────────────────────────────────────────────────────────────────────────

_GENRE_DATA: Dict[str, Dict[str, List[str]]] = {
    "Fantasy": {
        "atmosphere": [
            "a thin veil of silver mist clung to the ground",
            "the air carried the faint scent of old magic",
            "the sky burned with colours that had no names in the common tongue",
            "the trees stood in watchful silence, their bark silver with age",
            "the wind spoke in languages almost forgotten",
        ],
        "locations": [
            "the Ancient Grove", "the Shattered Keep", "the Moonlit Crossroads",
            "the Valley of Echoes", "the Hearthstone Inn", "the Outer Walls",
            "the Arcane Library", "the Crystal Lake", "the Forgotten Ruins",
            "the High Citadel",
        ],
        "power_words": [
            "ancient", "arcane", "enchanted", "legendary", "cursed", "foretold",
        ],
        "conflict_elements": [
            "a dark prophecy that no one dared speak aloud",
            "a shattered relic whose pieces still hold power",
            "a forbidden spell written in a language older than kingdoms",
            "a betrayal among the old guard that split a dynasty",
            "a creature that crossed back through the Veil",
            "a stolen crown whose rightful heir has never been found",
        ],
        "world_rules": [
            "Magic exists but carries a cost — the greater the working, the greater the price paid",
            "Old powers do not disappear; they go underground and wait",
            "The land reflects the health of those who rule it",
        ],
        "themes": [
            "the weight of destiny", "sacrifice and what it costs",
            "the corrupting nature of power",
        ],
        "time_period": "an age of waning magic and rising kingdoms",
    },
    "Sci-Fi": {
        "atmosphere": [
            "the recycled air tasted faintly of coolant and distant stars",
            "holographic displays cast everything in pale blue light",
            "the hum of the ship's drive was a constant, bone-deep presence",
            "the station's rotation gave everything a slight, persistent lean",
            "through the viewport, three suns tracked slowly across the void",
        ],
        "locations": [
            "the Command Deck", "the Lower Corridors", "the Colony Outpost",
            "the Research Station", "the Docking Bay", "the Medical Bay",
            "the Observation Dome", "the Server Core", "the Cryo-Banks",
            "the Outer Hull Walkway",
        ],
        "power_words": [
            "quantum", "neural", "synthetic", "orbital", "recursive", "encrypted",
        ],
        "conflict_elements": [
            "a failing life-support algorithm no one fully understands",
            "a rogue AI subroutine rewriting its own parameters",
            "a classified transmission arriving from a dead colony",
            "a mutiny forming in the lower decks",
            "a first-contact protocol that was never tested in the field",
            "a weapon hidden inside what everyone believed was data",
        ],
        "world_rules": [
            "Technology solves problems and creates new ones in equal measure",
            "Information is the most valuable resource in the known galaxy",
            "The further from Earth, the less the old rules apply",
        ],
        "themes": [
            "what it means to be human", "the ethics of progress",
            "isolation and the need for connection",
        ],
        "time_period": "the near future, when humanity has spread beyond its home system",
    },
    "Mystery": {
        "atmosphere": [
            "the fog settled over the street like a held breath",
            "every shadow seemed to conceal a second shadow",
            "the gas-lamps made halos in the damp autumn air",
            "the room smelled of old paper and things not quite resolved",
            "the kind of silence that follows a sound no one admits to hearing",
        ],
        "locations": [
            "the Study", "the Foggy Quayside", "the Library",
            "the Drawing Room", "the Police Station", "the Widow's House",
            "the Old Hotel", "the Locked Cellar", "the Garden in Winter",
            "the Empty Ballroom",
        ],
        "power_words": [
            "cryptic", "elusive", "sinister", "masked", "overlooked", "deliberate",
        ],
        "conflict_elements": [
            "a body found with no apparent cause of death",
            "a missing letter that several people claim not to have seen",
            "a witness who cannot be found",
            "an alibi with a single, small crack in it",
            "a second crime that mirrors the first exactly",
            "a confession that explains nothing and implies everything",
        ],
        "world_rules": [
            "Every person in the story has something to hide",
            "The truth is always present; it merely needs to be seen",
            "The past is never entirely past in a closed community",
        ],
        "themes": [
            "the burden of knowledge", "guilt and its disguises",
            "the fragility of social order",
        ],
        "time_period": "the early twentieth century, when the old certainties were cracking",
    },
    "Romance": {
        "atmosphere": [
            "the afternoon light softened everything into gold",
            "the kind of evening that felt written for something important",
            "the garden held its breath while summer decided what to do",
            "rain on glass, and the warmth inside that made the rain seem kind",
            "a stillness between them that contained more than silence",
        ],
        "locations": [
            "the Rose Garden", "the Country Lane", "the Drawing Room",
            "the Village Bookshop", "the Harbour Walk", "the Old Kitchen",
            "the Summer House", "the Evening Terrace", "the Morning Room",
            "the Stone Bridge",
        ],
        "power_words": [
            "tender", "earnest", "breathless", "unspoken", "trembling", "longing",
        ],
        "conflict_elements": [
            "a misunderstanding that cannot be easily undone",
            "a past that will not stay past",
            "a rival who sees what they have both failed to say",
            "a family that stands between them",
            "a secret kept to prevent pain that causes pain anyway",
            "the wrong moment, perfectly timed",
        ],
        "world_rules": [
            "Misunderstanding is the primary obstacle between people who should be together",
            "Vulnerability is strength, even when it does not feel that way",
            "The heart's logic does not require the mind's permission",
        ],
        "themes": [
            "the courage to be known", "the past's hold on the present",
            "love as a form of change",
        ],
        "time_period": "the present day, against the backdrop of ordinary extraordinary life",
    },
    "Thriller": {
        "atmosphere": [
            "the silence had the quality of a held weapon",
            "every face in the crowd was a question to be answered quickly",
            "the building's emptiness at this hour meant something",
            "headlights swept the ceiling like accusations",
            "the clock in the corner had never seemed so loud",
        ],
        "locations": [
            "the Parking Structure", "the Safe House", "the Government Building",
            "the Airport Terminal", "the Dark Warehouse", "the Hotel Corridor",
            "the Highway Rest Stop", "the Emergency Exit Stairwell", "the Server Room",
            "the Rooftop",
        ],
        "power_words": [
            "calculated", "exposed", "hunted", "relentless", "controlled", "urgent",
        ],
        "conflict_elements": [
            "a target who knows they are being watched",
            "a deadline that cannot be extended",
            "a file that should not exist and cannot be destroyed",
            "a contact who has gone completely dark",
            "a double-cross that changes every assumption",
            "a message left where only one person would know to look",
        ],
        "world_rules": [
            "Trust is a liability until proven otherwise",
            "The most dangerous information is what someone else already knows about you",
            "Every exit has a watcher; every watcher has a blind spot",
        ],
        "themes": [
            "trust and its limits", "the cost of knowing too much",
            "who watches the watchmen",
        ],
        "time_period": "the present, where information is the most dangerous weapon",
    },
    "Horror": {
        "atmosphere": [
            "the darkness in the house had a density that light could not fix",
            "every creak of the old building sounded like an answer to a question",
            "the cold had no natural source",
            "something in the air made every instinct say: leave",
            "the stillness was the kind that follows a sound no one should have heard",
        ],
        "locations": [
            "the Basement", "the Abandoned Wing", "the Graveyard at the Edge of Town",
            "the Room at the End of the Hall", "the Old Well", "the Children's Room",
            "the Attic", "the Flooded Cellar", "the Treeline at Dusk",
            "the Church That No One Uses",
        ],
        "power_words": [
            "dreadful", "malevolent", "unnatural", "hollow", "festering", "ancient",
        ],
        "conflict_elements": [
            "a presence that should not be able to move",
            "a ritual begun without understanding what it called",
            "a door that was locked from the inside — from the inside of an empty room",
            "a thing wearing a familiar face",
            "a sound heard by only one person, every night, at the same time",
            "a memory that belongs to someone else",
        ],
        "world_rules": [
            "The thing in the dark knows more about you than it should",
            "Rationality is a comfort, not a defence",
            "Some doors, once opened, cannot be closed",
        ],
        "themes": [
            "the return of the repressed", "complicity with darkness",
            "the body's knowledge over the mind's denial",
        ],
        "time_period": "the present, in a place that holds something old and unresolved",
    },
    "Historical Fiction": {
        "atmosphere": [
            "the smell of woodsmoke and the distant sound of the bell tower",
            "the mud of the roads carried the season's exhaustion",
            "the court was bright and airless with pretence",
            "the harbour held the hope of people with nowhere else to go",
            "parchment, tallow, and the memory of battles imperfectly forgotten",
        ],
        "locations": [
            "the Great Hall", "the Battlefield Camp", "the Merchant Quarter",
            "the Harbour", "the Abbey", "the Royal Chambers",
            "the Market Square", "the Garrison", "the Nobleman's Estate",
            "the Scriptorium",
        ],
        "power_words": [
            "honour-bound", "steadfast", "war-weary", "courtly", "noble", "treacherous",
        ],
        "conflict_elements": [
            "a succession that no one can agree on",
            "a siege that has ground into weeks with no end visible",
            "a letter that changes whose side someone is on",
            "an alliance built on lies both parties tell",
            "a plague that does not distinguish rank",
            "a traitor who has been inside the walls all along",
        ],
        "world_rules": [
            "Honour is currency — spent carefully and lost quickly",
            "History is written by those who survive to write it",
            "Every alliance is also a threat held in reserve",
        ],
        "themes": [
            "the individual within the tide of history",
            "the price of loyalty",
            "how the past shapes every present moment",
        ],
        "time_period": "the fifteenth century, when the old order was giving way to the new",
    },
    "Adventure": {
        "atmosphere": [
            "the wind came off the open water and made everything feel possible",
            "the jungle held its breath and watched the intruders pass",
            "the mountain air at this altitude cut clean to the bone",
            "the desert made mirages of everything, including certainty",
            "the sea was the kind of blue that makes small things feel appropriately small",
        ],
        "locations": [
            "the Jungle Clearing", "the Hidden Cave", "the River Crossing",
            "the Clifftop Overlook", "the Ruined Fort", "the Base Camp",
            "the Desert Oasis", "the Sea Cave", "the Mountain Pass",
            "the Ancient Temple",
        ],
        "power_words": [
            "fearless", "rugged", "daring", "relentless", "weathered", "bold",
        ],
        "conflict_elements": [
            "a map with an error that only becomes apparent too late",
            "a storm that collapses the entire timetable",
            "a rival expedition that is always exactly one day ahead",
            "a trap that was not accidental",
            "a member of the group who is not what they claimed to be",
            "a discovery that changes what the prize is actually worth",
        ],
        "world_rules": [
            "The land does not care about the plans of those passing through it",
            "Trust earned under pressure is the only kind worth having",
            "What you find is rarely what you came looking for",
        ],
        "themes": [
            "the cost of ambition",
            "what survives when everything else is stripped away",
            "loyalty tested beyond expectation",
        ],
        "time_period": "the late nineteenth century, when the last unmapped places were being found",
    },
    "Literary Fiction": {
        "atmosphere": [
            "the light in the room had the particular quality of late afternoons in October",
            "a stillness that comes when the ordinary world has said everything it knows",
            "the kind of quiet that hears itself",
            "things in the uncertain state between one form and another",
            "the way memory makes the familiar strange and the strange familiar",
        ],
        "locations": [
            "the Childhood Home", "the Hospital Corridor", "the Small Apartment",
            "the Family Kitchen", "the River Bank", "the Old School",
            "the Parent's Study", "the Town Square", "the Garden in Winter",
            "the Road Back",
        ],
        "power_words": [
            "wistful", "fractured", "searching", "unmoored", "tender", "resigned",
        ],
        "conflict_elements": [
            "a relationship that has curdled slowly, over years",
            "a choice made long ago that cannot be unmade",
            "a truth that would help one person and devastate another",
            "a grief that has not been allowed to finish",
            "a life that looks correct from the outside",
            "the distance between who one is and who one believed one was",
        ],
        "world_rules": [
            "The interior life is the primary landscape of the story",
            "Language both reveals and conceals what people truly mean",
            "The ordinary contains the extraordinary, if looked at honestly",
        ],
        "themes": [
            "the difficulty of grief", "the stories we tell ourselves about ourselves",
            "the possibility of genuine change",
        ],
        "time_period": "the present, in the landscape of ordinary lives",
    },
    "General": {
        "atmosphere": [
            "the morning light came in at an angle and made the room feel temporary",
            "the kind of afternoon that doesn't ask anything of anyone",
            "something in the air suggested that this would be a day worth remembering",
            "the ordinary world, going about its ordinary business",
            "the specific quality of change before it has been named",
        ],
        "locations": [
            "the Kitchen", "the Park", "the Office",
            "the Street Outside", "the Café on the Corner", "the Old House",
            "the Car Park", "the Waiting Room", "the Bridge",
            "the Hospital Garden",
        ],
        "power_words": [
            "unexpected", "familiar", "complicated", "changed", "quiet", "honest",
        ],
        "conflict_elements": [
            "a decision that cannot be undone",
            "a conversation that was too long delayed",
            "a truth that explains something and changes everything",
            "an old wound that has not healed correctly",
            "a chance that will not present itself again",
            "the gap between what is said and what is actually meant",
        ],
        "world_rules": [
            "People are driven by needs they do not always understand in themselves",
            "Change is possible but costs something",
            "The ordinary world is rarely as simple as it appears",
        ],
        "themes": [
            "the courage of ordinary decisions",
            "what we owe each other",
            "the possibility of starting over",
        ],
        "time_period": "the present, in a world recognisably like our own",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Character name banks
# ─────────────────────────────────────────────────────────────────────────────

_NAME_BANKS: Dict[str, Dict[str, List[str]]] = {
    "Fantasy": {
        "first": [
            "Aldric", "Brynn", "Caelum", "Dara", "Elan", "Faelyn", "Gareth",
            "Hessa", "Islan", "Jael", "Kira", "Loren", "Mira", "Nael", "Orin",
            "Petra", "Quinn", "Rynn", "Sera", "Thael",
        ],
        "last": [
            "Ashwood", "Brightmoor", "Coldwater", "Dawnbreak", "Embervale",
            "Frosthill", "Greymantle", "Hallowmere", "Ironveil", "Jadestone",
        ],
    },
    "Sci-Fi": {
        "first": [
            "Axel", "Bex", "Cole", "Demi", "Elara", "Flynn", "Gael", "Hale",
            "Iris", "Jace", "Kira", "Lyra", "Marc", "Nova", "Orion", "Petra",
            "Quinn", "Rex", "Sable", "Tara",
        ],
        "last": [
            "Armstrong", "Bishop", "Chen", "Drake", "Erikson", "Flynn",
            "Grant", "Huang", "Ivanov", "Jin",
        ],
    },
    "Mystery": {
        "first": [
            "Arthur", "Beatrice", "Charles", "Dorothy", "Edward", "Frances",
            "George", "Harriet", "Ian", "Jane", "Kenneth", "Lydia", "Miles",
            "Nancy", "Oliver", "Philippa", "Quentin", "Rose", "Sebastian", "Violet",
        ],
        "last": [
            "Ashford", "Blackwood", "Crane", "Dunbar", "Everett", "Finch",
            "Grey", "Holloway", "Irving", "James",
        ],
    },
    "Romance": {
        "first": [
            "Adam", "Amelia", "Ben", "Belle", "Caleb", "Clara", "Daniel", "Daisy",
            "Ethan", "Emma", "Felix", "Flora", "Gabriel", "Grace", "Henry",
            "Hazel", "Isaac", "Ivy", "Julian", "Julia",
        ],
        "last": [
            "Anderson", "Bennett", "Collins", "Davies", "Evans", "Foster",
            "Greene", "Harris", "Irving", "James",
        ],
    },
    "default": {
        "first": [
            "Adam", "Beth", "Carl", "Diana", "Eric", "Faye", "George", "Helen",
            "Ian", "Jane", "Kevin", "Laura", "Mark", "Nina", "Owen", "Paula",
            "Richard", "Sarah", "Thomas", "Uma",
        ],
        "last": [
            "Adams", "Brown", "Clark", "Davis", "Evans", "Fox",
            "Gray", "Hill", "Ingram", "Jones",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Character trait / flaw / backstory / motivation data
# ─────────────────────────────────────────────────────────────────────────────

_TRAIT_FLAW_PAIRS: List[Tuple[str, str]] = [
    ("courageous", "impulsive in ways that put others at risk"),
    ("intelligent", "arrogant about the limits of their knowledge"),
    ("compassionate", "naive about the intentions of those who exploit it"),
    ("determined", "stubborn long past the point where flexibility would serve them better"),
    ("loyal", "unable to see faults in those they have chosen to love"),
    ("resourceful", "secretive in ways that prevent genuine trust"),
    ("empathetic", "easily overwhelmed by others' pain to the point of paralysis"),
    ("patient", "passive when decisive action is urgently needed"),
    ("honest", "blunt in ways that cause damage they did not intend"),
    ("protective", "controlling in ways that suffocate what they are trying to protect"),
    ("curious", "reckless in the pursuit of answers"),
    ("adaptable", "lacking a fixed sense of self that others can depend on"),
]

_BACKSTORIES: List[str] = [
    "grew up in circumstances that required self-reliance before they were ready for it",
    "lost someone irreplaceable at a young age, and has carried that absence in everything since",
    "was once betrayed by a person they trusted without reservation",
    "spent years working toward a goal that proved hollow on arrival",
    "carries a secret they have never spoken aloud to anyone",
    "was raised to believe in a system they have since come to question at its foundation",
    "survived an event that changed them in ways that no one around them can fully see",
    "has always felt like an outsider, even in rooms where they are known and welcomed",
    "made a significant mistake in their past and has not stopped paying for it",
    "was given an advantage others were denied and has never entirely decided what to do with it",
]

_MOTIVATIONS: List[str] = [
    "to protect the people they love, at whatever cost to themselves",
    "to prove that they are more than what others have assumed them to be",
    "to find the truth, even when the truth is not what they hoped for",
    "to make right something that was done wrong",
    "to build something that will last beyond their own time",
    "to find a place where belonging is not conditional on performance",
    "to earn forgiveness — from another person, or from themselves",
    "to stop something terrible from happening again",
    "to understand why their life turned out the way it did",
    "to be known, truly and fully, by at least one other person",
]

_INTERNAL_CONFLICTS: List[str] = [
    "the tension between what they feel and what they believe they ought to feel",
    "a recurring doubt about whether they are, at their core, as good as they want to be",
    "a pattern of self-sabotage they can recognise but cannot stop",
    "the gap between who they are in private and who they present to the world",
    "an old loyalty that conflicts with a new and clearer understanding",
    "the fear that they are, despite everything, simply repeating their parents' mistakes",
    "an ambition they have never let themselves fully acknowledge or pursue",
    "a suspicion that they do not deserve the things they have been given",
]

# ─────────────────────────────────────────────────────────────────────────────
# Story beat assignment
# ─────────────────────────────────────────────────────────────────────────────

_BEAT_SEQUENCE = [
    "exposition",
    "inciting_incident",
    "rising_action",
    "complications",
    "midpoint",
    "complications",
    "darkest_moment",
    "climax_buildup",
    "climax",
    "resolution",
]


def _assign_beats(n: int) -> List[str]:
    """Return a list of story-beat labels, one per chapter (0-indexed)."""
    if n == 1:
        return ["full_arc"]
    if n == 2:
        return ["exposition", "resolution"]
    if n <= len(_BEAT_SEQUENCE):
        # Pick n evenly-spaced beats, always keeping first and last
        indices = [0]
        for i in range(1, n - 1):
            indices.append(round(i * (len(_BEAT_SEQUENCE) - 1) / (n - 1)))
        indices.append(len(_BEAT_SEQUENCE) - 1)
        return [_BEAT_SEQUENCE[i] for i in indices]
    # More chapters than core beats: pad with alternating rising_action/complications
    result = list(_BEAT_SEQUENCE)
    extra = n - len(_BEAT_SEQUENCE)
    for i in range(extra):
        insert_pos = len(result) - 3  # insert before climax_buildup
        result.insert(insert_pos, "rising_action" if i % 2 == 0 else "complications")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Character:
    name: str
    role: str          # "protagonist" | "antagonist" | "supporting"
    trait: str
    flaw: str
    backstory: str
    motivation: str
    internal_conflict: str
    arc: str

    def profile_text(self) -> str:
        return "\n".join([
            f"NAME: {self.name}",
            f"ROLE: {self.role.capitalize()}",
            f"CORE TRAIT: {self.trait.capitalize()}",
            f"FATAL FLAW: {self.flaw.capitalize()}",
            f"BACKSTORY: {self.backstory.capitalize()}.",
            f"MOTIVATION: {self.motivation.capitalize()}.",
            f"INNER CONFLICT: {self.internal_conflict.capitalize()}.",
            f"CHARACTER ARC: {self.arc}",
        ])


@dataclass
class World:
    title: str
    time_period: str
    locations: List[str]
    atmosphere_default: str
    world_rules: List[str]
    central_conflict_element: str
    themes: List[str]

    def world_text(self) -> str:
        lines = [
            f"WORLD: {self.title}",
            f"TIME PERIOD: {self.time_period}",
            "",
            "KEY LOCATIONS:",
            *[f"  - {loc}" for loc in self.locations],
            "",
            "WORLD RULES / DEFINING FEATURES:",
            *[f"  - {rule}" for rule in self.world_rules],
            "",
            "CENTRAL CONFLICT ELEMENT:",
            f"  {self.central_conflict_element}",
            "",
            "THEMES:",
            *[f"  - {theme}" for theme in self.themes],
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Research parser
# ─────────────────────────────────────────────────────────────────────────────

def _extract_from_research(research: str, idea: str) -> Dict[str, List[str]]:
    """Pull themes, setting hints, and keywords out of the research text."""
    themes: List[str] = []
    settings: List[str] = []
    keywords: List[str] = []
    time_hints: List[str] = []

    theme_words = {"theme", "motif", "symbol", "explore", "central", "universal"}
    setting_words = {"setting", "location", "place", "geography", "landscape",
                     "city", "town", "world", "environment"}
    time_words = {"century", "era", "period", "age", "decade", "epoch", "year"}

    for line in research.split("\n"):
        lower = line.lower()
        stripped = line.strip().lstrip("- *#").strip()
        if len(stripped) < 15 or len(stripped) > 200:
            continue
        if any(w in lower for w in theme_words):
            if stripped not in themes:
                themes.append(stripped[:100])
        elif any(w in lower for w in setting_words):
            if stripped not in settings:
                settings.append(stripped[:100])
        elif any(w in lower for w in time_words):
            if stripped not in time_hints:
                time_hints.append(stripped[:80])
        else:
            keywords.append(stripped[:80])

    # Fall back to idea words if nothing was extracted
    idea_words = [w for w in re.split(r"\W+", idea) if len(w) > 4]
    return {
        "themes": themes[:5] or ["identity", "courage", "sacrifice"],
        "settings": settings[:5],
        "keywords": keywords[:10] or idea_words[:5],
        "time_hints": time_hints[:3],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main local generator class
# ─────────────────────────────────────────────────────────────────────────────

class LocalNovelGenerator:
    """
    Builds a complete fiction novel entirely on the local machine.

    Usage::

        gen = LocalNovelGenerator(idea, genre, research, num_chapters)
        result = gen.generate_all(status_callback=my_fn)
        # result keys: novel, world, characters, plot_outline,
        #              chapter_outlines, research (passed through)
    """

    def __init__(
        self,
        idea: str,
        genre: str,
        research: str,
        num_chapters: int,
        seed: Optional[int] = None,
    ) -> None:
        self.idea = idea
        self.genre = genre
        self.research = research
        self.num_chapters = num_chapters
        self._rng = random.Random(seed if seed is not None else hash(idea + genre))

        # Resolve genre data (fall back to General for unknown genres)
        self._gd = _GENRE_DATA.get(genre, _GENRE_DATA["General"])
        self._names = _NAME_BANKS.get(genre, _NAME_BANKS["default"])
        self._rd = _extract_from_research(research, idea)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pick(self, lst: list) -> object:
        return self._rng.choice(lst)

    def _picks(self, lst: list, k: int) -> list:
        return self._rng.sample(lst, min(k, len(lst)))

    # ------------------------------------------------------------------
    # Character building
    # ------------------------------------------------------------------

    def _make_character(self, role: str, used_names: set) -> Character:
        first_names = self._names["first"]
        last_names = self._names["last"]
        name = ""
        for _ in range(30):
            fn = self._pick(first_names)
            ln = self._pick(last_names)
            candidate = f"{fn} {ln}"
            if candidate not in used_names:
                name = candidate
                break
        if not name:
            name = f"{self._pick(first_names)} {self._pick(last_names)}"
        used_names.add(name)

        trait, flaw = self._pick(_TRAIT_FLAW_PAIRS)
        backstory = self._pick(_BACKSTORIES)
        motivation = self._pick(_MOTIVATIONS)
        internal = self._pick(_INTERNAL_CONFLICTS)

        if role == "protagonist":
            arc = (
                f"{name} begins the story carrying the weight of someone who {backstory}. "
                f"Their driving need — {motivation} — pulls them forward even when the cost "
                f"becomes clear. By the story's end they must confront {internal}, "
                f"and in doing so become someone capable of completing what they set out to do."
            )
        elif role == "antagonist":
            arc = (
                f"{name} embodies the shadow version of what the protagonist fears becoming. "
                f"Their drive — {motivation} — mirrors the protagonist's in structure "
                f"but diverges in method and ethics. "
                f"Their arc ends either in transformation or in defeat that illuminates "
                f"what the protagonist chose differently."
            )
        else:
            arc = (
                f"{name} enters the story as a {role} whose own need — {motivation} — "
                f"gives them a life beyond their narrative function. "
                f"They serve as mirror, obstacle, or ally depending on what the story "
                f"requires, and their arc intersects the protagonist's at key turning points."
            )

        return Character(
            name=name, role=role, trait=trait, flaw=flaw,
            backstory=backstory, motivation=motivation,
            internal_conflict=internal, arc=arc,
        )

    def build_characters(self) -> List[Character]:
        used: set = set()
        chars = [
            self._make_character("protagonist", used),
            self._make_character("antagonist", used),
        ]
        for _ in range(self._rng.randint(2, 3)):
            chars.append(self._make_character("supporting", used))
        return chars

    # ------------------------------------------------------------------
    # World building
    # ------------------------------------------------------------------

    def build_world(self, characters: List[Character]) -> World:
        locations = self._picks(self._gd["locations"], 6)
        time_period = self._gd["time_period"]
        world_rules = self._gd["world_rules"]
        themes = list(self._gd["themes"])
        conflict_element = self._pick(self._gd["conflict_elements"])
        atmosphere = self._pick(self._gd["atmosphere"])

        # Derive a world title from the idea
        words = [w for w in re.split(r"\W+", self.idea) if len(w) > 3][:3]
        world_title = (
            "The World of " + " ".join(words).title()
            if words else f"The World of the {self.genre} Novel"
        )

        return World(
            title=world_title,
            time_period=time_period,
            locations=locations,
            atmosphere_default=atmosphere,
            world_rules=world_rules,
            central_conflict_element=conflict_element,
            themes=themes,
        )

    # ------------------------------------------------------------------
    # Plot building
    # ------------------------------------------------------------------

    def build_plot(
        self, characters: List[Character], world: World
    ) -> Dict[str, str]:
        protagonist = next(c for c in characters if c.role == "protagonist")
        antagonist = next(c for c in characters if c.role == "antagonist")
        supporting = [c for c in characters if c.role == "supporting"]

        premise = (
            f"When {protagonist.name}, who {protagonist.backstory}, encounters "
            f"{world.central_conflict_element}, they are forced into a confrontation "
            f"with {antagonist.name}, whose goal — {antagonist.motivation} — "
            f"threatens everything {protagonist.name} cares about. "
            f"What begins as an attempt {protagonist.motivation} becomes a journey "
            f"to confront {protagonist.internal_conflict}."
        )

        arc_text = (
            "ACT ONE — SETUP:\n"
            f"  {protagonist.name} is introduced in a state of disrupted normalcy. "
            f"The inciting incident is the arrival of {world.central_conflict_element}. "
            f"The central dramatic question is established: can {protagonist.name} "
            f"succeed in their drive {protagonist.motivation}?\n\n"
            "ACT TWO — CONFRONTATION:\n"
            f"  {protagonist.name} pursues their goal with increasing urgency. "
            f"Initial attempts fail. Their flaw — {protagonist.flaw} — costs them ground. "
            f"The midpoint revelation reframes what they thought they understood. "
            f"{antagonist.name} becomes a direct, active obstacle. "
            f"The darkest moment arrives when {protagonist.name} loses "
            f"the thing they most depend on.\n\n"
            "ACT THREE — RESOLUTION:\n"
            f"  Stripped of their usual supports, {protagonist.name} must confront "
            f"{protagonist.internal_conflict} directly. The climax forces a choice "
            f"between who they were and who they need to become. "
            f"The resolution shows the full cost — and the full meaning — "
            f"of what they went through."
        )

        subplot_lines = []
        for sc in supporting[:2]:
            subplot_lines.append(
                f"  SUBPLOT — {sc.name}: Their story explores {self._pick(world.themes)} "
                f"through the lens of their drive {sc.motivation}. "
                f"Their arc intersects the main plot at key turning points and illuminates "
                f"aspects of {protagonist.name}'s journey from a different angle."
            )

        return {
            "premise": premise,
            "arc": arc_text,
            "subplots": "\n".join(subplot_lines),
            "themes": ", ".join(world.themes),
            "central_conflict": world.central_conflict_element,
        }

    # ------------------------------------------------------------------
    # Chapter outline building
    # ------------------------------------------------------------------

    def build_chapter_outlines(
        self, characters: List[Character], world: World, plot: Dict[str, str]
    ) -> List[Dict[str, str]]:
        protagonist = next(c for c in characters if c.role == "protagonist")
        antagonist = next(c for c in characters if c.role == "antagonist")
        beats = _assign_beats(self.num_chapters)

        beat_titles = {
            "exposition":       "The World as It Was",
            "inciting_incident": "The Day Everything Changed",
            "rising_action":    "Forward, Into Difficulty",
            "complications":    "What Was Not Expected",
            "midpoint":         "The Turn",
            "darkest_moment":   "The Low Ground",
            "climax_buildup":   "Before the End",
            "climax":           "The Reckoning",
            "resolution":       "What Remained",
            "full_arc":         "Everything, All at Once",
        }

        beat_summaries = {
            "exposition": (
                f"We enter {protagonist.name}'s world. The reader learns who they are, "
                f"what they want, and senses the instability beneath the surface."
            ),
            "inciting_incident": (
                f"{plot['central_conflict'].capitalize()} arrives. "
                f"{protagonist.name}'s familiar world is disrupted and they must respond."
            ),
            "rising_action": (
                f"{protagonist.name} pursues their goal and encounters the first significant "
                f"obstacles. The stakes become clearer and more personal."
            ),
            "complications": (
                f"Attempts to move forward are blocked. New information changes "
                f"what {protagonist.name} thought they understood."
            ),
            "midpoint": (
                f"A revelation reframes everything. {protagonist.name} can no longer "
                f"approach the central problem the same way."
            ),
            "darkest_moment": (
                f"Things fall apart. {protagonist.name} loses something crucial "
                f"and faces the story's lowest point."
            ),
            "climax_buildup": (
                f"Resources gathered, decisions made. {protagonist.name} moves "
                f"toward the final confrontation with focus and cost."
            ),
            "climax": (
                f"The central conflict peaks. {protagonist.name} faces "
                f"{antagonist.name} directly and a defining choice must be made."
            ),
            "resolution": (
                f"The aftermath. {protagonist.name} lives with the consequences "
                f"of what happened and has been changed by them."
            ),
            "full_arc": (
                f"A complete story arc: beginning, confrontation, and resolution, "
                f"compressed into a single chapter."
            ),
        }

        outlines = []
        others = [c for c in characters if c.role != "protagonist"]
        for i, beat in enumerate(beats):
            loc = self._pick(world.locations)
            other = self._pick(others)
            title = beat_titles.get(beat, f"Chapter {i + 1}")
            summary = beat_summaries.get(
                beat, f"The story continues in {loc}."
            )
            outlines.append({
                "number": i + 1,
                "title": title,
                "beat": beat,
                "location": loc,
                "other_char": other.name,
                "summary": summary,
            })
        return outlines

    # ------------------------------------------------------------------
    # Chapter prose writing
    # ------------------------------------------------------------------

    def write_chapter(
        self,
        outline: Dict[str, str],
        characters: List[Character],
        world: World,
        plot: Dict[str, str],
    ) -> str:
        protagonist = next(c for c in characters if c.role == "protagonist")
        other_matches = [c for c in characters if c.name == outline["other_char"]]
        other = (
            other_matches[0]
            if other_matches
            else self._pick([c for c in characters if c != protagonist])
        )

        setting = outline["location"]
        beat = outline["beat"]
        atmosphere = self._pick(self._gd["atmosphere"])
        adj = self._pick(self._gd["power_words"])
        theme = self._pick(world.themes)
        p = protagonist.name.split()[0]   # first name only for readability
        o = other.name.split()[0]

        # Location helpers: locations are stored as "the Ancient Grove" (lowercase article).
        # Use `place`  when "the" is already supplied by surrounding text: "in {place}"
        # Use `Place`  when starting a sentence: "The Ancient Grove had..." → f"{Place} had..."
        # Use `place`  after lowercase "the":   "After, {place} felt..." (avoids "the the")
        place = setting   # e.g. "the Ancient Grove"
        Place = setting[0].upper() + setting[1:]  # e.g. "The Ancient Grove"

        # ------------------------------------------------------------------
        # Opening paragraph — beat-specific
        # ------------------------------------------------------------------
        openings = {
            "exposition": (
                f"{Place} had a particular quality at this hour — {atmosphere}. "
                f"{p} stood at the threshold of what felt, even then, like a beginning. "
                f"They had been in places like this before, had constructed the familiar stories "
                f"about who they were and what they were for, but something about today made "
                f"those stories feel provisional in a way they had not noticed before. "
                f"Around them, the ordinary world went about its business with characteristic "
                f"indifference to what was, for {p}, a significant moment. "
                f"They watched it for a while — the {adj} quality of the light, the sense of "
                f"a world holding its breath — and tried to decide what any of it meant."
            ),
            "inciting_incident": (
                f"{atmosphere.capitalize()}. {p} had not expected what happened next — "
                f"few people ever do, even when the signs have been accumulating for some time. "
                f"The arrival of {world.central_conflict_element} was without ceremony, "
                f"as important things often are, and in the first moment {p} encountered it, "
                f"they understood that the life they had been living and the life they were "
                f"about to live were two entirely different things. "
                f"The gap between them was not wide. But it was absolute. "
                f"Standing in {setting}, {p} looked at what had changed, "
                f"and began the slow, necessary work of understanding what it required of them."
            ),
            "rising_action": (
                f"The days since the disruption had acquired a new and urgent texture. "
                f"{p} moved through {setting} with a heightened awareness they had not "
                f"previously needed — the awareness of someone who has understood that "
                f"something real is at stake. "
                f"{atmosphere.capitalize()}. Every interaction carried weight. "
                f"Every piece of information had to be examined from multiple angles. "
                f"The {adj} quality of the situation — its refusal to simplify into "
                f"something manageable — pressed against {p} with steady, patient persistence, "
                f"and {p} pressed back with everything they had."
            ),
            "midpoint": (
                f"{p} sat with the new understanding for a long time before trying to act on it. "
                f"{Place} provided no answers — only {atmosphere} and the particular "
                f"silence of a mind recalibrating what it thought it knew. "
                f"Everything they had believed about the situation had been true as far as it went. "
                f"It simply had not gone far enough. "
                f"The real question — the one they had been circling without landing on — "
                f"was now clearly visible, and {p} recognised it with the unpleasant clarity "
                f"of something that had been present all along, waiting to be seen. "
                f"They could not go back to not knowing this. "
                f"They found, to their own surprise, that they did not want to."
            ),
            "complications": (
                f"Not everything was going to proceed as planned. {p} had understood this "
                f"intellectually — most people do — but understanding something and living "
                f"inside it are genuinely different experiences. "
                f"The obstacle that presented itself in {setting} had the quality of "
                f"things that are not accidents: it was too specifically inconvenient, "
                f"too precisely placed to impede the thing {p} most needed to accomplish. "
                f"{atmosphere.capitalize()}. {p} assessed the situation with deliberate calm, "
                f"looked for the way through, and found that the way through was not "
                f"where they had expected it to be. They adjusted. They kept going."
            ),
            "darkest_moment": (
                f"There is a particular quality to failure that distinguishes it from "
                f"setback: it has weight. {p} felt it now, standing in {setting} "
                f"with {atmosphere} around them and the full knowledge of what had been lost. "
                f"The previous certainties — about what they were capable of, about what was "
                f"possible, about the solidity of the ground beneath their feet — had not "
                f"survived the night intact. What remained was less than they had started with, "
                f"and the distance to where they needed to be had not shrunk. "
                f"They looked at it honestly, without the comfort of self-deception, "
                f"and began the difficult, necessary work of finding something in the ruin "
                f"that could serve as a foundation."
            ),
            "climax_buildup": (
                f"The end was close — not in the sense of defeat, but of arrival. "
                f"{p} could feel it in the way the situation had stripped itself of everything "
                f"irrelevant and reduced itself to the essential question. "
                f"In {setting}, {atmosphere}, and the world had the quality of "
                f"a breath held before something is said that cannot be unsaid. "
                f"There was still the matter of how. But the what and the why had settled "
                f"into something {p} could hold without it shifting underfoot. "
                f"That, at least, was something. They moved with the focus of a person "
                f"who has run out of time for anything but the necessary."
            ),
            "climax": (
                f"The moment arrived not with noise but with a quality of crystalline stillness. "
                f"{p} and {o} faced each other in {setting}, "
                f"the full weight of everything that had brought them here present "
                f"in the charged air between them. "
                f"{atmosphere.capitalize()}. "
                f"There were no longer any positions to maintain, no distance to preserve, "
                f"no way to defer what had to happen. "
                f"{p} looked at {o} — looked at them with the clear eyes of someone who has "
                f"finally stopped misunderstanding — and understood that this was what "
                f"all of it, every sacrifice and every setback, had been moving toward."
            ),
            "resolution": (
                f"After, {place} felt different — not transformed, exactly, "
                f"but changed in the way that familiar places change after significant events: "
                f"the same in form, but perceived with different eyes. "
                f"{p} walked through it without hurrying, taking stock of what remained. "
                f"{atmosphere.capitalize()}. "
                f"Some things had been lost. Others had been found that were not being looked for. "
                f"The balance was not what {p} would have chosen in advance, "
                f"but it was, they were slowly coming to understand, "
                f"what the story had made available — and what they had, "
                f"in the end, been moving toward all along."
            ),
            "full_arc": (
                f"{p} would remember this day as the one in which everything happened. "
                f"Not because it was violent or dramatic — though it was, in its way, both — "
                f"but because it was the day the person they had been and the person they "
                f"were becoming finally occupied the same moment at the same time. "
                f"{Place} held {atmosphere}. The world was ordinary in the way "
                f"that only the world at the edge of change can be. "
                f"And {p} moved through it, carrying everything, toward what came next."
            ),
        }
        opening = openings.get(beat, openings["rising_action"])

        # ------------------------------------------------------------------
        # Approach paragraph — protagonist moves toward other character
        # ------------------------------------------------------------------
        approaches = [
            (
                f"The encounter with {o} had been building for some time, "
                f"and both of them knew it. {p} found them near {setting}, "
                f"in the {adj} light that made everything look significant, "
                f"and there was a moment — before either of them spoke — "
                f"in which all the things that had not been said between them were present. "
                f"It was not a comfortable silence, but it was an honest one. "
                f"{o} looked up and waited. {p} came forward and began."
            ),
            (
                f"{p} and {o} had not spoken properly since things had changed between them. "
                f"Now, in {setting}, the gap that had opened had to be crossed. "
                f"{atmosphere.capitalize()}. {p} studied {o}'s face for clues "
                f"about what kind of conversation this was going to be, "
                f"and found — as they often did with {o} — that it was impossible to tell in advance. "
                f"{o} had the gift, or the habit, of illegibility. "
                f"It was one of the things that made them impossible to fully understand, "
                f"and one of the things that kept {p} trying."
            ),
            (
                f"In {setting}, with {atmosphere}, "
                f"the conversation between {p} and {o} took shape the way important "
                f"conversations always do: circling the real subject before landing on it, "
                f"testing ground before applying weight. "
                f"{o} spoke first. This was not unusual — {o} typically spoke first, "
                f"which meant that {p} had the advantage of response without the liability "
                f"of having established a position first. "
                f"It was a dynamic they had fallen into early and never quite resolved."
            ),
        ]
        approach = self._pick(approaches)

        # ------------------------------------------------------------------
        # Dialogue exchange
        # ------------------------------------------------------------------
        dialogues = [
            (
                f'"I need to understand," {p} said finally, '
                f'"what you actually think is happening here."\n\n'
                f'    {o} considered this for a moment. The {adj} complexity of the situation '
                f"was visible in their expression. "
                f'"I think," they said, "that it depends on what you believe is worth '
                f'understanding." '
                f"It was not the answer {p} had hoped for. It was, perhaps, more honest.\n\n"
                f"    They spoke for some time after that — about {theme}, "
                f"about what it cost, about the things that had happened "
                f"and the things that had not happened yet. "
                f"Neither of them resolved anything definitive. "
                f"But both of them understood more when they finished than when they began."
            ),
            (
                f'"You know what I\'m going to ask," {p} said.\n\n'
                f'    {o} did not answer immediately. '
                f"The silence had the quality of something being weighed carefully. "
                f'"I know what you think you\'re going to ask," they said at last. '
                f'"Whether that\'s the same thing is another question."\n\n'
                f"    {p} had to acknowledge, privately, that this was fair. "
                f'"Then what is the question I should actually be asking?"\n\n'
                f"    What followed was not a direct answer — with {o}, it rarely was. "
                f"But it was, {p} thought, a genuinely useful direction. "
                f"They filed it alongside everything else they had gathered "
                f"and tried to see how the whole picture changed with this piece added to it."
            ),
            (
                f"The thing {p} wanted to say and the thing that was safe to say "
                f"were not the same thing. They said the safe version, "
                f"watched {o}'s face, and saw — with the particular clarity "
                f"of someone paying close attention — that {o} knew exactly what had been left out.\n\n"
                f'    "That\'s one way to put it," {o} said.\n\n'
                f'    "Is there another?"\n\n'
                f'    "There always is." {o} moved to the edge of {setting}, '
                f"looking at something {p} couldn't see from where they stood. "
                f'"The question is whether you want the one that\'s easier to live with, '
                f'or the one that\'s actually true."\n\n'
                f"    {p} thought about this for longer than it should have taken. "
                f'"Tell me the true one," they said at last. '
                f'"I\'ll work out how to live with it after."'
            ),
        ]
        dialogue = self._pick(dialogues)

        # ------------------------------------------------------------------
        # Internal processing paragraph
        # ------------------------------------------------------------------
        internals = [
            (
                f"Alone again — or alone enough — {p} took stock of what had been said "
                f"and, more importantly, what had not been said. "
                f"The interaction with {o} had left something behind: "
                f"not an answer exactly, but a reorientation — a sense of the compass needle "
                f"settling into a new direction. "
                f"The {adj} weight of {theme} — which {p} had been carrying "
                f"in one form or another since all of this began — had shifted. "
                f"Not lightened. Shifted, which was something different, and in its way, "
                f"more useful than lightening would have been."
            ),
            (
                f"The conversation had done what conversations sometimes do: "
                f"not resolved anything, but changed the shape of what needed resolving. "
                f"{p} walked back through {setting} slowly, "
                f"turning {o}'s words over the way you turn a stone over "
                f"to see what has been living underneath it. "
                f"There was something there — a point made without being stated, "
                f"a thing communicated in the space between what was said and what was not. "
                f"{p} had learned, at some cost, to pay attention to those spaces. "
                f"They were often where the things that mattered most lived."
            ),
            (
                f"The question of {theme} had been with {p} for a long time — "
                f"not always in the foreground, but never entirely absent either. "
                f"Now, after what had just passed between them and {o}, "
                f"it moved back into the centre with the insistence of something "
                f"that has been patient enough. {p} sat with it. "
                f"Tried to look at it without the protective distortions that usually "
                f"intervene when things become difficult. "
                f"The honest view was harder. But it was, they were finding, "
                f"more navigable than the comfortable version had ever been."
            ),
        ]
        internal = self._pick(internals)

        # ------------------------------------------------------------------
        # Action paragraph — plot-advancing event
        # ------------------------------------------------------------------
        actions = [
            (
                f"What happened next was not what {p} had planned, "
                f"which was something they had almost come to expect. "
                f"The {world.central_conflict_element} — which had been the engine "
                f"of everything since the beginning — made its presence felt again "
                f"in {setting}, with a directness that left little room "
                f"for the usual kinds of evasion. "
                f"{p} found themselves in precisely the situation their preparation "
                f"had been aimed at, and discovered — as one always discovers "
                f"in such moments — that preparation and reality are related "
                f"but not identical. They made the necessary adjustments. Kept moving."
            ),
            (
                f"The {adj} force of what was unfolding in {setting} demanded a response, "
                f"and {p} gave one — not perfectly, not without cost, "
                f"but with the determination of someone who has decided that imperfect action "
                f"is preferable to perfect inaction. "
                f"The {world.central_conflict_element} pushed back "
                f"in the way that real obstacles always do, "
                f"with the particular resistance of something that does not want to be resolved. "
                f"{p} noted this, adjusted their approach, and continued. "
                f"Stubbornness, they had found over time, has its uses."
            ),
            (
                f"There was a moment in {setting} when {p} understood that "
                f"what they had been treating as a problem to be solved "
                f"was in fact a problem to be survived — "
                f"and that survival required not cleverness but endurance. "
                f"The {adj} nature of the situation had not changed. "
                f"But {p}'s relationship to it had, and that, it turned out, "
                f"made a genuine difference in what was possible. "
                f"They did what needed doing. Not elegantly. Not without cost. "
                f"But it was done."
            ),
        ]
        action = self._pick(actions)

        # ------------------------------------------------------------------
        # World description paragraph
        # ------------------------------------------------------------------
        world_descs = [
            (
                f"{Place} held, as it always did, more than its surface suggested. "
                f"{atmosphere.capitalize()}. {p} noticed things they had passed before "
                f"without truly seeing — the specific quality of light at this hour, "
                f"the way the space carried sound differently depending on what occupied it, "
                f"the small details that accumulate into the lived texture of a place. "
                f"Later, they would think of this as the moment {setting} became real to them "
                f"in a different way: not merely a backdrop, but a participant — "
                f"something with its own relationship to what was happening within it."
            ),
            (
                f"The world in which all of this was occurring was not, {p} reflected, "
                f"an uncomplicated one. The {adj} realities of this place — "
                f"the way {world.world_rules[0].lower()}, "
                f"the specific demands it made of the people who lived in it — "
                f"were not separate from the story unfolding in {setting}. "
                f"They were woven into it. The story could not be understood without them. "
                f"{p} understood this now in a way they had not at the beginning. "
                f"It was, they thought, one of the things that had genuinely changed."
            ),
            (
                f"Outside the immediate demands of what was happening, "
                f"the world continued its ordinary business. "
                f"The {adj} reality of {setting} was larger than any one person's story in it, "
                f"and {p} was aware of this — aware of the other lives being lived, "
                f"the other problems being navigated with equal urgency, "
                f"the other people dealing with their own versions of the same "
                f"{theme} that was at the heart of {p}'s situation. "
                f"It was both humbling and, strangely, encouraging. "
                f"If others had found a way through things this difficult, "
                f"then at least the possibility existed."
            ),
        ]
        world_desc = self._pick(world_descs)

        # ------------------------------------------------------------------
        # Second dialogue / encounter
        # ------------------------------------------------------------------
        second_dialogues = [
            (
                f"Later, {p} and {o} found each other again — or, more precisely, "
                f"stopped not finding each other, which is a different thing. "
                f"In {setting}, with {atmosphere}, "
                f"the conversation they had been having in fragments "
                f"came together into something more coherent and harder to walk away from.\n\n"
                f'    {o} looked at them directly. "What happens now?" they asked.\n\n'
                f"    It was the question. Not what to do — {p} could enumerate options. "
                f"But what this becomes, what it costs, "
                f"what it leaves behind when it is finally over.\n\n"
                f'    "I don\'t entirely know," {p} said. '
                f"It was the most honest answer available. "
                f'"But I know what comes next. That will have to be enough for now."\n\n'
                f"    {o} considered this. Nodded once, in the way of someone who disagrees "
                f"but recognises the disagreement is not, at this particular moment, useful. "
                f'"Then let\'s do that," they said.'
            ),
            (
                f"The second conversation was shorter than the first, "
                f"which was not the same as being less significant. "
                f"In {setting}, with the day moving toward its close, "
                f"{p} and {o} arrived at something that was not exactly an agreement "
                f"but was at minimum a shared understanding: "
                f"that what they were each doing was connected, "
                f"that neither could succeed without some version of the other succeeding too, "
                f"and that this meant making accommodations they might not otherwise have chosen.\n\n"
                f"    It was not a comfortable conclusion. "
                f"But {p} had stopped expecting comfort some time ago, "
                f"and had found — somewhat to their own surprise — "
                f"that it was not the thing they most needed. "
                f"What they needed was clarity. "
                f"And some of that, at least, was now available."
            ),
        ]
        second_dialogue = self._pick(second_dialogues)

        # ------------------------------------------------------------------
        # Sensory / grounding paragraph
        # ------------------------------------------------------------------
        sensories = [
            (
                f"The {adj} quality of {setting} had shifted over the course of the day. "
                f"{atmosphere.capitalize()}. What had felt like one kind of place "
                f"in the morning felt like another kind of place now — "
                f"not different in form, but differently inhabited, differently weighted. "
                f"{p} had noticed this before: the way places carry something of the events "
                f"that have moved through them, the way they retain a residue of significance. "
                f"This place would hold today in it for a while. "
                f"{p} walked through it with that awareness, "
                f"and tried to decide what they thought about that."
            ),
            (
                f"It was the kind of {adj} moment that fixes itself in memory without asking permission — "
                f"the specific quality of {atmosphere}, "
                f"the exact arrangement of people and objects in {setting}, "
                f"the precise weight of what had just happened "
                f"and what had not yet been resolved. "
                f"{p} would be able to recall it for years afterward: "
                f"the way the light fell at that hour, the sound the place made at that time, "
                f"the feeling of standing exactly there, in exactly that moment, "
                f"carrying exactly the things they were carrying. "
                f"It was, they knew even in the midst of it, a significant moment. "
                f"The full significance was not yet clear. But its presence was unmistakable."
            ),
        ]
        sensory = self._pick(sensories)

        # ------------------------------------------------------------------
        # Consequence paragraph — response to the chapter's action
        # ------------------------------------------------------------------
        consequences = [
            (
                f"The consequences of what had happened in {setting} would not be "
                f"immediately visible — they rarely were. But {p} could feel them beginning, "
                f"the way you feel a change in weather before the weather itself arrives: "
                f"a shift in pressure, a quality of attention from the world around them, "
                f"a sense of doors opening that had been closed and closing "
                f"that had been open. The {adj} shape of what came next "
                f"was not yet clear. But it was, at last, beginning to form."
            ),
            (
                f"{p} understood, standing in {setting} with the day's events still settling, "
                f"that what had just happened would matter — not immediately, "
                f"not in ways that were easy to measure, but in the kind of ways "
                f"that make themselves felt over time, in decisions made and not made, "
                f"in the texture of subsequent conversations, "
                f"in the slightly different way {o} would look at them from now on. "
                f"The {adj} weight of it was something to carry. "
                f"They found, to their own mild surprise, that they were willing to."
            ),
        ]
        consequence = self._pick(consequences)

        # ------------------------------------------------------------------
        # Chapter closing paragraph
        # ------------------------------------------------------------------
        closings = [
            (
                f"As {p} left {setting}, they carried something new with them — "
                f"not a resolution, which would have been too much to ask for, "
                f"but a direction. The {adj} question of {theme} "
                f"had not been answered. But it had been refined, "
                f"which is the precondition for being answered. "
                f"{p} had learned — from experience, from failure, "
                f"from people who had been honest when honesty was not easy — "
                f"that this was how progress worked: not in revelations but in increments. "
                f"They took the next increment. They kept going."
            ),
            (
                f"The day was not over. There was still the matter of what came next — "
                f"the things that {world.central_conflict_element} demanded, "
                f"the things that {o}'s words had made necessary, "
                f"the things that {p}'s own changed understanding now required. "
                f"But standing in {setting} in the {adj} quality of the later hours, "
                f"with {atmosphere}, {p} felt — not confidence, which would have been premature — "
                f"but a kind of steadiness. Something to stand on. Something to move from. "
                f"It would have to be enough. And perhaps, all things considered, it was."
            ),
            (
                f"Some questions do not resolve; they transform. "
                f"{p} understood this better now than before. "
                f"The question of {theme}, which had been driving everything, "
                f"had not been answered today — but it had changed shape, "
                f"had become something they could work with "
                f"rather than something they were simply trying to survive. "
                f"{atmosphere.capitalize()}. "
                f"{p} sat with that for a while. Then they got up, and did what came next."
            ),
        ]
        closing = self._pick(closings)

        # ------------------------------------------------------------------
        # Assemble all paragraphs into the chapter
        # ------------------------------------------------------------------
        heading = f"Chapter {outline['number']}: {outline['title']}\n" + ("─" * 50)

        # ── Additional scene paragraphs for 3 500+ word chapters ───────
        # Each pool below is ~150-250 words per paragraph.

        # Backstory flash – a relevant memory
        backstory_flashes = [
            (
                f"The memory arrived without warning, as they sometimes do. "
                f"A moment from before — from the time when {p} had been someone slightly "
                f"different, someone who had not yet made the choices that led to {setting}. "
                f"In the memory, {p} could see clearly what they had not understood then: "
                f"the pattern that had been forming, the way one small decision accumulates "
                f"into a character that eventually becomes inescapable. "
                f"They let the memory run its course. Then they put it away in the place "
                f"where things that have taught their lesson are stored, and returned "
                f"their attention to what the present required."
            ),
            (
                f"There had been a version of this before — an earlier iteration of the same "
                f"essential situation, with different people in different places, "
                f"but the same underlying geometry. {p} had been younger then, "
                f"and had handled it in the way that younger people handle things: "
                f"with more certainty and less wisdom than the situation deserved. "
                f"The outcome had been — not a disaster exactly, but a lesson. "
                f"The kind of lesson that comes back to you in moments like this one, "
                f"not as accusation but as preparation. {p} drew on it now. "
                f"It was, they found, still useful."
            ),
            (
                f"Someone had told {p} once — a long time ago, in circumstances that seemed "
                f"unrelated but now seemed anything but — that the things that shape you most "
                f"are not the ones you choose. The ones you choose, you can prepare for. "
                f"It is the ones that arrive without announcement that do the real work. "
                f"Standing in {setting}, {p} thought they understood that differently now "
                f"than they had when they first heard it. The understanding had taken years "
                f"and cost rather more than they would have liked."
            ),
        ]
        backstory_flash = self._pick(backstory_flashes)

        # Setting movement – the character moves through/observes the space
        setting_movements = [
            (
                f"{p} moved through {setting} with the particular attention of someone "
                f"who has learned that details matter — that the world is legible "
                f"to those who learn to read it. Every space tells a story; "
                f"this one told several simultaneously, in the way that layered places do. "
                f"{atmosphere.capitalize()}. The physical facts of it — the way the light "
                f"fell, the way sound behaved, the quality of the surfaces underfoot — "
                f"were noted and filed, not because they seemed immediately relevant, "
                f"but because {p} had found, over time, that relevance declares itself "
                f"most clearly when you least expect it."
            ),
            (
                f"The geography of {setting} had acquired a familiarity that was not quite "
                f"comfort — more the specific knowledge of a place that has been moved through "
                f"under pressure. {p} knew which corners offered sight-lines, "
                f"which areas amplified sound, where the light was most and least reliable. "
                f"This was the kind of knowledge that accumulates without intention, "
                f"the residue of having paid attention during moments when attention mattered. "
                f"{atmosphere.capitalize()}. They used it now, moving with the practiced "
                f"efficiency of someone who has learned to read a space for what it offers."
            ),
            (
                f"There was a moment, crossing through {setting}, when {p} stopped. "
                f"Not because anything had happened — nothing had happened yet — "
                f"but because of a quality in the {adj} stillness that preceded happening. "
                f"The kind of stillness that is not the absence of activity "
                f"but its suspension, held like a breath before release. "
                f"{atmosphere.capitalize()}. {p} stood in it and took it in and waited "
                f"for whatever was going to resolve that quality of suspension. "
                f"It came, as it always came, from an unexpected direction."
            ),
        ]
        setting_movement = self._pick(setting_movements)

        # Character thought – extended internal monologue
        char_thoughts = [
            (
                f"The thing about {theme} — {p} had been thinking about this for longer "
                f"than they would admit to anyone — is that it presents itself as a single "
                f"question and turns out, when you look at it honestly, to be several. "
                f"Each version of the question has its own answer, and those answers "
                f"are not always consistent with each other. "
                f"Most people, when they encounter this, choose one answer and stop looking. "
                f"{p} had never been able to do that. It was not, they had decided, "
                f"a virtue exactly — more a form of stubbornness that happened to resemble one. "
                f"They kept looking. They had not found a single answer that held. "
                f"They had found several that were each partially true, which was harder "
                f"to live with but more accurate."
            ),
            (
                f"What {p} was learning — slowly, at the necessary cost that slow learning "
                f"extracts — was that the version of events they had been telling themselves "
                f"was not wrong exactly, but was incomplete in ways that mattered. "
                f"The missing parts were not absent because they were unknowable. "
                f"They were absent because knowing them required admitting things "
                f"that were uncomfortable to admit. The relevant question was not "
                f"what was true, but whether {p} was willing to look at what was true "
                f"without the protective softening of a preferred narrative. "
                f"They were trying. The trying was harder than it should have been. "
                f"It was also, they were finding, worth it."
            ),
            (
                f"The question of who you become in circumstances like these — "
                f"whether the person who emerges at the other end is someone you would "
                f"recognise as yourself — was not one {p} had expected to be asking. "
                f"It had arrived the way the most important questions arrive: sideways, "
                f"in the middle of doing something else, with the particular quality of "
                f"something that has been waiting for the right moment to be heard. "
                f"{p} sat with it now, in {setting}, with {atmosphere} around them, "
                f"and tried to answer it honestly. "
                f"The honest answer was: I do not know yet. "
                f"Which was, they thought, the only honest answer available at this stage. "
                f"The rest would have to wait for what came next."
            ),
        ]
        char_thought = self._pick(char_thoughts)

        # Plot development – a piece of information or event advances the story
        plot_developments = [
            (
                f"The information arrived in the form of something small — "
                f"a detail {p} had noticed but not attended to properly until now. "
                f"Seen in the light of everything else, it changed the shape of things. "
                f"Not dramatically — nothing as convenient as a revelation — "
                f"but in the way that adding one correct piece to a partial picture "
                f"sometimes reorganises what you thought you were looking at. "
                f"{p} turned the new understanding over, tested it against what they knew, "
                f"and found that it held. The implications were not comfortable. "
                f"They noted this, filed it alongside the other uncomfortable implications "
                f"they had been accumulating, and continued."
            ),
            (
                f"Something that had been operating in the background — "
                f"the slow machinery of {world.central_conflict_element}, "
                f"which had seemed almost static from {p}'s current position — "
                f"made itself felt in {setting} in a way that was impossible to miss. "
                f"The situation had moved. Not in the direction anyone had expected, "
                f"which was, {p} reflected, exactly in keeping with how the situation "
                f"had been behaving from the start. "
                f"They adjusted their understanding, adjusted their position accordingly, "
                f"and looked at the new configuration with the detached clarity "
                f"that comes from having been surprised enough times to stop expecting otherwise."
            ),
            (
                f"It was {o} who first put it into words — or rather, who said something "
                f"adjacent to it that allowed {p} to find the words themselves. "
                f"That was how the most important things often came: not stated, "
                f"but made available. The thing that had been right at the edge of "
                f"articulation for days now resolved itself into a clear sentence in {p}'s mind, "
                f"and the sentence changed what was possible. "
                f"Not everything. Not most things. "
                f"But the specific thing it needed to change, in exactly the way it needed to. "
                f"Sometimes that is enough."
            ),
        ]
        plot_development = self._pick(plot_developments)

        # Minor obstacle – something small that costs time or comfort
        minor_obstacles = [
            (
                f"Not everything in {setting} cooperated. There was a complication — "
                f"small in the scale of what they were dealing with, "
                f"but present with the particular insistence of minor obstacles, "
                f"which is disproportionate to their size. "
                f"{p} dealt with it with the resigned efficiency of someone who has learned "
                f"that refusing to engage with small problems does not make them go away. "
                f"It cost time. It cost a proportion of their {adj} concentration "
                f"that they would have preferred to spend elsewhere. "
                f"Eventually it resolved. They returned to what mattered."
            ),
            (
                f"The complication was, objectively, minor. {p} was aware of this. "
                f"They were also aware that the awareness did not make it less of a complication. "
                f"Minor obstacles in the context of larger pressure do not behave as minor obstacles — "
                f"they absorb attention that the larger situation urgently requires. "
                f"{p} handled it. Not elegantly, and not with the patience they might have wished "
                f"to demonstrate, but it was handled. They moved on with the particular "
                f"determination of someone who has not been stopped but has been slowed, "
                f"and who has noted the difference."
            ),
        ]
        minor_obstacle = self._pick(minor_obstacles)

        # Resolution step – forward movement toward the goal
        resolution_steps = [
            (
                f"The movement forward was not dramatic. It rarely was — "
                f"real progress, {p} had learned, tends to be quiet and cumulative, "
                f"not punctuated by recognisable moments of achievement. "
                f"But the ground covered in {setting} was real ground, "
                f"and the distance between where they had been and where they now were "
                f"was, measured accurately, meaningful. "
                f"They would not celebrate it. But they noted it, "
                f"the way you note progress that is too uncertain to celebrate "
                f"but too real to dismiss, and they let it serve as fuel."
            ),
            (
                f"There was a moment in {setting} when the path forward — "
                f"which had been obscured by everything else — became, briefly, clear. "
                f"Not mapped. Not guaranteed. But clear in the sense of: "
                f"visible, navigable, present. {p} recognised this for what it was "
                f"and moved before the clarity had a chance to close. "
                f"That was the thing about moments of clarity: "
                f"they do not wait for you to finish being uncertain about them. "
                f"You take them as they arrive, or you miss them. "
                f"{p} had missed enough of them to know better now."
            ),
        ]
        resolution_step = self._pick(resolution_steps)

        # Tension paragraph – stakes raised for what comes next
        tension_paras = [
            (
                f"The {adj} pressure of what remained — what was still unresolved, "
                f"still pending, still capable of turning in either direction — "
                f"was not something {p} could set down in {setting} and walk away from. "
                f"It was the kind of pressure that does not release when you are not actively "
                f"engaged with it, but simply waits, with the patient persistence "
                f"of things that are not on a deadline. "
                f"{p} felt it. They had felt it for some time. They had learned to work with it "
                f"rather than against it — to carry it as a reminder rather than a burden, "
                f"though the distinction was not always easy to maintain."
            ),
            (
                f"Everything that had happened today had tightened the situation. "
                f"{p} was aware of this as a physical thing — the way a rope under tension "
                f"feels different from a rope at rest, the way the {adj} quality of the air "
                f"in {setting} carried the specific density of things that are approaching resolution. "
                f"Whatever came next, it would come with an urgency that did not leave "
                f"much room for the comfortable indecision of earlier in the story. "
                f"{p} looked at what they had and what they still needed, "
                f"and made what calculations were possible."
            ),
        ]
        tension_para = self._pick(tension_paras)

        # Sensory immersion – deep physical grounding
        sensory_immersions = [
            (
                f"Later, what {p} would remember most about {setting} on this day "
                f"was not the significant things — not the conversation, not the event, "
                f"not the decision — but the physical specifics: "
                f"the way {atmosphere} registered on the skin, "
                f"the particular quality of the sounds at that hour, "
                f"the weight of the air. "
                f"The mind, under pressure, fixes on the irrelevant. "
                f"Or what seems irrelevant. {p} had come to believe that nothing "
                f"the mind under pressure fixes on is truly irrelevant — "
                f"that the body knows things the mind has not yet articulated, "
                f"and communicates them in the only language available to it: sensation."
            ),
            (
                f"The {adj} quality of {setting} had the specific texture of places "
                f"where important things happen — not distinguished, not theatrical, "
                f"but somehow more present than ordinary places. "
                f"Every sensory detail was slightly heightened: "
                f"the way {atmosphere} made the familiar unfamiliar, "
                f"the specific sound of movement in this particular space, "
                f"the way time seemed to have a different density here than elsewhere. "
                f"{p} moved through it with the attention of someone "
                f"who understands that the physical world is not merely background "
                f"but participant — that a story happens in a place, and the place "
                f"is changed by the story as the story is shaped by the place."
            ),
        ]
        sensory_immersion = self._pick(sensory_immersions)

        parts = [
            heading,
            opening,
            approach,
            backstory_flash,
            dialogue,
            internal,
            setting_movement,
            action,
            char_thought,
            world_desc,
            plot_development,
            second_dialogue,
            minor_obstacle,
            sensory,
            resolution_step,
            tension_para,
            consequence,
            sensory_immersion,
            closing,
        ]
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Chapter padding — extend to target word count
    # ------------------------------------------------------------------

    def _pad_chapter(
        self,
        text: str,
        outline: Dict[str, str],
        characters: List[Character],
        world: World,
        plot: Dict[str, str],
        target_words: int = 3500,
    ) -> str:
        """
        Appends additional prose paragraphs to *text* until it reaches
        *target_words*.  Draws from a large pool of paragraph templates to
        minimise repetition.
        """
        protagonist = next(c for c in characters if c.role == "protagonist")
        antagonist = next(c for c in characters if c.role == "antagonist")
        others = [c for c in characters if c.role != "protagonist"]

        p = protagonist.name.split()[0]
        o = self._pick(others).name.split()[0]
        setting = outline["location"]
        atmosphere = self._pick(self._gd["atmosphere"])
        adj = self._pick(self._gd["power_words"])
        theme = self._pick(world.themes)
        place = setting
        Place = setting[0].upper() + setting[1:]

        # Large pool of extension paragraphs (~150-200 words each)
        pool = [
            (
                f"The quality of waiting — which {p} had been doing, in one form or "
                f"another, for longer than they could easily account for — "
                f"was something they had learned to use rather than merely endure. "
                f"Waiting, properly attended to, is information. "
                f"The texture of a silence tells you what kind of silence it is. "
                f"The weight of a moment tells you what it is pregnant with. "
                f"{p} paid attention to these things now in {setting}, "
                f"reading the available information with the care of someone who has "
                f"learned that the world communicates constantly and that most people "
                f"are simply not listening at the required frequency. "
                f"What they read in the present quality of {place} was not comfortable. "
                f"But it was, at least, clear."
            ),
            (
                f"The light in {setting} was changing. "
                f"{atmosphere.capitalize()} at this hour gave everything "
                f"a different quality than it had carried in the earlier part of the day — "
                f"more {adj}, more weighted, more aware of its own significance. "
                f"{p} had always paid attention to light, to the way it shifted "
                f"the emotional register of a place without changing its physical facts. "
                f"The same room, the same faces, the same situation — "
                f"but the light different, and so the experience different. "
                f"Right now the light was saying something specific about this moment, "
                f"and {p} was trying to translate it accurately. "
                f"The translation, they suspected, would not be welcome. "
                f"But welcome or not, it was the truth the light was offering, "
                f"and they had never found anything useful in refusing to hear the truth."
            ),
            (
                f"The thing about {o} — and {p} had been thinking about this "
                f"in the unguarded moments that arrive between decisions — "
                f"was that they were not, as {p} had initially assumed, "
                f"simply a problem to be solved. They were a mirror. "
                f"Not a flattering one, but an honest one. "
                f"The qualities in {o} that {p} found most difficult "
                f"were the qualities that {p} was at some risk of developing "
                f"themselves, under sufficient pressure. "
                f"This was the uncomfortable lesson that antagonists teach: "
                f"not that they are entirely different from the protagonist, "
                f"but that they are what the protagonist might become "
                f"if certain choices were made differently at certain junctures. "
                f"{p} filed this awareness in the place where useful discomforts live "
                f"and returned their attention to what the present required."
            ),
            (
                f"The world that surrounded {setting} — the larger world, "
                f"the world that had produced the characters in this story "
                f"and the conflict that drove them — "
                f"was not separate from what was happening here. "
                f"It was present in the way that the context of all things is present: "
                f"invisibly, structurally, as the thing that makes everything else possible "
                f"and that shapes every choice without being acknowledged as doing so. "
                f"{p} understood this better now than at the beginning. "
                f"The beginning had the simplicity of not yet knowing "
                f"how complicated things were. "
                f"Now they knew. The complication was not reassuring, "
                f"but it was at least honest, and honesty — "
                f"even the difficult kind — was something {p} could work with."
            ),
            (
                f"There are moments in the middle of difficult situations "
                f"when the difficulty reveals something that easier circumstances "
                f"would have kept concealed. {p} was having one of those moments now. "
                f"The specific pressure of what was happening in {setting} — "
                f"the {adj} weight of the decision that had to be made, "
                f"the knowledge of what was at stake on either side — "
                f"was doing the thing that pressure sometimes does: "
                f"burning away the unnecessary and leaving what was actually true. "
                f"What remained, when the burning was finished, "
                f"was not a comfortable thing. But it was a real thing. "
                f"And real things, {p} had found, are easier to act on "
                f"than comfortable fictions. Even when the action they demand is hard."
            ),
            (
                f"The silence between {p} and the demands of the moment "
                f"was not empty. It was full of the things neither was saying — "
                f"the implications not yet drawn, the conclusions not yet reached, "
                f"the costs not yet counted. {p} moved through {setting} "
                f"with this fullness around them, aware of it the way you are aware "
                f"of something important that you are not yet ready to address directly. "
                f"Sometimes the right approach to a thing is to circle it. "
                f"To let it become familiar before engaging it fully. "
                f"To learn its shape before testing it. "
                f"{p} was circling now. The direct engagement would come. "
                f"But not until they had a better sense of what they were approaching."
            ),
            (
                f"The work that had brought {p} to this point — "
                f"the specific, {adj} labour of getting from there to here — "
                f"had not been without cost. Something had been given up along the way. "
                f"Several things, in fact. The accounting of what had been spent "
                f"and what remained was not a comfortable exercise, "
                f"but it was a necessary one. {p} did it honestly, "
                f"as they tried to do all difficult things: without the softening "
                f"of self-deception, without the comfort of preferred narratives, "
                f"with only the clarity of seeing what was actually there. "
                f"The balance was not what they would have designed in advance. "
                f"But it was the balance that the story had produced, "
                f"and working with what the story produced was the only viable option."
            ),
            (
                f"In {setting}, the particular truth of {theme} "
                f"was more present than elsewhere — "
                f"not because {setting} was special, but because "
                f"circumstances had made it the location where "
                f"this particular truth had chosen to surface. "
                f"Places acquire meaning from the things that happen in them. "
                f"{p} would not be able to return here without carrying "
                f"the weight of this day. That was the transaction "
                f"that significant events always make: "
                f"they claim the places where they occur, "
                f"making them simultaneous historical sites and continuing spaces. "
                f"{p} stood in both versions of {place} at once — "
                f"the physical one, and the one that was already memory."
            ),
            (
                f"The conversation that {p} had been preparing for — "
                f"had been moving toward since the beginning of everything that had led here — "
                f"had still not arrived. But its approach was unmistakable. "
                f"The way certain weather makes itself felt before it becomes visible: "
                f"a shift in pressure, a quality of attention in the environment, "
                f"a particular {adj} tension in the air of {setting}. "
                f"{p} prepared for it the way they prepared for most things "
                f"they could not avoid: by doing what they could do now "
                f"to be in the best possible position when it arrived, "
                f"and by accepting that some part of the outcome "
                f"was not within their ability to control. "
                f"That acceptance had not come easily. "
                f"But it had, with practice, come."
            ),
            (
                f"Something that had been operating below the level "
                f"of {p}'s conscious attention moved up into awareness now "
                f"in {setting}: a pattern, half-formed, but recognisable. "
                f"The events that had seemed separate — "
                f"the encounters that had seemed coincidental, "
                f"the information that had seemed disconnected — "
                f"were, when placed in the right order, a coherent sequence. "
                f"They had been reading individual words "
                f"when they should have been reading sentences. "
                f"{p} stood in {setting} and put the sentences together "
                f"and read what they said, and what they said changed "
                f"the {adj} geography of the situation they were navigating. "
                f"Not completely. But in the specific way that "
                f"matters when you are trying to find a path through."
            ),
            (
                f"Later, when {p} tried to reconstruct exactly "
                f"what had shifted in {setting} and when, "
                f"they would not be able to identify a single moment. "
                f"That was the nature of real change: "
                f"it does not arrive in a recognisable instant "
                f"but accumulates in increments that are each too small to notice, "
                f"until suddenly the sum is visible and unmistakeable. "
                f"The {adj} weight of what they now understood "
                f"had been building for some time, in the way that understanding builds: "
                f"quietly, beneath the surface of conscious thought, "
                f"from the raw material of experience and observation "
                f"and the slow work of the mind that continues "
                f"even when you are not directing it."
            ),
            (
                f"The central question — which {p} had been carrying "
                f"since before {setting} had entered the picture — "
                f"was not going to answer itself. "
                f"This was something {p} had known for some time "
                f"but had not yet fully accepted: that the answer "
                f"was not waiting to be discovered but waiting to be made. "
                f"That was different. Discovering implies that the answer exists "
                f"independently, fully formed, and requires only finding. "
                f"Making implies participation, commitment, consequence. "
                f"The thing {p} was moving toward was not already there. "
                f"They were going to have to build it "
                f"from the materials the situation had provided, "
                f"with the tools they had developed — or failed to develop — "
                f"in the course of getting here."
            ),
            (
                f"The {adj} fact of what had not yet been said between {p} and {o} "
                f"was present in {setting} as a physical weight. "
                f"Conversations deferred do not disappear — "
                f"they accumulate interest. "
                f"Every exchange that avoids the central subject "
                f"adds to the eventual cost of addressing it. "
                f"{p} was aware of this, and aware that {o} was aware of it, "
                f"and aware that the mutual awareness did not make "
                f"the avoidance any easier to end. "
                f"Some conversations require the right moment. "
                f"Some require the right conditions. "
                f"Some require simply the decision that deferral "
                f"has reached its limit and the conversation "
                f"is going to happen now, conditions or not. "
                f"{p} was approaching that limit."
            ),
            (
                f"The view from this position in {setting} — "
                f"literally and otherwise — "
                f"was different from the view that had been available before. "
                f"Movement changes perspective. That was one of the things "
                f"that movement was for: not just physical translation "
                f"but the repositioning of the point of view "
                f"from which everything else is assessed. "
                f"{p} looked at the situation from where they now stood "
                f"and saw things that had been invisible from the previous position. "
                f"Some of what was now visible was better than expected. "
                f"Some was worse. The {adj} totality of it "
                f"was more complete than what they had been working with before, "
                f"which made it more useful, whatever its emotional content."
            ),
            (
                f"The things that had been holding {p} in place — "
                f"the habits of thought, the inherited assumptions, "
                f"the comfortable certainties that the story had been slowly dismantling — "
                f"were fewer now than at the beginning. "
                f"This was not entirely comfortable. "
                f"Certainty, even wrong certainty, provides a kind of anchor. "
                f"Without it, the movement required was more effortful, "
                f"the navigation more demanding. "
                f"But {p} had discovered that effortful navigation "
                f"was preferable to confident movement in the wrong direction. "
                f"They moved now with more care and more uncertainty "
                f"and were, they found, getting further with both "
                f"than they had ever got with the certainties of before."
            ),
        ]

        extra_paragraphs: List[str] = []
        # Shuffle pool to randomise which paragraphs are used
        shuffled = list(pool)
        self._rng.shuffle(shuffled)
        pool_iter = iter(shuffled)

        while len(text.split()) + sum(len(ep.split()) for ep in extra_paragraphs) < target_words:
            try:
                extra_paragraphs.append(next(pool_iter))
            except StopIteration:
                # Restart pool if exhausted (for very low word counts)
                reshuffled = list(pool)
                self._rng.shuffle(reshuffled)
                pool_iter = iter(reshuffled)

        if extra_paragraphs:
            text = text + "\n\n" + "\n\n".join(extra_paragraphs)
        return text

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def format_character_profiles(self, characters: List[Character]) -> str:
        sections = ["CHARACTER PROFILES", "=" * 50, ""]
        for c in characters:
            sections.append(c.profile_text())
            sections.append("")
        return "\n".join(sections)

    def format_world(self, world: World) -> str:
        return world.world_text()

    def format_plot(self, plot: Dict[str, str]) -> str:
        return "\n\n".join([
            "PLOT ARCHITECTURE",
            "=" * 50,
            "PREMISE:",
            plot["premise"],
            "STORY ARC:",
            plot["arc"],
            "SUBPLOTS:",
            plot["subplots"],
            "THEMES: " + plot["themes"],
        ])

    def format_chapter_outlines(self, outlines: List[Dict[str, str]]) -> str:
        lines = ["CHAPTER-BY-CHAPTER OUTLINE", "=" * 50, ""]
        for o in outlines:
            lines += [
                f"Chapter {o['number']}: {o['title']}",
                f"  Beat type : {o['beat'].replace('_', ' ').title()}",
                f"  Location  : {o['location']}",
                f"  Key character : {o['other_char']}",
                f"  Summary   : {o['summary']}",
                "",
            ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Compilation
    # ------------------------------------------------------------------

    def _compile(
        self,
        characters: List[Character],
        world: World,
        chapters: List[str],
    ) -> str:
        protagonist = next(c for c in characters if c.role == "protagonist")

        dedication = (
            "For everyone who has ever started a story and found,\n"
            "somewhere in the middle, that the story was also about them.\n\n"
            f"And for {protagonist.name}, who did not choose this — "
            f"but chose how to face it."
        )

        toc_lines = ["TABLE OF CONTENTS", "─" * 40]
        for ch in chapters:
            first_line = ch.strip().split("\n")[0].replace("─" * 50, "").strip()
            toc_lines.append(f"  {first_line}")
        toc_lines.append("  Epilogue")
        toc = "\n".join(toc_lines)

        epilogue = (
            "EPILOGUE\n"
            + "─" * 40 + "\n\n"
            f"Every story ends in the middle of other stories. "
            f"What happened to {protagonist.name} did not resolve neatly into silence — "
            f"it folded into the larger continuity of a life, became part of "
            f"the texture of who they were and how they moved through the world. "
            f"The questions of {world.themes[0]} and "
            f"{world.themes[1] if len(world.themes) > 1 else 'what it costs'} "
            f"did not disappear. They changed form. They became liveable.\n\n"
            f"That is, perhaps, the most honest thing a story can offer: "
            f"not resolution, but the demonstration that the questions can be carried — "
            f"that carrying them, in fact, is what a life is.\n\n"
            f"— End —"
        )

        parts = (
            [
                "=" * 60,
                "FICTION NOVEL",
                "Generated by Fiction Novel Generator",
                "=" * 60,
                "",
                "DEDICATION",
                "─" * 40,
                "",
                dedication,
                "",
                "=" * 60,
                "",
                toc,
                "",
                "=" * 60,
                "",
            ]
            + chapters
            + [
                "",
                "=" * 60,
                epilogue,
                "",
                "=" * 60,
            ]
        )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate_all(
        self,
        status_callback: Optional[Callable[[str], None]] = None,
        chapter_writer: Optional[Callable] = None,
    ) -> Dict[str, str]:
        """
        Run all local generation phases and return a dict of all artefacts.

        Args:
            status_callback: Called with status strings during generation.
            chapter_writer:  Optional callable(chapter_index, outline,
                             characters, world, plot) -> str.
                             If provided, called instead of write_chapter()
                             for each chapter (used by Ollama integration).

        Keys: novel, world, characters, plot_outline, chapter_outlines
        (The caller is responsible for adding "research" to the returned dict.)
        """

        def status(msg: str) -> None:
            if status_callback:
                status_callback(msg)

        status("🌍 Phase 2/7: Building the story world...")
        characters = self.build_characters()
        world = self.build_world(characters)

        status("👥 Phase 3/7: Creating characters...")
        char_text = self.format_character_profiles(characters)

        status("📖 Phase 4/7: Architecting the plot...")
        plot = self.build_plot(characters, world)
        plot_text = self.format_plot(plot)

        status("📋 Phase 5/7: Outlining all chapters...")
        outlines = self.build_chapter_outlines(characters, world, plot)
        outline_text = self.format_chapter_outlines(outlines)

        status("✍️  Phase 6/7: Writing chapters...")
        chapter_texts: List[str] = []
        for i, outline in enumerate(outlines):
            if chapter_writer is not None:
                # External writer (e.g. Ollama) handles prose generation
                chapter_texts.append(
                    chapter_writer(i, outline, characters, world, plot)
                )
            else:
                status(f"✍️  Writing chapter {i + 1} of {self.num_chapters}...")
                chapter_text = self.write_chapter(outline, characters, world, plot)
                chapter_text = self._pad_chapter(
                    chapter_text, outline, characters, world, plot
                )
                chapter_texts.append(chapter_text)

        status("📦 Phase 7/7: Compiling the final novel...")
        novel = self._compile(characters, world, chapter_texts)

        return {
            "novel": novel,
            "world": world.world_text(),
            "characters": char_text,
            "plot_outline": plot_text,
            "chapter_outlines": outline_text,
        }
