# Discord Bot

## Executing the bot with docker (recommended)
Create a `.env` file and build the docker image:
```console
docker build -t discord-bot .
```

Run the docker image to start the bot:
```console
docker run --rm discord-bot
```

## Executing the bot in your local machine

**Prerequisites**
- Python 3.10.2 (other versions may or may not work)
- ffmpeg

Create a `.env` file in the project directory with the following content:
```text
DISCORD_TOKEN=...
```

Run the bot with the following command:
```console
python bot.py
```
