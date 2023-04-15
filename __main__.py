"""
Copyright 2022 Ganymede Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software. Access to the software
is not to be used for malicious actions or the attempt thereof, including,
but not limited to: Circumventing security and/or moderation features of the
Discord Bot "Ganymede" (hereafter referred to as "Ganymede", "Ganymedes"),
evading automated moderation features of Ganymede, harming the performance of
Ganymede, using Ganymede in guilds that do not intend to allow you to use it
(this includes restricting your account from parts of Ganymedes features or its
entirety), gaining control of Ganymedes account.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import asyncio
import datetime
import sqlite3
import time
import threading
import traceback
import typing
import logging

import disnake
from disnake.ext import (
    commands,
)
import dotenv

import errors
import constants as c

# import verification as vfc
import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s|%(created)f:%(levelname)s:%(funcName)s:%(message)s"
)
handler = logging.FileHandler("log.txt")
handler.setFormatter(formatter)
logger.addHandler(handler)
credentials = dotenv.dotenv_values(c.FILE_PATH + "/.env")
client = commands.Bot(
    command_prefix="g?",
    intents=disnake.Intents.all(),
)
client.load_extension("exts.moderation")


@client.event
async def on_ready():
    """Called when the client is done preparing the data received from API."""
    print(f"Logged in as {client.user} (ID: {client.user.id})")


@client.event
async def on_message_delete(
        message: disnake.Message,
):
    """Called when a message that is visible to the client is deleted."""
    if message.author.bot:
        return  # Bots are ignored
    await utils.log(
        guild=message.guild,
        colour=c.DEFAULT,
        title="Message deletion",
        fields={
            "📋 Basic information:": "Message sent by member "
                                    f"{message.author.mention} (ID: {message.author.id})\nin channel "
                                    f"{message.channel.mention} was deleted on "
                                    f"{time.strftime('%b. %d', time.gmtime())} at (approx.) "
                                    f"{time.strftime('%H:%M:%S UTC', time.gmtime())}",
            "📃 Message content:": message.content,
        },
        log_type="Msg_Log",
    )


@client.event
async def on_message_edit(
        before: disnake.Message,
        after: disnake.Message,
):
    """Called when a message that is visible to the client is edited."""
    if before.author.bot:
        return  # Bots are ignored
    await utils.log(
        guild=before.guild,
        colour=c.DEFAULT,
        title="Message edit",
        fields={
            "📋 Basic information:": "Message sent by member "
                                    f"{before.author.mention} (ID: {before.author.id})\nin channel "
                                    f"{before.channel.mention} was edited on "
                                    f"{time.strftime('%b. %d', time.gmtime())} at (approx.) "
                                    f"{time.strftime('%H:%M:%S UTC', time.gmtime())}",
            "📃 Message content (before):": before.content,
            "📃 Message content (after):": after.content,
        },
        log_type="Msg_Log",
    )


@client.before_slash_command_invoke
async def before_slash_command_invoke(
        inter: disnake.CmdInter,
):
    """Called before a slash command is invoked

    The function checks whether the command is valid, e.g. whether the user is
    blacklisted and whether the user has the required clearance tier.
    """
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    with connection:
        cursor.execute(
            f"""SELECT D_ID
                FROM Blacklisteds
                WHERE D_ID={inter.author.id}
            """
        )
        if cursor.fetchall():
            raise errors.BlacklistedUserError(
                "You are blacklisted from using Ganymedes services"
            )
        cursor.execute(
            f"""SELECT Tier FROM Clearances WHERE
            D_ID={inter.author.id} AND G_ID={inter.guild.id}"""
        )
        tier_results = cursor.fetchone()
        is_owner = inter.author.id == inter.guild.owner_id
        try:
            req_clearance = c.REQ_CLEARANCE[inter.application_command.name]
            if tier_results and not is_owner:
                author_tier = tier_results[0]
            elif is_owner:
                author_tier = 5  # Guild owner should override permissions
            else:
                raise errors.MissingPermissionsError(
                    f"Command '{inter.application_command.name}' requires "
                    f"clearance tier `{req_clearance}` (or higher), not `0`"
                )
            if req_clearance > author_tier:
                raise errors.MissingPermissionsError(
                    f"Command '{inter.application_command.name}' requires "
                    f"clearance tier `{req_clearance}` (or higher), not "
                    f"`{author_tier}`"
                )
        except KeyError:  # Command name is not in constants.REQ_CLEARANCE
            logging.log(f"before_slash_command_invoke: skipping command \"{inter.application_command.name}\"")


@client.event
async def on_slash_command_error(
        inter: disnake.CmdInter,
        exception: disnake.ext.commands.errors.CommandInvokeError,
):
    """Called to handle slash command errors: display error message and log."""
    try:
        assert exception.original
        exc_is_custom = False
    except AttributeError:  # Custom exceptions don't have an 'original' attr
        exc_is_custom = True
    exc = exception.original if not exc_is_custom else exception
    if isinstance(
            exc,
            asyncio.exceptions.TimeoutError,
    ):
        return  # A confirm button timed out
    exc_name = exc.__class__.__name__
    cmd = inter.application_command
    filled = inter.filled_options
    params = " ".join(
        [f"{key}: {str(value)}" for key, value in filled.items()]
    )
    exception_embed = (
        disnake.Embed(
            color=disnake.Color(c.EXCEPTION),
            title="⚠ An error occurred:",
        )
        .add_field(
            name="🔍 Error type:",
            value=f"`{exc_name}`",
            inline=False,
        )
        .add_field(
            name="📃 Error description:",
            value=exc.args[0],
            inline=False,
        )
        .add_field(
            name="👾 Think this a bug?",
            value="Contact <@560865133476315156> or join "
                  "https://discord.gg/re2AkgyFbS",
            inline=False,
        )
        .set_footer(text=f"/{cmd.name} {params} | t: {int(time.time())}")
    )
    if exc_is_custom:
        # This is likely a user error, logging is mostly for support purposes
        logger.info(
            msg=f"\nBad user input in slash command '{cmd.name}' by "
                f"{inter.author} (ID: {inter.author.id}):\n\t"
                + "\n".join(traceback.format_exception(exc))
        )
    else:
        logger.warning(msg="\n\t" + "\n".join(traceback.format_exception(exc)))
    await inter.send(
        embed=exception_embed,
        ephemeral=True,
    )


@client.event
async def on_member_join(
        member: disnake.Member,
):
    """Called when a member joins a guild visible to the client."""
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    cursor.execute(
        f"""SELECT Setting
            FROM Captchas
            WHERE G_ID={member.guild.id}
        """
    )
    captcha_setting = cursor.fetchall()[0]
    if not captcha_setting:
        return
    if captcha_setting[0]:  # Captchas are enabled on this server
        for channel in member.guild.channels:
            if channel.category_id == visible_category:
                await channel.set_permissions(
                    target=member, overwrite=c.MUTE_OVERWRITE, reason="Pending captcha test"
                )
            else:
                await channel.set_permissions(
                    target=member, overwrite=c.QUARANTINE_OVERWRITE, reason="Pending captcha test"
                )
        captcha_passed = False
        captcha = utils.captcha_gen()
        await member.send(
            f"""Hello, Ganymede bot here!
To ensure that you're a human, the owner of the server you just joined has enabled my captcha system.
To see the server channels, please enter the result of the maths problem below as digits:
`{captcha[0][0]} {captcha[1]} {captcha[0][1]}`"""
        )
        response = (await client.wait_for("message", timeout=300)).content
        if response != captcha[2]:
            cursor.execute(f"""SELECT consequence FROM Captchas WHERE G_ID={member.guild.id}""")
            penalty = cursor.fetchone()[0]
            await member.send(
                "I'm sorry, that's not the correct answer." +
                (
                    " The punishment as configured by the server owner "
                    f"is `{c.CAPTCHA_CONSEQUENCES[penalty].lower()}`"
                    if penalty != "None" and penalty else ""
                )
            )
            if penalty != "None" and penalty:
                match c.CAPTCHA_CONSEQUENCES[penalty]:
                    case "1h timeout":
                        await member.guild.timeout(member, duration=3600.0, reason="Failed captcha test")
                    case "2h timeout":
                        await member.guild.timeout(member, duration=7200.0, reason="Failed captcha test")
                    case "1d timeout":
                        await member.guild.timeout(member, duration=86400.0, reason="Failed captcha test")
                    case "Kick":
                        await member.guild.kick(member, reason="Failed captcha test")
                        return
                    case "Permanent ban":
                        await member.guild.ban(member, delete_message_days=0, reason="Failed captcha test")
                        return
        else:
            captcha_passed = True
        if captcha_passed:
            await member.send(f"`{captcha[2]}` is correct! You now have access to the server.")
    for channel in member.guild.channels:
        await channel.set_permissions(member, overwrite=None)
    with connection:
        cursor.execute(
            f"""SELECT Roles
                FROM Recorded
                WHERE D_ID={member.id} AND G_ID={member.guild.id}"""
        )
        results = cursor.fetchone()
        if results is None:
            return
        guild_role_ids = [role.id for role in member.guild.roles]
        recorded_roles = results[0].split(":")  # Role list is serialized
        for role_id in recorded_roles:
            role_id = int(role_id)
            if role_id not in guild_role_ids:  # The role has been deleted
                continue
            if role_id == member.guild.id:  # @everyone role
                continue
            role = member.guild.get_role(role_id)
            await member.add_roles(
                role,
                reason="Restoring saved roles",
            )
            cursor.execute(
                f"""DELETE FROM Recorded
                    WHERE D_ID={member.id} AND G_ID={member.guild.id}"""
            )


@client.event
async def on_member_update(
        before: disnake.Member,
        after: disnake.Member,
):
    """Called when a member updates their profile."""
    if before.current_timeout and not after.current_timeout:
        timeout_duration = after.current_timeout - datetime.datetime.now()
        if timeout_duration < datetime.timedelta(days=28):
            return  # This timeout doesn't have to be renewed
        until_timestamp = int(after.current_timeout.strftime("%s"))
        twenty_eight_days = 2419200.0
        connection = sqlite3.connect("ganymede.db")
        cursor = connection.cursor()
        with connection:
            cursor.execute(
                f"""INSERT INTO Timeouts
                    {until_timestamp}, {before.id}, {before.guild.id}"""
            )
        threading.Timer(
            twenty_eight_days,
            function=utils.renew_timeout,
            kwargs={"member": before},
        ).start()


@client.slash_command(
    name="credits",
    description="Roll the credits!",
)
async def acknowledgements(
        inter: disnake.CmdInter,
):
    """Displays a credits message."""
    await inter.send(
        c.CREDIT + inter.author.mention + " (using Ganymede)",
        ephemeral=True,
    )


@client.slash_command(
    name="set_channel",
    description="Assigns a utility function to a channel",
)
async def set_channel(
        inter: disnake.CmdInter,
        channel: disnake.TextChannel,
        purpose: c.LOG_CHANNELS,
):
    """Assigns a utility function (log type) to a disnake.TextChannel."""
    col_name = {
        "Message Log": "Msg_Log",
        "Moderation Log": "Mod_log",
        "Reports": "Reports",
        "Server Log": "Serv_Log",
    }[purpose]
    guild_id = inter.guild.id
    channel_id = channel.id
    connection = sqlite3.connect("ganymede.db")
    with connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Util_channels WHERE G_ID={guild_id}")
        if cursor.fetchall():  # There are settings entries for this guild
            cursor.execute(
                f"""UPDATE Util_channels SET {col_name}={channel_id}
                    WHERE G_ID={guild_id}"""
            )
        else:  # Create new settings entry
            cursor.execute(
                f"""INSERT INTO Util_channels (
                        G_ID,
                        {col_name}
                    ) VALUES (
                        {guild_id},
                        {channel_id}
                    )"""
            )
    await inter.send(f"'{purpose}' is now assigned to {channel.mention}")
    await channel.send(
        f"This channel has been assigned the '{purpose}' purpose"
    )


@client.slash_command(description="Removes a channel's utility function")
async def remove_channel(
        inter: disnake.CmdInter,
        purpose: c.LOG_CHANNELS,
):
    """Removes a utility function (log type) from a disnake.TextChannel."""
    col_name = {
        "Message Log": "Msg_Log",
        "Moderation Log": "Mod_log",
        "Reports": "Reports",
        "Server Log": "Serv_Log",
    }[purpose]
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    with connection:
        cursor.execute(
            f"""UPDATE Util_channels
                SET {col_name}=NULL
                WHERE G_ID={inter.guild.id}"""
        )


@client.slash_command(
    name="query_channel",
    description="Check which channel is assigned to a given utility function",
)
async def query_channel(
        inter: disnake.CmdInter,
        purpose: c.LOG_CHANNELS,
):
    """Checks the utility function (log type) of a disnake.TextChannel."""
    channel_col = [
        "G_ID",
        "Message Log",
        "Moderation Log",
        "Reports",
        "Server Log",
    ].index(purpose)
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Util_channels WHERE G_ID={inter.guild.id}")
    settings = cursor.fetchall()
    if settings is None:
        raise errors.EntryNotFoundError(
            "Guild doesn't have any utility channels"
        )
    queried_id = settings[0][channel_col]  # Only one result
    if queried_id is None:
        raise errors.PurposeNotSetError(
            "This purpose hasn't been assigned to any channel yet"
        )
    if queried_id not in [channel.id for channel in inter.guild.channels]:
        raise errors.ChannelNotFoundError("This channel has been deleted")
    await inter.send(
        f"'{purpose}' is assigned to "
        f"{inter.guild.get_channel(queried_id).mention}"
    )


@client.slash_command(description="Creates or edits a member's clearance tier")
async def set_tier(
        inter: disnake.CmdInter,
        target: disnake.Member,
        tier: typing.Literal[
            "Regular Member",
            "Trial Moderator",
            "Moderator",
            "Head Moderator",
            "Administrator",
        ],
):
    """Sets a member's clearance tier."""
    if target.bot:
        raise errors.InvalidTargetError("Bot users can't have clearance tiers")
    tier_num = [
        "Regular Member",
        "Trial Moderator",
        "Moderator",
        "Head Moderator",
        "Administrator",
    ].index(
        tier
    )  # R. M. = 0, T. M. = 1, M. = 2, ...
    connection = sqlite3.connect("ganymede.db")
    with connection:
        cursor = connection.cursor()
        cursor.execute(
            f"""SELECT * FROM Clearances
                WHERE D_ID={target.id} AND G_ID={inter.guild.id}"""
        )
        if not cursor.fetchall():
            cursor.execute(
                f"""INSERT INTO Clearances (
                    D_ID,
                    Tier,
                    G_ID
                ) VALUES (
                    {target.id},
                    {tier_num},
                    {inter.guild.id}
                )"""
            )
        else:
            cursor.execute(
                f"""UPDATE Clearances
                    SET Tier={tier_num}
                    WHERE D_ID={target.id} AND G_ID={inter.guild.id}"""
            )
    ending = "'s" if target.display_name[-1] != "s" else "'"
    info_embed = disnake.Embed(
        colour=c.DEFAULT,
        title=f"Tier change for {target}",
        description=f"{target.mention}{ending} clearance tier has been set to "
                    f"`{tier_num}` ({tier})",
    )
    await inter.send(embed=info_embed)


@client.slash_command(description="Check which clearance tier a member has")
async def query_tier(
        inter: disnake.CmdInter,
        target: disnake.Member,
):
    """Checks a member's clearance tier."""
    if target.bot:
        raise errors.InvalidTargetError("Bot users can't have clearance tiers")
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    cursor.execute(
        f"""SELECT Tier
            FROM Clearances
            WHERE D_ID={target.id} AND G_ID={inter.guild.id}
        """
    )
    tier_results = cursor.fetchone()
    tier_num = tier_results[0] if tier_results else 0
    tier = [
        "Regular Member",
        "Trial Moderator",
        "Moderator",
        "Head Moderator",
        "Administrator",
    ][tier_num]
    ending = "'s" if target.display_name[-1] != "s" else "'"
    info_embed = disnake.Embed(
        colour=c.DEFAULT,
        title=f"Tier query for {target}",
        description=f"{target.mention}{ending} clearance tier is set to "
                    f"`{tier_num}` ({tier})",
    )
    await inter.send(embed=info_embed)


@client.slash_command(
    description="Enables or disables captcha verification", options=[
        disnake.Option(name="enable", choices=["Yes", "No"], type=disnake.OptionType.string, required=True),
        disnake.Option(
            name="penalty", description="The consequence for failing the captcha", choices=[
                "None", "1h timeout", "2h timeout", "1d timeout", "Kick", "Permanent ban"
            ]
        )
    ]
)
async def set_captcha(inter: disnake.CmdInter, enable: str, penalty: str | None = None):
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    if inter.author.id != inter.guild.owner_id:
        cursor.execute(
            f"""SELECT Tier FROM Clearances WHERE
                    D_ID={inter.author.id} AND G_ID={inter.guild.id}"""
        )
        tier_results = cursor.fetchone()
        if not tier_results:
            raise errors.MissingPermissionsError(
                f"Command '{inter.application_command.name}' requires "
                f"clearance tier `5`, not `0`"
            )
        else:
            author_tier = tier_results[0]
            raise errors.MissingPermissionsError(
                f"Command '{inter.application_command.name}' requires "
                f"clearance tier `5` (or higher), not `{author_tier}`"
            )
    with connection:
        enable = True if enable == "Yes" else False
        if enable:
            if cursor.execute(
                    f"""SELECT *
                    FROM Captchas
                    WHERE G_ID={inter.guild.id}
                """
            ).fetchall():
                # Guild has a setting for captchas, update instead of inserting
                cursor.execute(
                    f"""UPDATE Captchas
                        SET Setting=1
                        WHERE G_ID={inter.guild.id}
                    """
                )
            else:
                cursor.execute(
                    f"""INSERT INTO Captchas (
                        G_ID,
                        Setting
                    ) VALUES (
                        {inter.guild.id}, 1
                    )"""
                )
        elif not enable:
            if cursor.execute(
                    f"""SELECT *
                    FROM Captchas
                    WHERE G_ID={inter.guild.id}
                """
            ).fetchall():
                # Guild has a setting for captchas, update instead of inserting
                cursor.execute(
                    f"""UPDATE Captchas
                        SET Setting=0
                        WHERE G_ID={inter.guild.id}
                    """
                )
            else:
                cursor.execute(
                    f"""INSERT INTO Captchas (
                        G_ID,
                        Setting
                    ) VALUES (
                        {inter.guild.id}, 0
                    )"""
                )
        if penalty:
            if cursor.execute(
                    f"""SELECT *
                    FROM Captchas
                    WHERE G_ID={inter.guild.id}
                """
            ).fetchall():
                # Guild has a setting for captchas, update instead of inserting
                cursor.execute(
                    f"""UPDATE CAPTCHAS
                        SET consequence={c.CAPTCHA_CONSEQUENCES.index(penalty)}
                        WHERE G_ID={inter.guild.id}
                    """
                )
            else:
                cursor.execute(
                    f"""INSERT INTO Captchas (
                            G_ID,
                            consequence
                        ) VALUES (
                            {inter.guild.id}, {c.CAPTCHA_CONSEQUENCES.index(penalty)}
                        )"""
                )
    await inter.send("Successfully updated your captcha settings")


@client.slash_command(description="Makes a category visile to all following quarantined members")
async def set_visible_category(inter: disnake.CmdInter, category: disnake.CategoryChannel):
    ...


@client.slash_command(description="Reports a member")
async def report(
        inter: disnake.CmdInter,
        target: disnake.Member,
        reason: str,
        proof: str = None,
):
    """Reports a member in the guild's corresponding log channel."""
    await utils.confirm(inter)
    await client.wait_for(
        "button_click",
        timeout=15.0,
    )
    log = await utils.log(
        guild=inter.guild,
        colour=c.DEFAULT,
        title="Member report",
        fields={
            "📋 Basic information:": f"Member {target.mention} "
                                    f"(ID: {target.id}) was reported by member {inter.author.mention} "
                                    f"(ID: {inter.author.id})",
            "❓ Reason:": reason,
            "🔍 Proof": proof if proof else "Unspecified",
        },
        log_type="Reports",
    )
    if log != -1:
        await inter.send(
            embed=disnake.Embed(
                colour=c.SUCCESS,
                title="Report successful",
                description=f"You successfully reported {target.mention} for "
                            f"the reason '{reason}'",
            ),
            ephemeral=True,
        )
    else:
        await inter.send(
            "This server doesn't have the corresponding log channel",
            ephemeral=True,
        )


@client.command()
async def reload(
        ctx: commands.Context,
):
    """Dev-exclusive command for reloading extensions."""
    if ctx.author.id != c.DEV_ID:  # Developer account ID
        # await ctx.send("This command is exclusive to the developer")
        return
    ext_list = ["moderation"]
    for ext in ext_list:
        client.reload_extension(f"exts.{ext}")


if __name__ == "__main__":
    client.run(credentials["TOKEN"])
