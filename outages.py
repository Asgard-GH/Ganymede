import asyncio
import time
import dotenv
import os

import disnake
from disnake.ext import commands

FILE_PATH = os.path.dirname(__file__)
ASGARD = "<@560865133476315156>"
credentials = dotenv.dotenv_values(FILE_PATH + "/.env")
client = commands.Bot(
    command_prefix="g?", intents=disnake.Intents.all()
)
offline_timestamp = None
unresolved = False

@client.listen("on_ready")
async def on_ready():
    global dev
    global dev_dm
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    _guild = await client.fetch_guild(1005837173343387711)
    dev = await _guild.fetch_member(560865133476315156)
    dev_dm = await dev.create_dm()


def alert_message():
        return f"""<@&1010092361440829490> Ganymede has gone offline on {
    offline_timestamp
    }.
The outage has either not been acknowledged by Asgard or confirmed
as unintentional. Please attempt to resolve the issue
and / or alert {ASGARD} about this.
"""


async def send_messages():
    alert_guild = await client.fetch_guild(998993584718102631)
    alert_channel = await alert_guild.fetch_channel(1010092927361495050)
    await alert_channel.send(alert_message())
    notif_ch = await alert_guild.fetch_channel(998993585296912409)
    await notif_ch.send(
        "<@998996826252394596> has just gone offline.\n"
        "The developer team is already working on fixing this issue.\n"
        "Please wait while the problem is being resolved..."
    )


class GreenButton(disnake.ui.Button):
    async def callback(self, inter: disnake.CmdInter):
        global unresolved

        unresolved = False
        await inter.send("✅ Bot downtime has been confirmed as intentional!")
        # Disable both buttons
        for item in self.view.children:
            item.disabled = True
        await inter.message.edit(
            view=self.view
        )


class RedButton(disnake.ui.Button):
    async def callback(self, inter: disnake.MessageInteraction):
        global unresolved
        
        unresolved = False  # Avoid duplicate alert
        await inter.send(
            "❌ Bot downtime has been confirmed as **un**intentional!\n"
            "Alerting downtime team"
            )
        await send_messages()
        # Disable both buttons
        for item in self.view.children:
            item.disabled = True
        await inter.message.edit(
            view=self.view
        )
        resolved_view = disnake.ui.View().add_item(
            ResolvedButton(
                style=disnake.ButtonStyle(1), label="Resolved", emoji="🕑"
            )
        )
        await dev_dm.send(
            "Click the button below once the issue has been resolved.",
            view=resolved_view
            )


class ResolvedButton(disnake.ui.Button):
    async def callback(self, inter: disnake.MessageInteraction):
        alert_guild = await client.fetch_guild(998993584718102631)
        alert_channel = await alert_guild.fetch_channel(1010092927361495050)
        await alert_channel.send("The downtime has been marked as resolved!")
        notif_ch = await alert_guild.fetch_channel(998993585296912409)
        await notif_ch.send(
            "<@998996826252394596> is now back online.\n"
            "We thank you for your patience ♥"
        )
        # Disable button
        for item in self.view.children:
            item.disabled = True
        await inter.message.edit(
            view=self.view
        )


@client.listen("on_presence_update")
async def on_presence_update(before: disnake.Member, after: disnake.Member):
    global offline_timestamp
    global unresolved

    if (
        before.status == disnake.Status.online
        and after.status == disnake.Status.offline
        and after.id == 998996826252394596
        and after.guild.id == 1005837173343387711
            ):
        offline_timestamp = f"<t:{round(time.time())}:F>"
        unresolved = True
        _view = disnake.ui.View(timeout=60)
        _view.add_item(
            GreenButton(
                style=disnake.ButtonStyle(3), label="Okay", emoji="✅"
                )
            )
        _view.add_item(
            RedButton(
                style=disnake.ButtonStyle(4), label="Alert", emoji="❌"
            )
        )
        await dev_dm.send(
            "Ganymede has gone offline.\n"
            "Please press the green button if this is intentional\n"
            "or the red button if this is an unplanned outage.\n\n"
            "The downtime team will be alerted automatically in 60 seconds.",
            view=_view
            )
        await asyncio.sleep(60)
        if unresolved:
            await send_messages()
            resolved_view = disnake.ui.View()
            resolved_view.add_item(
                ResolvedButton(
                    style=disnake.ButtonStyle(1), label="Resolved", emoji="🕑"
                )
            )
            await dev_dm.send(
                "Click the button below once the issue has been resolved.",
                view=resolved_view
                )
            unresolved = False


client.run(credentials["OUTAGES"])
