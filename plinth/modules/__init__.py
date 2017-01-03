#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import collections

from plinth import cfg
from plinth.errors import ModuleError
from plinth.setup import ModuleSetup

logger = logging.getLogger(__name__)


class PlinthModuleManager(object):
    """
    Class representing a Plinth module.

    ModuleManager has to be subclassed in a modules __init__.py file, where
    the default values given here can be customized.

    The module itself is accessible via <module_manager_instance>.module.
    To avoid any conflicts with module-internal names a module does not have a
    direct link to its module manager (this can be changed easily if necessary)

    Each ModuleManager instance gets (or can provide) a 'setup' attribute
    which (if not provided) is an instance of plinth.setup.ModuleSetup. It
    can be used like <manager_instance>.setup.get_state()

    """
    version = 0
    depends = []
    is_essential = False
    description = ""
    packages = []
    services = []


class Modules(object):
    """
    A registry to store PlinthModuleManager instances.

    It might also be used to actually load the modules in the future, which
    is not done by module_loader.py.
    """
    def __init__(self):
        self.managers = collections.OrderedDict()

    def initialize_module(self, module_name):
        manager = self.managers[module_name]
        module = manager.module
        if not hasattr(manager, 'setup_helper'):
            manager.setup_helper = ModuleSetup(module_name, module)

        try:
            init = module.init
        except AttributeError:
            logger.debug('No init() for module - %s', module.__name__)
            return

        try:
            init()
        except Exception as exception:
            logger.exception('Exception while running init for %s: %s',
                             module, exception)
            if cfg.debug:
                raise

    def instanciate_manager(self, module_name, module):
        """
        Before loading any module instanciate its ModuleManager to access
        ModuleManager.depends
        # TODO: can this be a classmethod like AppConfig.create?
        """
        manager_name = getattr(module, 'module_manager_name', 'ModuleManager')
        ModuleManager = getattr(module, manager_name, None)
        if ModuleManager is None:
            msg = 'Module %s has no valid ModuleManager' % module_name
            logger.debug(msg)
            # TODO: raise error once all modules are migrated
            if cfg.debug and False:
                raise ModuleError(msg)
            return

        manager = ModuleManager()
        manager.module = module
        self.managers[module_name] = manager


modules = Modules()
