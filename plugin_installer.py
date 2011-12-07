import time
import os
import re
from gettext import gettext as _

import gtk
import gedit


# Menu item example, insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="PluginInstaller" action="PluginInstaller"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""


class PluginInstallerWindowHelper:
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin

        self._insert_menu()

    def deactivate(self):
        # Remove any installed menu items
        self._remove_menu()

        self._window = None
        self._plugin = None
        self._action_group = None

    def _insert_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Create a new action group
        self._action_group = gtk.ActionGroup("PluginInstallerActions")
        self._action_group.add_actions([("PluginInstaller", None, _("Install plugin..."),
                                         None, _("Install a plugin"),
                                         self.on_install_plugin_activate)])

        # Insert the action group
        manager.insert_action_group(self._action_group, -1)

        # Merge the UI
        self._ui_id = manager.add_ui_from_string(ui_str)

    def _remove_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Remove the ui
        manager.remove_ui(self._ui_id)

        # Remove the action group
        manager.remove_action_group(self._action_group)

        # Make sure the manager updates
        manager.ensure_update()

    def update_ui(self):
        self._action_group.set_sensitive(self._window.get_active_document() != None)

    # Menu activate handlers
    def on_install_plugin_activate(self, action):
        fileChooser = gtk.FileChooserDialog(title="Select a valid tar.gz or tar.bz2 plugin",
            parent=self._window,
            action=gtk.FILE_CHOOSER_CONFIRMATION_CONFIRM,
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                       gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fileChooser.set_default_response(gtk.RESPONSE_OK)

        response = fileChooser.run()
        if response == gtk.RESPONSE_OK:
            selectedDir = os.path.normpath( fileChooser.get_filename() ) #+ "/"
            self.install(selectedDir)
        fileChooser.destroy()

    def install(self, path):
        try:
            directory = "/tmp/gedit-plugin-installer-%s" % time.time()
            os.mkdir(directory)
            if re.search(r'\.t(ar.)?gz$', path):
                os.system('tar -xzf %s -C %s' % (path, directory))
            elif re.search(r'\.tar.bz2$', path):
                os.system('tar -xjf %s -C %s' % (path, directory))
            else:
                gtk.MessageDialog(parent=self._window, message_format="Invalid plugin archive.").show()        
                return
            os.chdir(directory)
            find = 'find -name "*.gedit-plugin" -printf %h'
            os.chdir(os.popen(find).readlines()[0])
            os.system('cp -r . $HOME/.gnome2/gedit/plugins/')
        except:
            gtk.MessageDialog(parent=self._window, message_format="Error.").show()        
        else:
            gtk.MessageDialog(parent=self._window, message_format="Plugin installed. Enable it in Edit > Preferences.").show()       

    def update_ui(self):
        pass


class PluginInstaller(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self._instances = {}

    def activate(self, window):
        self._instances[window] = PluginInstallerWindowHelper(self, window)

    def deactivate(self, window):
        self._instances[window].deactivate()
        del self._instances[window]

    def update_ui(self, window):
        self._instances[window].update_ui()
