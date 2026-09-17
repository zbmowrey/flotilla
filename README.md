# flotilla

Definition: (n) a fleet of ships or boats. 

## What

A docker-compose file built to let you quickly stand up a usenet stack. 

## Why

Because I can't find an equivalent that I like. The ones I have found are out of date or incomplete in some way. I'll take the best ideas from those and add my own personal touches. 

## Where

Right here. 

## When

When I find time. This is a personal project, not a job. Deadlines are expressly forbidden. 

## How

With my own two hands. And maybe yours. 

## How, Part 2 (Installation)

- Clone the repo
- CD into the folder
- Edit the env file as appropriate for your use-case
- `docker-compose up -d`
- See the .env file for ports for the various downloaders

## How changes reach the NAS (since 2026-09-16)

- Portainer runs this repo as a **git-backed stack** with **GitOps polling every 5 minutes**:
  a commit on `main` is deployed within 5 minutes, removed services are pruned. There is no
  separate deploy step; `make deploy` only forces an immediate pull.
- Images are **pinned** to exact tags. Renovate (`renovate.json`) opens PRs for bumps on
  Saturday mornings; merging the PR is the upgrade. Watchtower was removed (it cannot talk to
  Docker 29 and made unreviewed changes).
- Secrets and host paths live in the Portainer stack environment, not in git. `.env`
  (gitignored) is the local mirror used by the scripts.
- Drift checks and API helpers live in `~/code/nas` (`scripts/nas-portainer.py`).
