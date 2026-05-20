# Makefile for syncing Flotilla files with remote host

# Remote host and path
REMOTE_HOST := dtz
REMOTE_PATH := /volume1/Flotilla/

# Exclusions
EXCLUDES := --exclude='.flotilla' --exclude='data'

# Rsync options:
# -a : archive (preserves permissions, symlinks, times, etc.)
# -v : verbose
# -z : compress during transfer
# -e ssh : specify remote shell
RSYNC_OPTS := -avz $(EXCLUDES) -e ssh

# Local path (relative to Makefile)
LOCAL_PATH := .

# Python interpreter for helper scripts
PYTHON := python3

.PHONY: push pull inventory

## Sync from local to remote (push)
push:
	rsync $(RSYNC_OPTS) $(LOCAL_PATH)/ $(REMOTE_HOST):$(REMOTE_PATH)

## Sync from remote to local (pull)
pull:
	rsync $(RSYNC_OPTS) $(REMOTE_HOST):$(REMOTE_PATH) $(LOCAL_PATH)/

## Snapshot the Portainer host into ./inventory/
inventory:
	$(PYTHON) scripts/portainer_inventory.py
