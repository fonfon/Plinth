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
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured

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
    # TODO: add missing attributes
    # Reference to the python package of this app
    package = None


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
        package = app.package
        if not hasattr(app, 'setup_helper'):
            app.setup_helper = ModuleSetup(app_name, package)

        try:
            init = package.init
        except AttributeError:
            logger.debug('No init() for app - %s', package.__name__)
            return

        try:
            init()
        except Exception as exception:
            logger.exception('Exception while running init for %s: %s',
                             package, exception)
            if cfg.debug:
                raise

    def instanciate_app(self, app_name, package):
        """
        Before loading any package instanciate its App to access
        App.depends
        # TODO: can this be a classmethod like AppConfig.create?
        """
        rel_app_class_path = getattr(package, 'app_class', 'apps.App')

        # Import the module containing the App class
        module_rel_path, _, app_class_name = rel_app_class_path.rpartition('.')
        module_path = ".".join([package.__package__, module_rel_path])
        try:
            app_class_module = import_module(module_path)
        except ImportError:
            msg = ("Could not import module containing App class: %s. "
                   "Make sure that app_class is a relative path within the "
                   "app, like 'apps.MyApp'.") % module_path
            logger.exception(msg)
            # TODO: deactivate this when all modules are migrated
            if cfg.debug and False:
                raise
            else:
                return

        # Get App class from the imported module
        try:
            app_class = getattr(app_class_module, app_class_name)
        except AttributeError:
            msg = 'Could not find App class of %s using path %s' % \
                  (app_name, rel_app_class_path)
            logger.exception(msg)
            # TODO: raise error once all modules/apps are migrated
            if cfg.debug and False:
                raise AppError(msg)
            else:
                return

        # Check that a correct class is provided, e.g. to verify that no
        # django AppConfig is used. This prevents duck typing but can be
        # removed if it becomes a problem.
        if not issubclass(app_class, App):
            raise ImproperlyConfigured(
                    "%s isn't a subclass of plinth.apps.App" % app_class_name)

        app = app_class()
        # store a reference to the python package of the app
        if app.package is not None:
            msg = "App in %s already has the attribute 'package' set" % \
                    module_path
            raise AppError(msg)
        app.package = package
        self.apps[app_name] = app


apps = Apps()
