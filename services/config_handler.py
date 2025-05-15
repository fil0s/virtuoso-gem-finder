from watchdog.events import FileSystemEventHandler

# Forward declaration for VirtuosoGemFinder type hint if needed, or import later
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from ..solgem import VirtuosoGemFinder # Assuming solgem.py is one level up

class ConfigHandler(FileSystemEventHandler):
    def __init__(self, gem_finder): # gem_finder is of type 'VirtuosoGemFinder'
        self.gem_finder = gem_finder
        
    def on_modified(self, event):
        # To avoid issues with config.json vs config.yaml, let's make this more flexible
        # or rely on the gem_finder instance to know its config file name.
        # For now, sticking to the original logic which implies 'config.json'
        # This should be updated if config file name/type changes.
        if event.src_path.endswith(self.gem_finder.config_file_name): # Assuming gem_finder has a config_file_name attribute
            self.gem_finder.logger.info(f"Config file '{self.gem_finder.config_file_name}' modified, reloading...")
            self.gem_finder.config = self.gem_finder._load_config() # _load_config should handle the actual loading 