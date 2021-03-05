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
- Edit your hosts file (/etc/hosts or c:\windows\system32\drivers\etc\hosts) to add the dashboard domain: dashboard.local. 
- Visit dashboard.local in your browser. 
- The various downloaders are available at "localhost:$port": 
  - These are customizable in the .env file. 
  - SABNzbd: 8080
  - NZBGet: 8081
  - Transmission: 8082
  - Radarr: 8083
  - Lidarr: 8084
  - Sonarr: 8085
  - Bazarr: 8086
  - Headphones: 8087
  - Mylar: 8088
  - LazyLibrarian: 8089
