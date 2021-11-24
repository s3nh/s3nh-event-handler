import ast
import logging
import time
import re
import requests


from pathlib import Path
from shutil import copy
from typing import List, Dict, Union, Any

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class AbstractHandler(object):
    def __init__(self):
        self.config = CFG()
        self.event = self.inialize_events()
        self.observer = Observer()
        self.logger = self.inialize_logger()

    def __call__(self):
        self.create_destination_path(dstpath = self.config.destination_path)
        self.set_properties()
        self.set_start_observe()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            self.observer.join()

    def create_destination_path(self, dstpath: str):
        dstpath = Path(dstpath)
        if not dstpath.exists():
            Path.mkdir(dstpath)

    def load_config(self):
        with open(self.config.path, "rb") as confile:
            config = yaml.safe_load(confile)
        return config

    def initialize_logger(self):
        logging.root.setLevel(logging.NOTSET)
        logging.basicConfig(level=logging.NOTSET)
        logging.config.dictConfig(LOGGING_CONFIG)
        log = logging.getLogger(self.config.logger_name)
        log.info(f"Initialize logger")
        return log

    def initialize_events(self):

        event = PatternMatchingEventHandler(
            patterns = self.config.patterns,
            ignore_patterns = self.config.ignore_patterns,
            ignore_directories = self.config.ignore_directories,
            case_sensitive = self.config.case_sensitive
        )
        return event

    def set_properties(self):
        self.event.on_created = self.on_created
        self.event.on_modified = self.on_modified
        self.event.on_deleted = self.on_deleted
        self.event.on_moved = self.on_moved

    def set_start_observe(self) -> None:
        self.observer.schedule(
            self.event, 
            path = self.config.file_path, 
            recursive = self.config.go_recursively
        )
        self.observer.start()

    def get_created(self):
        return self.event.on_created

    def get_deleted(self):
        return self.event.on_deleted
    
    def get_moved(self):
        return self.event.on_moved
    
    def get_modified(self):
        return self.event.on_modified
    
    def get_filename(self, path: Union[str, Path]) -> str:
        if isinstance(paht, str):
            path = Path(path)
        filename = path.parts[-1]
        return filename

    def on_created(self, event: Any):
        raise NotImplementedError