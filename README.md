# Discord Bot

## Executing the bot with docker (recommended)
1. Create a `.env` file in the project directory with the following contents:
    ```text
    DISCORD_TOKEN=...
    GUILD_ID=...
    ACTIVITY=...
    ```

    The `DISCORD_TOKEN` represents your bot's secret token, the `GUILD_ID` represents your server/guild's ID, and the `ACTIVITY` represents the bot's status/activity message.

2. Build the docker image:
    ```console
    docker build -t discord-bot .
    ```

3. Run the docker image to start the bot:
    ```console
    docker run --rm discord-bot
    ```

## Executing the bot in your local machine

**Prerequisites**
- Python 3.10.13 (other versions may or may not work)
- ffmpeg

Create the `.env` file as described above and run the bot with the following command:
```console
python bot.py
```
