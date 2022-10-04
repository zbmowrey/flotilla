#!/bin/bash

# Drop this into Transmission's transmission-home directory to run post-processing scripts.

#!/bin/bash
find /torrent_complete/ -name '*.rar' -execdir unrar e -o- {} \;
find /torrent_complete/ -name '*.avi' -exec chmod 777 {} \;
find /torrent_complete/ -name '*.mkv' -exec chmod 777 {} \;