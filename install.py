import os
import shutil


def copy(src_file, folder):
    shutil.copyfile(src_file, os.path.join(folder, os.path.basename(src_file)))

# Any addons in the root of the addons folder will be loaded when HexChat loads. Thus we need the plugin
# to be in the root folder, and all the pre-requisites to be in the 'rat_lib' folder.
# (The plugin adds this sub folder to the sys.path so those modules can be imported.)

install_folder = os.path.join(os.getenv('APPDATA'), "HexChat", "addons")
os.makedirs(install_folder, exist_ok=True)

lib_folder = os.path.join(install_folder, "rat_lib")
os.makedirs(lib_folder, exist_ok=True)

copy("Python/rat_hexchat.py", install_folder)
copy("Python/alert.wav", lib_folder)
copy("Python/rat_client.py", lib_folder)
copy("Python/rat_config.py", lib_folder)
copy("Python/rat_irc.py", lib_folder)
copy("Python/rat_lib.py", lib_folder)