import importlib.abc
import logging
import sys
import traceback
import types
from importlib.machinery import ModuleSpec
from typing import Sequence, Optional

import rustimport

logger = logging.getLogger(__name__)


class Finder(importlib.abc.MetaPathFinder):
    def __init__(self):
        self.__running = False

    def find_module(self, fullname: str, path: Optional[Sequence]) -> Optional['Loader']:
        # Prevent re-entry by the underlying importer
        if self.__running:
            return

        try:
            self.__running = True
            return Loader(rustimport.imp(fullname, opt_in=True))
        except ImportError:
            # ImportError should be quashed because that simply means rustimport
            # didn't find anything, and probably shouldn't have found anything!
            logger.debug(traceback.format_exc())
        finally:
            self.__running = False

    def find_spec(
        self, fullname: str, path: Optional[Sequence], target: Optional[types.ModuleType] = ...
    ) -> Optional[ModuleSpec]:
        # Prevent re-entry by the underlying importer
        if self.__running:
            return

        try:
            self.__running = True

            return ModuleSpec(
                name=fullname,
                loader=Loader(rustimport.imp(fullname, opt_in=True)),
            )
        except ImportError:
            # ImportError should be quashed because that simply means rustimport
            # didn't find anything, and probably shouldn't have found anything!
            logger.debug(f"Error while trying to import {fullname}: {traceback.format_exc()}")
            return None
        finally:
            self.__running = False


class Loader(importlib.abc.Loader):
    def __init__(self, module: types.ModuleType):
        self.__module = module

    def load_module(self, fullname: str) -> types.ModuleType:
        return self.__module


# Add the hook to the list of import handlers for Python.
hook_obj = Finder()
sys.meta_path.insert(0, hook_obj)
