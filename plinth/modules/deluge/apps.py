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

"""
Plinth module to configure a Deluge web client.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.apps import App as PlinthApp
from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module


class App(PlinthApp):
    """
    Example usage of an App (without much customization)
    """
    version = 1

    depends = ['apps']

    service = None

    managed_services = ['deluge-web']

    managed_packages = ['deluged', 'deluge-web']

    title = _('BitTorrent Web Client \n (Deluge)')

    description = [
        _('Deluge is a BitTorrent client that features a Web UI.'),

        _('When enabled, the Deluge web client will be available from '
          '<a href="/deluge">/deluge</a> path on the web server. The '
          'default password is \'deluge\', but you should log in and change '
          'it immediately after enabling this service.')
    ]

    def init(self):
        """Initialize the Deluge module."""
        menu = cfg.main_menu.get('apps:index')
        menu.add_urlname(self.title, 'glyphicon-magnet', 'deluge:index')

        global service
        setup_helper = globals()['setup_helper']
        if setup_helper.get_state() != 'needs-setup':
            service = service_module.Service(
                self.managed_services[0], self.title, ports=['http', 'https'],
                is_external=True, is_enabled=self.is_enabled,
                enable=self.enable, disable=self.disable)

            if self.is_enabled():
                self.add_shortcut()

    def setup(self, helper, old_version=None):
        """Install and configure the module."""
        helper.install(self.managed_packages)
        helper.call('post', actions.superuser_run, 'deluge', ['enable'])
        global service
        if service is None:
            service = service_module.Service(
                self.managed_services[0], self.title, ports=['http', 'https'],
                is_external=True, is_enabled=self.is_enabled,
                enable=self.enable, disable=self.disable)
        helper.call('post', service.notify_enabled, None, True)
        helper.call('post', self.add_shortcut)

    def add_shortcut(self):
        frontpage.add_shortcut('deluge', self.title, url='/deluge',
                               login_required=True)

    def is_enabled(self):
        """Return whether the module is enabled."""
        return (action_utils.webserver_is_enabled('deluge-plinth') and
                action_utils.service_is_enabled('deluge-web'))

    def enable(self):
        """Enable the module."""
        actions.superuser_run('deluge', ['enable'])
        # TODO: move add_shortcut functionality to default enable method
        self.add_shortcut()

    def disable(self):
        """Disable the module."""
        actions.superuser_run('deluge', ['disable'])
        frontpage.remove_shortcut('deluge')

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = []

        results.append(action_utils.diagnose_port_listening(8112, 'tcp4'))
        results.append(action_utils.diagnose_port_listening(8112, 'tcp6'))
        results.extend(action_utils.diagnose_url_on_all(
            'https://{host}/deluge', check_certificate=False))

        return results

class DelugeApp(App):
    pass