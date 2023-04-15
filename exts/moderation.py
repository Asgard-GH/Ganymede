import datetime
import re
import threading
import sqlite3
import time
import typing

import disnake
from disnake.ext import commands

import constants as c
import errors
import utils


class ModerationCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.slash_command(
        name="mute",
        description="Mutes a user for the specified duration",
        options=[
            disnake.Option(
                "target", "The user to be muted", disnake.OptionType.user, True
            ),
            disnake.Option(
                "duration", "How long the target should be muted",
                disnake.OptionType.string
            ),
            disnake.Option(
                "until", "Until when the target should be muted",
                disnake.OptionType.string
            ),
            disnake.Option(
                "reason", "The reason why the target is muted",
                disnake.OptionType.string
            )
        ]
    )
    async def mute(
            self, inter: disnake.CmdInter, target: disnake.Member,
            duration: str = None,
            until: str = None, reason: str = None
    ):
        await utils.lbyl(inter=inter, target=target, action="mute")
        await utils.confirm(inter)
        await self.client.wait_for("button_click", timeout=15.0)
        twenty_eight_days = 2419200.0
        if until:  # input sanitization: until must be yyyy-MM-dd hh:mm:ss
            if (
                    not re.findall(
                        r"\d{4}-0\d|1[0-2]-0\d|1\d|2\d|3[0-1] \d\d:\d\d:\d\d",
                        until
                    )
                    or not len(until) == 19
            ):
                raise errors.InvalidParameterError(
                    "Parameter `until` only accepts the format "
                    f"yyyy-MM-dd hh:mm:ss, not '{until}'. "
                    "Check the format and values of your input."
                )
        if duration:
            timeout_duration = utils.string_to_timedelta(duration)
            until_dt = None
        elif until:
            timeout_duration = None
            until_dt = datetime.datetime.strptime(
                until, "%Y-%m-%d %H:%M:%S"
            )
            now = datetime.datetime.now()
            if until_dt < now:  # until lies in the past
                raise errors.PunishmentDurationError(
                    "`until` can't be a date in the past"
                )
            if until_dt - now > datetime.timedelta(weeks=52):
                raise errors.PunishmentDurationError(
                    "Punishments can't be longer than one year unless "
                    "permanent"
                )
        else:
            timeout_duration = None
            until_dt = None
        if duration:
            await target.timeout(
                duration=(
                    timeout_duration
                    if timeout_duration.total_seconds() < twenty_eight_days
                    else datetime.timedelta(days=28)
                ),
                reason=f"Mute issued by {inter.author}, reason: {reason}"
            )
        elif until:
            await target.timeout(
                until=(
                    until_dt
                    if int(
                        until_dt.strftime("%s")
                    ) - time.time() < twenty_eight_days
                    else datetime.datetime.fromtimestamp(
                        time.time() + twenty_eight_days
                    )
                ),
                reason=f"Mute issued by {inter.author}, reason: {reason}"
            )
        if timeout_duration:
            until_timestamp = time.time() + timeout_duration.total_seconds()
        elif until_dt:
            until_timestamp = int(until_dt.strftime("%s"))
        else:
            until_timestamp = -1
        if until_timestamp > time.time() + twenty_eight_days:
            connection = sqlite3.connect("ganymede.db")
            cursor = connection.cursor()
            with connection:
                cursor.execute(
                    f"""INSERT INTO Timeouts
                        {until_timestamp}, {target.id}, {target.guild.id}"""
                )
            threading.Timer(
                twenty_eight_days, function=utils.renew_timeout,
                kwargs={"member": target}
            ).start()
        await utils.log(
            guild=inter.guild, colour=c.SUCCESS, title="Member muted",
            fields={
                "🔍 Actor:": f"{inter.author.mention}\n(ID: {inter.author.id})",
                "🎯 Target:": f"{target.mention}\n(ID: {target.id})",
                "❓ Reason:": reason if reason else "None",
                "🕑 Duration:": timeout_duration if timeout_duration else (
                    f"Until {until_dt}" if until_dt else "Indefinite"
                )
            }, log_type="Mod_Log"
        )
        inter_embed = disnake.Embed(
            color=disnake.Color(c.SUCCESS),
            title="✅ Successfully muted",
            timestamp=datetime.datetime.now()
        ).add_field(
            name="🎯 Target:",
            value=f"{target.mention}\n(ID: {target.id})",
            inline=False
        ).add_field(
            name="🔍 Actor:",
            value=f"{inter.author.mention}\n(ID: {inter.author.id})",
            inline=False
        ).add_field(
            name="❓ Reason:",
            value=reason if reason else "None",
            inline=False
        ).add_field(
            name="🕑 Duration:",
            value=(
                timeout_duration if timeout_duration else (
                    f"Until {until_dt}" if until_dt else "Indefinite"
                )
            ),
            inline=False
        )
        await inter.send(embed=inter_embed)

    @commands.slash_command(
        name="kick",
        description="Kicks a member from the server",
        options=[
            disnake.Option(
                "target", "The member to be kicked", disnake.OptionType.user,
                True
            ),
            disnake.Option(
                "reason", "The reason why the target is kicked",
                disnake.OptionType.string
            ),
            disnake.Option(
                "save_roles", "Whether or not to remember the target's roles",
                disnake.OptionType.boolean
            )
        ]
    )
    async def kick(
            self, inter: disnake.CmdInter, target: disnake.Member,
            reason: str = None, save_roles: bool = False
    ):
        await utils.lbyl(inter=inter, target=target, action="kick")
        await utils.confirm(inter)
        await self.client.wait_for("button_click", timeout=15.0)
        if save_roles:
            utils.record_roles(member=target)
        await inter.guild.kick(user=target, reason=reason)
        await utils.log(
            guild=inter.guild, colour=c.SUCCESS, title="Member kicked",
            fields={
                "🔍 Actor:": f"{inter.author.mention}\n(ID: {inter.author.id})",
                "🎯 Target:": f"{target.mention}\n(ID: {target.id})",
                "❓ Reason:": reason if reason else "None",
                "📝 Roles:": "Saved" if save_roles else "Not saved"
            }, log_type="Mod_Log"
        )
        inter_embed = disnake.Embed(
            color=disnake.Color(c.SUCCESS),
            title="✅ Successfully muted",
            timestamp=datetime.datetime.now()
        ).add_field(
            name="🎯 Target:",
            value=f"{target.mention}\n(ID: {target.id})",
            inline=False
        ).add_field(
            name="🔍 Actor:",
            value=f"{inter.author.mention}\n(ID: {inter.author.id})",
            inline=False
        ).add_field(
            name="❓ Reason:",
            value=reason if reason else "None",
            inline=False
        ).add_field(
            name="📝 Roles:",
            value=(
                "Saved" if save_roles else "Not saved"
            ),
            inline=False
        )
        await inter.send(embed=inter_embed, ephemeral=True)

    @commands.slash_command(
        name="ban",
        description="Bans a member from the server",
        options=[
            disnake.Option(
                name="target", description="The member to be banned",
                type=disnake.OptionType.user
            ),
            disnake.Option(
                name="user_id",
                description="User ID as an alternative to 'target'",
                type=disnake.OptionType.integer
            ),
            disnake.Option(
                name="reason",
                description="The reason why the target is kicked",
                type=disnake.OptionType.string
            ),
            disnake.Option(
                name="save_roles",
                description="Whether or not to remember the target's roles",
                type=disnake.OptionType.boolean
            ),
            disnake.Option(
                name="delete_messages",
                description="How many days back the target's messages should "
                            "be deleted",
                type=disnake.OptionType.integer,
                choices={
                    f"{n} day{'s' if n != 1 else ''}": n for n in range(8)
                }
            )
        ]
    )
    async def ban(
            self, inter: disnake.CmdInter, target: disnake.Member,
            user_id: int = 0, reason: str = "", save_roles: bool = False,
            delete_messages: typing.Literal[0, 1, 2, 3, 4, 5, 6, 7] = 0
    ):
        if (target is not None and user_id is not None) \
                and target.id != user_id:
            raise errors.InvalidTargetError(
                f"Specified target '{target.name}' does not match\n"
                f"the specified ID '{user_id}'. Consider using only one of the"
                " arguments."
            )
        if not (target or user_id):
            raise errors.InvalidParameterError(
                "Either 'target' or 'user_id' must be specified."
            )
        target: disnake.Member
        await utils.lbyl(inter=inter, target=target, action="ban")
        await utils.confirm(inter=inter)
        await self.client.wait_for("button_click", timeout=15.0)
        if not target and user_id:
            target = await self.client.fetch_user(user_id)
            if target.id in [member.id for member in inter.guild.members]:
                target = inter.guild.fetch_member(target.id)
        if save_roles:
            utils.record_roles(target)
        await inter.guild.ban(
            user=target, reason=reason, delete_message_days=delete_messages
        )
        await utils.log(
            guild=inter.guild, colour=c.SUCCESS, title="Member banned",
            fields={
                "🔍 Actor:": f"{inter.author.mention}\n(ID: {inter.author.id})",
                "🎯 Target:": f"{target.mention}\n(ID: {target.id})",
                "❓ Reason:": reason if reason else "None",
                "📝 Roles:": "Saved" if save_roles else "Not saved"
            }, log_type="Mod_Log"
        )
        inter_embed = disnake.Embed(
            color=disnake.Color(c.SUCCESS),
            title="✅ Successfully banned",
            timestamp=datetime.datetime.now()
        ).add_field(
            name="🎯 Target:",
            value=f"{target.mention}\n(ID: {target.id})",
            inline=False
        ).add_field(
            name="🔍 Actor:",
            value=f"{inter.author.mention}\n(ID: {inter.author.id})",
            inline=False
        ).add_field(
            name="❓ Reason:",
            value=reason if reason else "None",
            inline=False
        ).add_field(
            name="📝 Roles:",
            value=(
                "Saved" if save_roles else "Not saved"
            ),
            inline=False
        )
        await inter.send(embed=inter_embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(ModerationCommands(bot))
