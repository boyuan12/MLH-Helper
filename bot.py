import discord
from discord.ext import commands
import requests

client = discord.Client()

SECRET_KEY="secretkey"
BASE_URL="http://0.0.0.0:1234"

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    id = client.user.id
    if str(id) in message.content:

        # get the question
        resp = str(message.content).split(f"<@!{str(id)}> ")[1]

        if resp == "checkin":
            await message.channel.send(f"Welcome! Please go ahead and go to {BASE_URL}/{message.author.id}. When you finished, please tag me and say finished, and I will send you more information!")

        elif resp == "attendees" and "mlh" in [y.name.lower() for y in message.author.roles]:
            curr = requests.get("https://mlh-events.now.sh/na-2020").json()[0]["name"]
            csv_file = requests.get(f"{BASE_URL}/api/generate/{curr}/{SECRET_KEY}").json()["url"]
            channel = await message.author.create_dm()
            await channel.send(f"Here's the file link to download: {csv_file}")

        elif resp == "attendees" and "mlh" not in [y.name.lower() for y in message.author.roles]:
            await message.channel.send(f"Oops, looks like you don't have permission to use this command!")

        elif resp == "finished":
            resp = requests.get(f"{BASE_URL}/api/current_hack/{message.author.id}").json()["resp"]
            await message.channel.send(resp)


client.run("NzE4NTAwOTk1Nzg4ODMyODkx.Xtpy1g.61iB7LnWwL82BgUBcvm0k2dRXfs")