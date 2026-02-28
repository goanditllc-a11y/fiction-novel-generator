import os

APP_NAME = "Fiction Novel Editor"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Fiction Novel Editor"
APPDATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'FictionNovelEditor')
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
AUTOSAVE_DIR = os.path.join(APPDATA_DIR, 'autosave')
MAX_RECENT_FILES = 10
DEFAULT_AUTOSAVE_INTERVAL = 300  # seconds
DEFAULT_FONT_SIZE = 12
DEFAULT_FONT_FAMILY = "Segoe UI"
SUPPORTED_EXTENSIONS = ['.txt', '.docx', '.md']

# AI Pattern phrases
AI_OVERUSED_PHRASES = [
    "delve into", "it's important to note", "in conclusion", "furthermore",
    "moreover", "it's worth noting", "dive into", "navigate", "landscape",
    "leverage", "in today's world", "crucial", "foster", "underscores",
    "realm", "multifaceted", "holistic", "paradigm", "synergy", "tapestry",
    "beacon", "unwavering", "testament", "groundbreaking", "revolutionary",
    "transformative", "cutting-edge", "state-of-the-art", "robust", "dynamic",
    "innovative", "comprehensive", "streamline", "optimize", "utilize",
    "facilitate", "demonstrate", "implement", "significant", "substantial"
]

HEDGING_PHRASES = [
    "somewhat", "arguably", "it could be said", "perhaps", "in many ways",
    "to some extent", "it seems", "it appears", "one might argue",
    "it could be argued", "in a sense", "relatively", "rather"
]

FORMAL_TRANSITIONS = [
    "in addition", "additionally", "consequently", "therefore", "thus",
    "hence", "nevertheless", "nonetheless", "however", "in contrast",
    "on the other hand", "as a result", "in summary", "to summarize",
    "in conclusion", "to conclude", "finally", "lastly"
]
