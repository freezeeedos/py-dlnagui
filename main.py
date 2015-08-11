#!/usr/bin/python3
import cairo
from gi.repository import GLib, Gtk, GObject
import os
import subprocess
import netifaces
import threading
import shlex
import subprocess

username = os.environ.get( "USER" )
homedir = os.environ.get("HOME")
confdir = homedir + "/.pydlnagui"
dbdir = confdir + "/database"
sharesfile = confdir + "/shares"
netfile = confdir + "/netinf"
portfile = confdir + "/port"
minidlna_conf_file = confdir + "/minidlna.conf"

class MainWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Minidlna GUI")

        self.set_default_size(600, 400)
        self.set_border_width(1)

        self.Vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True, hexpand=True)
        self.Hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, vexpand=True, hexpand=True)
        self.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True, hexpand=True, border_width=1)
        self.vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True, hexpand=True, border_width=1)
        self.listStore = Gtk.ListStore(str, str)
        self.SharesList = Gtk.TreeView(self.listStore)

        for i, column_title in enumerate(["Share name", "Path"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.SharesList.append_column(column)
        
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.scrollable_treelist.set_hexpand(True)
        self.scrollable_treelist.add(self.SharesList)

        self.share_btn_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, border_width=5)
        self.addShare_btn = Gtk.Button(label="Add Share", image=Gtk.Image(stock=Gtk.STOCK_ADD))
        self.delShare_btn = Gtk.Button(label="Remove Share", image=Gtk.Image(stock=Gtk.STOCK_DELETE))
        self.share_btn_hbox.add(self.addShare_btn)
        self.share_btn_hbox.add(self.delShare_btn)
        self.Netinf_Label = Gtk.Label("Network interface:")
        self.Netinf_Combo = Gtk.ComboBoxText(border_width=2)
        
        for i in netifaces.interfaces():
            self.Netinf_Combo.append_text(i)

        self.Port_Label = Gtk.Label("Port:")
        self.Port_Entry = Gtk.Entry()
        self.save_btn = Gtk.Button(label="Save Settings", border_width=2, image=Gtk.Image(stock=Gtk.STOCK_SAVE))
        self.start_btn = Gtk.Button(label="Start", border_width=2, image=Gtk.Image(stock=Gtk.STOCK_MEDIA_PLAY))
        #self.restart_btn = Gtk.Button(label="Restart", border_width=2, image=Gtk.Image(stock=Gtk.STOCK_REFRESH))
        self.stop_btn = Gtk.Button(label="Stop", border_width=2, image=Gtk.Image(stock=Gtk.STOCK_STOP))
        self.statusbar = Gtk.Statusbar()

        self.vbox1.add(self.scrollable_treelist)
        self.vbox1.add(self.share_btn_hbox)

        self.vbox2.add(self.Netinf_Label)
        self.vbox2.add(self.Netinf_Combo)
        self.vbox2.add(self.Port_Label)
        self.vbox2.add(self.Port_Entry)
        self.vbox2.add(self.save_btn)
        self.vbox2.add(self.start_btn)
        #self.vbox2.add(self.restart_btn)
        self.vbox2.add(self.stop_btn)
        
        self.Hbox.add(self.vbox1)
        self.Hbox.add(self.vbox2)
        self.Vbox.add(self.Hbox)
        self.Vbox.add(self.statusbar)
        self.add(self.Vbox)

        self.addShare_handle = self.addShare_btn.connect("clicked", self.on_addShare_clicked)
        self.delShare_handle = self.delShare_btn.connect("clicked", self.on_delShare_clicked)
        self.save_handle = self.save_btn.connect("clicked", self.on_save_clicked)
        self.start_handle = self.start_btn.connect("clicked", self.thread_minidlna)
        self.stop_handle = self.stop_btn.connect("clicked", self.kill_minidlna)
        self.Netinf_Combo.connect("changed", self.Config_changed)
        self.Port_Entry.connect("changed", self.Config_changed)

        self.populate_fields()
        self.save_btn.set_sensitive(False)

    def Config_changed(self, widget):
        self.save_btn.set_sensitive(True)

    def thread_minidlna(self, widget):
        self.statusbar.push(self.statusbar.get_context_id("text"),"minidlnad started!")
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        thread = threading.Thread(target=self.launch_minidlna())
        thread.daemon = True
        thread.start()

    def launch_minidlna(self):
        cmd_dlna = "minidlnad -f " + minidlna_conf_file
        p = subprocess.call(["gksudo","-S", cmd_dlna])
    
    def kill_minidlna(self, widget):
        self.statusbar.push(self.statusbar.get_context_id("text"),"minidlnad stopped!")
        self.stop_btn.set_sensitive(False)
        self.start_btn.set_sensitive(True)
        p = subprocess.call(["killall", "minidlnad"])

    def populate_fields(self):
        if os.path.isfile(sharesfile):
            shares_handle = open(sharesfile, 'r')
            for line in shares_handle:
                splitline = line.rstrip('\n').split(',')
                if len(splitline) > 1:
                    share_tuple = (splitline[0],splitline[1])
                    self.listStore.append(share_tuple)
            shares_handle.close()

        if os.path.isfile(netfile):
            netfile_handle = open(netfile, 'r')
            for line in netfile_handle:
                self.Netinf_Combo.set_active(int(line))
            netfile_handle.close

        if os.path.isfile(portfile):
            portfile_handle = open(portfile, 'r')
            for line in portfile_handle:
                self.Port_Entry.set_text(line.rstrip('\n'))
            portfile_handle.close()

    def on_addShare_clicked(self, widget):
       self.dialog = Gtk.FileChooserDialog("Please choose a folder", self, 
Gtk.FileChooserAction.SELECT_FOLDER,
(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
"Select", Gtk.ResponseType.OK))

       self.response = self.dialog.run()
       if self.response == Gtk.ResponseType.OK:
           self.selected_path = self.dialog.get_filename()
           self.selected_dirname = os.path.basename(self.selected_path)
           self.listStore.append([self.selected_dirname, self.selected_path])
           self.save_btn.set_sensitive(True)

       self.dialog.destroy()

    def on_delShare_clicked(self,widget):
        self.selection = self.SharesList.get_selection()
        model, paths = self.selection.get_selected_rows()
        
        # Get the TreeIter instance for each path
        for path in paths:
            iter = model.get_iter(path)
           # Remove the ListStore row referenced by iter
            model.remove(iter)
 
    def on_save_clicked(self, widget):
        self.save_btn.set_sensitive(False)
        if not os.path.isdir(confdir):
            os.mkdir(confdir)
        if not os.path.isdir(dbdir):
            os.mkdir(dbdir)
        shares = ""
        conf_shares = ""

        for row in self.listStore:
            shares += '''%s,%s\n''' % (row[0], row[1])
            conf_shares += "media_dir=%s\n" % (row[1])

        selected_netinf = self.Netinf_Combo.get_active()
        selected_netinf_name = self.Netinf_Combo.get_active_text()
        selected_port = self.Port_Entry.get_text()

        conf = '''
# This is the configuration file for the MiniDLNA daemon, a DLNA/UPnP-AV media
# server.
#
# Unless otherwise noted, the commented out options show their default value.
#
# On Debian, you can also refer to the minidlna.conf(5) man page for
# documentation about this file.

# Specify the user name or uid to run as.
user=%s


# Path to the directory you want scanned for media files.
#
# This option can be specified more than once if you want multiple directories
# scanned.
#
# If you want to restrict a media_dir to a specific content type, you can
# prepend the directory name with a letter representing the type (A, P or V),
# followed by a comma, as so:
#   * "A" for audio    (eg. media_dir=A,/var/lib/minidlna/music)
#   * "P" for pictures (eg. media_dir=P,/var/lib/minidlna/pictures)
#   * "V" for video    (eg. media_dir=V,/var/lib/minidlna/videos)
%s

# Path to the directory that should hold the database and album art cache.
db_dir=%s

# Path to the directory that should hold the log file.
log_dir=%s

# Type and minimum level of importance of messages to be logged.
#
# The types are "artwork", "database", "general", "http", "inotify",
# "metadata", "scanner", "ssdp" and "tivo".
#
# The levels are "off", "fatal", "error", "warn", "info" or "debug".
# "off" turns of logging entirely, "fatal" is the highest level of importance
# and "debug" the lowest.
#
# The types are comma-separated, followed by an equal sign ("="), followed by a
# level that applies to the preceding types. This can be repeated, separating
# each of these constructs with a comma.
#
# The default is to log all types of messages at the "warn" level.
#log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=warn

# Use a different container as the root of the directory tree presented to
# clients. The possible values are:
#   * "." - standard container
#   * "B" - "Browse Directory"
#   * "M" - "Music"
#   * "P" - "Pictures"
#   * "V" - "Video"
# If you specify "B" and the client device is audio-only then "Music/Folders"
# will be used as root.
root_container=B

# Network interface(s) to bind to (e.g. eth0), comma delimited.
# This option can be specified more than once.
network_interface=%s

# IPv4 address to listen on (e.g. 192.0.2.1/24).
# If omitted, the mask defaults to 24. The IPs are added to those determined
# from the network_interface option above.
# This option can be specified more than once.
#listening_ip=

# Port number for HTTP traffic (descriptions, SOAP, media transfer).
# This option is mandatory (or it must be specified on the command-line using
# "-p").
port=%s

# URL presented to clients (e.g. http://example.com:80).
#presentation_url=/

# Name that the DLNA server presents to clients.
# Defaults to "hostname: username".
friendly_name="Minidlna (GUI) %s"

# Serial number the server reports to clients.
# Defaults to 00000000.
serial=681019810597110

# Model name the server reports to clients.
model_name="Windows Media Connect compatible (MiniDLNA) GUI by Quentin Gibert"

# Model number the server reports to clients.
# Defaults to the version number of minidlna.
#model_number=

# Automatic discovery of new files in the media_dir directory.
inotify=yes

# List of file names to look for when searching for album art.
# Names should be delimited with a forward slash ("/").
# This option can be specified more than once.
album_art_names=Cover.jpg/cover.jpg/AlbumArtSmall.jpg/albumartsmall.jpg
album_art_names=AlbumArt.jpg/albumart.jpg/Album.jpg/album.jpg
album_art_names=Folder.jpg/folder.jpg/Thumb.jpg/thumb.jpg

# Strictly adhere to DLNA standards.
# This allows server-side downscaling of very large JPEG images, which may
# decrease JPEG serving performance on (at least) Sony DLNA products.
#strict_dlna=no

# Support for streaming .jpg and .mp3 files to a TiVo supporting HMO.
#enable_tivo=no

# Notify interval, in seconds.
#notify_interval=895

# Path to the MiniSSDPd socket, for MiniSSDPd support.
#minissdpdsocket=/run/minissdpd.sock
''' % (username, conf_shares, dbdir, confdir, selected_netinf_name, selected_port, username)


        print(conf)
        shares_handle = open(sharesfile, 'w')
        print(shares, file=shares_handle)
        shares_handle.close()
        netinf_handle = open(netfile, 'w')
        print(selected_netinf, file=netinf_handle)
        netinf_handle.close()
        port_handle = open(portfile, 'w')
        print(selected_port, file=port_handle)
        port_handle.close()
        dlna_conf_handle = open(minidlna_conf_file, 'w')
        print(conf, file=dlna_conf_handle)
        dlna_conf_handle.close()

def main():
    GObject.threads_init()
    win = MainWindow()
    win.connect('destroy', lambda w: Gtk.main_quit())

    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()

