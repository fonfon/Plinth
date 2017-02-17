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
from plinth.errors import AppError
from plinth.setup import ModuleSetup

logger = logging.getLogger(__name__)


class App(object):
    """
    Class representing a Plinth app.

    App has to be subclassed in a modules __init__.py file, where
    the default values given here can be customized.

    The app itself is accessible via <app_manager_instance>.app.
    To avoid any conflicts with app-internal names a app does not have a
    direct link to its module app (this can be changed easily if necessary)

    Each App instance gets (or can provide) a 'setup' attribute
    which (if not provided) is an instance of plinth.setup.ModuleSetup. It
    can be used like <app_instance>.setup.get_state()

    """
    # plinth-internal app version.
    # Increase the version number to apply upgrades. This will trigger
    # executing the <app>.setup mechanism.
    version = 1
    # Dependencies on other apps.
    # List of app names, as listed in /etc/plinth/modules-enabled.
    depends = []
    # Is this app essential to run Pinth?
    # Essential apps cannot be uninstalled.
    is_essential = False
    # Short description of the app.
    # This information is displayed in the dashboard and should be about
    # 2-3 brief sentences.
    description = ""
    # debian packages this app depends on.
    # These packages will be installed when a user clicks on the 'Install'
    # button of the app.
    packages = []
    # plinth-internal services that are managed by this app.
    # the names have to be unique within plinth, and should be close or equal
    # to the actual debian service names.
    # TODO: improve this description
    services = []


class Apps(object):
    """
    A registry to store App instances.

    It might also be used to actually load the apps in the future, which
    is not done by module_loader.py.
    """
    def __init__(self):
        self.apps = collections.OrderedDict()

    def initialize_app(self, app_name):
        app = self.apps[app_name]
        module = app.module
        if not hasattr(app, 'setup_helper'):
            app.setup_helper = ModuleSetup(app_name, module)

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

    def instanciate_app(self, app_name, python_package):
        """
        Before loading any package instanciate its App to access
        App.depends
        # TODO: can this be a classmethod like AppConfig.create?
        """
        app_name = getattr(python_package, 'app_name', 'apps.App')
        App = getattr(python_package, app_name, None)
        if App is None:
            msg = 'Module %s has no valid App' % app_name
            logger.debug(msg)
            # TODO: raise error once all modules/apps are migrated
            if cfg.debug and False:
                raise AppError(msg)
            return
        else:
            import ipdb; ipdb.set_trace()

        app = App()
        # store a reference to the python package of the app
        app.python_package = python_package
        self.apps[app_name] = app


apps = Apps()

