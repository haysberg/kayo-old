# 🤖 KAY/O

*"If I'm powered down, restart me. You leave me for scrap, I'll kill you."*

KAY/O is a Discord bot that will send a message when a team / league is playing.

## Using the hosted version

If you want to invite KAY/O on your server, using [this link](https://discord.com/api/oauth2/authorize?client_id=1112803073094594601&permissions=18432&scope=bot).

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
      - LOGLEVEL=INFO
    volumes:
      - /your/path/here:/app/db
```
