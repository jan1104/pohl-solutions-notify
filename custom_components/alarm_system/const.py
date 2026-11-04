"""Local alarm system constants."""
DOMAIN = "alarm_system"
VERSION = "0.5.4"
TYPES = ("INFO", "WARNING", "FIRE", "INTRUSION")
CHANNELS = {"INFO": "Info", "WARNING": "Warnung", "FIRE": "Feueralarm", "INTRUSION": "Einbruchalarm"}
LABELS = {"INFO": "Information", "WARNING": "Warnung", "FIRE": "Feueralarm", "INTRUSION": "Einbruchalarm"}
EVENT = "alarm_system_updated"
