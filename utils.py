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
import datetime
import random
import re
import sqlite3
import threading
import time
import typing

import disnake

import constants
import errors


class ConfirmView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=15.0)

    @disnake.ui.button(label="Confirm", style=disnake.ButtonStyle.green)
    async def confirm(
            self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        # PyCharm is getting on my nerves about the unused parameter
        assert button == button
        await inter.response.edit_message(content="Confirmed!")


def record_roles(member: disnake.Member) -> None:
    """Record a members roles and save them to the respective JSON file.

    The function is called when a member leaves or was kicked/banned by a
    moderator with the moderator choosing to preserve their roles. They can
    use /restore_roles after joining back to automatically restore their roles.

    Parameters
    ----------
    member: :class:`disnake.Member` The member that left / was kicked or banned
    """
    if not member.roles:
        return  # Avoid IndexError when no roles can be recorded
    connection = sqlite3.connect("ganymede.db")
    with connection:
        cursor = connection.cursor()
        cursor.execute(
            f"""INSERT INTO Recorded (D_ID, G_ID, Roles)
                VALUES (
                    {member.id},
                    {member.guild.id},
                    '{":".join([str(role.id) for role in member.roles])}'
                )"""  # SQL does not accept lists, so we serializze the list
        )


def string_to_timedelta(string: str) -> datetime.timedelta:
    """Converts a string to a timedelta.
    
    The function converts strings that represent composite numbers with time
    units (Ex. "1w5d", "3M 2w", "4d50m") into a datetime.timedelta object.
    Valid units: M - months, w - weeks, d - days, h - hours, m - minutes,
    s - seconds
    The highest recognized numbers are two digits long. If a number isn't
    followed by a digit, it is ignored.

    Parameters
    ----------
    string: :class:`str` The string that should be converted into a
    datetime.timedelta object.

    Returns
    -------
    td: :class:`datetime.timedelta` The converted timedelta.

    Raises
    ------
    `errors.RepeatingUnitsError`: A time unit is repeated. Ex. 2w3w, 5M3d1M
    `errors.InvalidParameterError`: No time specification was found. Ex. foo
    `errors.PunishmentDurationError`: The punishment duration exceeds a year.
    This is not allowed in order to save resources. Ex. 2y, 60w
    """
    if any([substring in string for substring in ["ns", "ms", "y"]]):
        raise errors.InvalidParameterError("Invalid time unit: ns, ms or y")
    months = re.findall(r"\d{1,2}(?=M)", string)
    weeks = re.findall(r"\d{1,2}(?=w)", string)
    days = re.findall(r"\d{1,2}(?=d)", string)
    hours = re.findall(r"\d{1,2}(?=h)", string)
    minutes = re.findall(r"\d{1,2}(?=m)", string)
    seconds = re.findall(r"\d{1,2}(?=s)", string)
    if any(
            [
                len(iterable) > 1 for iterable in [
                    months, weeks, days, hours, minutes, seconds
                ]
            ]
    ):
        raise errors.RepeatingUnitsError(
            "Parameter `duration` contains non-unique units"
        )
    months = int(months[0]) if months else 0
    weeks = int(weeks[0]) if weeks else 0
    days = int(days[0]) if days else 0
    hours = int(hours[0]) if hours else 0
    minutes = int(minutes[0]) if minutes else 0
    seconds = int(seconds[0]) if seconds else 0
    td = datetime.timedelta(
        weeks=months * 4 + weeks, days=days, hours=hours, minutes=minutes,
        seconds=seconds
    )
    if (
            td == datetime.timedelta(seconds=0) and
            re.findall(r"0[Mwdhms]", string)
    ):
        # inter.author specified zero duration => revoke punishment
        return td
    elif td == datetime.timedelta(seconds=0) and string is not None:
        raise errors.InvalidParameterError(
            "Parameter `duration` accepts values like '2w4d' or '1d45m', not "
            f"'{string}'."
        )
    if td > datetime.timedelta(weeks=52):
        raise errors.PunishmentDurationError(
            "Punishments can't be longer than one year unless permanent"
        )
    return td


async def is_above(
        a: disnake.Member | disnake.ClientUser, b: disnake.Member
) -> bool:
    """Checks if member `a` is above member `b` in the role hierarchy.

    The function checks if `a` is above `b` by checking if `a` has a higher
    top_role than `b` and returns the resulting boolean. If `a` is the guild
    owner, the function automatically returns True. If `b` is the guild
    owner, the function automatically returns False.

    Parameters
    ----------
    a: :class:`disnake.Member` | :class:`disnake.ClientUser` The first member
    b: :class:`disnake.Member` The second member

    Returns
    -------
    a.top_role > b.top_role: :class:`bool` Whether or not `a` is above `b`.
    True if `a` is the guild owner, False if `b` is the guild owner.
    """
    # a is sometimes the client which doesn't have a guild attr
    owner = await b.guild.getch_member(b.guild.owner_id)
    if type(a) == disnake.ClientUser:
        a = await b.guild.getch_member(a.id)
    if b == owner:
        return False
    if a != owner:
        # a isn't guild owner, role hierarchy applies
        return a.top_role > b.top_role
    else:
        # a is guild owner, overwrites role hierarchy
        return True


def inter_in_guild(inter: disnake.CmdInter) -> bool:
    """Checks if `inter` was invoked in a guild."""

    return bool(inter.guild)


async def lbyl(
        inter: disnake.CmdInter, target: disnake.Member,
        action: constants.MEMBER_ACTION_LITERAL
):
    """Checks if all necessary requirements for a moderator action are met.

    The function checks whether the command is used in a guild, the person has
    the required clearance tier, moderator is targeting themselves, the
    moderator is high enough in the hierarchy to perform this action and
    whether the bot is high enough in the hierarchy to perform this action.
    (Look Before You Leap)
    """
    if not inter_in_guild(inter):
        raise errors.CommandEnvironmentError(
            "This command can only be used in guilds"
        )
    if inter.author == target:
        raise errors.InvalidTargetError(f"You can't {action} yourself")
    if not await is_above(inter.author, target):
        raise errors.MissingPermissionsError(
            f"You don't have permission to {action} {target.mention} as you "
            "are below or equal to them in the role hierarchy and/or they own "
            "this server"
        )
    if not await is_above(inter.bot.user, target):
        raise errors.MissingPermissionsError(
            f"Cannot {action} {target.mention} as the bot is below or equal to"
            " them in the role hierarchy and/or they own this server"
        )


async def log(
    guild: disnake.Guild, colour: int, title: str,
    fields: dict[str: str], footer: str = f"t: {round(time.time())}",
    log_type=constants.LOG_CHANNELS
) -> typing.Union[int, None]:
    """Universal log function

    The function takes in the guild where something should be logged and
    constructs a log embed, fetches the respective log channel id and sends the
    embed there.
    """
    log_embed = disnake.Embed(
        colour=colour, title=title
    )
    for name, value in fields.items():
        log_embed.add_field(name=name, value=value, inline=False)
    log_embed.set_footer(text=footer)
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT {log_type} FROM Util_channels WHERE G_ID={guild.id}"
    )
    try:
        channel_id = cursor.fetchall()[0][0]
    except IndexError:
        return -1  # The guild doesn't have a log channel for this
    if channel_id not in [channel.id for channel in guild.text_channels]:
        return -1  # The corresponding channel was deleted
    log_channel = await guild.fetch_channel(channel_id)
    await log_channel.send(embed=log_embed)


async def confirm(inter: disnake.CmdInter):
    info_embed = disnake.Embed(
        colour=constants.DEFAULT,
        title=inter.application_command.name.upper()
    )
    for arg in inter.data.options:
        info_embed = info_embed.add_field(name=arg.name, value=arg.value)
    info_embed.set_footer(
        text=f"Times out after 15 seconds | t: {int(time.time())}"
    )
    await inter.send(
        "Please confirm your command:", embed=info_embed, ephemeral=True,
        view=ConfirmView()
    )


async def renew_timeout(member: disnake.Member):
    """Renews a member's timeout duration to circumvent the 28-day maxmimum
    timeout duration.

    Parameters
    ----------
    member: :class:`disnake.Member` The member whose timeout should be renewed

    Returns
    -------
    None
    """
    twenty_eight_days = 2419200.0
    connection = sqlite3.connect("ganymede.db")
    cursor = connection.cursor()
    cursor.execute(
        f"""SELECT until FROM Timeouts
        WHERE D_ID={member.id} AND G_ID={member.guild.id}"""
    )
    until_timestamp = cursor.fetchone()[0]
    remaining = until_timestamp - time.time()
    if remaining < twenty_eight_days and remaining != -1:
        await member.timeout(duration=remaining)
        with connection:
            cursor.execute(
                f"""DELETE FROM Timeouts
                WHERE D_ID={member.id} AND G_ID={member.guild.id}"""
            )
    else:
        await member.timeout(duration=twenty_eight_days)
        threading.Timer(
            twenty_eight_days, function=renew_timeout,
            kwargs={"member": member}
        ).start()


def captcha_gen() -> list[list[str], str]:
    diacritics = [
        " ̍", " ̎", " ̄", " ̅", " ̿", " ̑", " ̆", " ̐", " ͒", " ͗", " ͑", " ̇", " ̈", " ̊", " ͂", " ̓", " ̈́", " ͊", " ͋",
        " ͌", " ̃", " ̂", " ͐", " ́", " ̋", " ̏", " ̽", " ̉", " ͣ", " ͤ", " ͥ", " ͦ", " ͧ", " ͨ", " ͩ", " ͪ", " ͫ", " ͬ",
        " ͭ", " ͮ", " ͯ", " ̾", " ͛", " ͆", " ̚"
    ]  # Thanks to github.com/gregoryneal for this list
    numbers = random.choices(
        ["two", "three", "four", "five", "six", "seven", "eight"], k=2
    )
    str_to_int = {"two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8"}
    operand = ["+", "-", "*"][random.randint(0, 2)]
    result = eval(str_to_int[numbers[0]] + operand + str_to_int[numbers[1]])
    numbers = [
        "".join(
            [char + random.choice(diacritics).strip() if random.randint(0, 2) in [0, 1] else char for char in num]
        ) for num in numbers
    ]
    return [numbers, operand, str(result)]
