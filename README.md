# 🤖 KAY/O

*"If I'm powered down, restart me. You leave me for scrap, I'll kill you."*

KAY/O is a Discord bot that will send a message when a team / league is playing.

## Deployment

Here is a `docker-compose` file for deploying KAY/O yourself.
```yaml
version: '3'
services:
  kayayluh-twitch:
    container_name: kayo
    image: ghcr.io/haysberg/kayo:main
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=<your_discord_token_here>
      - RIOT_API_KEY=<riot_key_here>
      - DEPLOYED=production
    volumes:
      - /your/path/here:/app/db
```