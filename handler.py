import ast
import logging
import time
import re
import requests
import shutil
import yaml

from .logger import LOGGING_CONFIG
from pathlib import Path
from shutil import copy
from typing import Dict, List, Union, Any

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from sluch_ai.src.cfg import CFG
from sluch_ai.src.postprocess import Postprocess
from sluch_ai.utils.utils import create_txt_chunks_single

class AbstractHandler(object):
    def __init__(self):
        self.config = CFG()
        self.event = self.initialize_events()
        self.observer = Observer()
        self.logger = self.initialize_logger()

    def __call__(self):
        self.create_destination_path(dstpath=self.config.destination_path)
        self.set_properties()
        self.set_start_observe()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            self.observer.join()

    def create_destination_path(self, dstpath: str):
        """Create provided file destination folder,
        based on self.config.dsc_path argument value.
        """
        dstpath = Path(dstpath)
        if not dstpath.exists():
            Path.mkdir(dstpath)

    def load_config(self):
        """
        Params
        --------
        None

        Return
        --------
        config: Dict
            predefined configuration file.
        """
        with open(self.config_path, "rb") as confile:
            config = yaml.safe_load(confile)
        return config

    def initialize_logger(self):
        """Initialize logger object
        based on predefined watcher.src.logger arch.
        """
        logging.root.setLevel(logging.NOTSET)
        logging.basicConfig(level=logging.NOTSET)
        logging.config.dictConfig(LOGGING_CONFIG)
        log = logging.getLogger(self.config.logger_name)
        log.info(f"Logger initializer for app {self.config.logger_name}")
        return log

    def initialize_events(self):
        """Initialize event properties based on configuration file.

        #TODO: There is no border case in which self.config is empty,
        but at the moment there is no need to call PatternMatchingEventHandler
        with additional or default arguments.
        Return
        --------
            event: PatternMatchingEventHandler object.

        """
        event = PatternMatchingEventHandler(
            patterns=self.config.patterns,
            ignore_patterns=self.config.ignore_patterns,
            ignore_directories=self.config.ignore_directories,
            case_sensitive=self.config.case_sensitive,
        )
        return event

    def set_properties(self):
        """Set event properties

        on_created : Initialize after creation file.
        on_deleted : Initialize after file deletion process.
        on_modified : Initialize after file modification (renamed itp.)
        on_moved: Initialize after file moved.
        """
        self.event.on_created = self.on_created
        self.event.on_deleted = self.on_deleted
        self.event.on_modified = self.on_modified
        self.event.on_moved = self.on_moved

    def set_start_observe(self) -> None:
        """Initialize an observer objects with predefined arguments."""
        self.observer.schedule(
            self.event,
            path=self.config.file_path,
            recursive=self.config.go_recursively
        )
        self.observer.start()

    def get_created(self) -> None:
        """on created property on self.event object."""
        return self.event.on_created

    def get_deleted(self) -> None:
        """on deleted property on self.event object."""
        return self.event.get_deleted

    def get_moved(self) -> None:
        """on moved property on self.event object."""
        return self.event.get_moved

    def get_modified(self) -> None:
        """on modification property on self.event object."""
        return self.event.get_modified

    def get_filename(self, path: Union[str, Path]) -> str:
        """Get name of file from predefined path,
            convert str to pathlib.Path if needed.

        Params
        --------
        path: Union[str, Path]
            Path for splitted file.

        Returns
        --------
        filename: str
            Name of file.
        """
        if isinstance(path, str):
            path = Path(path)
        filename = path.parts[-1]
        return filename

    def on_created(self, event: Any):
        """
        #TODO
        - tests

        Define event.on_created object.
        If new file was created, move it into
        destination path defined in config.get('path')

        Params
        --------
        event:
        Returns
        ---------
        None
        """
        self.logger.info(f"{event.src_path} appear in {self.config.file_path}")
        filename = self.get_filename(path=event.src_path)
        time.sleep(2)
        self.logger.info(event.src_path)
        self.logger.info(self.config.request_url)
        _data = re.sub(r'\\', '/', event.src_path)
        self.logger.info(_data)
        response = requests.post(
            self.config.request_url,
            headers={
                "Content-type": "application/json",
            },
            data='{"filename" : "%s" }' % _data,
        )

        if self.config.postprocess:
            pp = Postprocess(cfg=CFG)
            _rsp = ast.literal_eval(response.text)
            _rsp = pp.postprocess_once(_rsp, event.src_path)
            create_txt_chunks_single(_rsp, filename, self.config.destination_path, 20)
        else:
            return {event.src_path: response.text}

    def on_deleted(self, event):
        """Notification on deletion stage."""
        self.logger.info(f"{event.src_path} has been deleted")

    def on_modified(self, event):
        """Notification on modification stage."""
        self.logger.info(f"{event.src_path} has been modified")

    def on_moved(self, event):
        """Notification on moving stage"""
        self.logger.info(f"File {event.src_path} moved to {event.dest_path}")

    def get_created(self):
        """Return self.event on_created property."""
        return self.event.on_created

    def get_deleted(self):
        """Return self.event on_deleted property."""
        return self.event.get_deleted

    def get_moved(self):
        """Return self.event on_moved property."""
        return self.event.get_moved

    def get_modified(self):
        """Return self.event on modification property."""
        return self.event.get_modified


class FileHandler(AbstractHandler):
    def __init__(self, config_path: str):
        super().__init__(config_path)

    def get_filelimit(self):
        pass
