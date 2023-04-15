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
import os
import typing

import disnake

CREDIT = ("""Credits for the Discord bot **Ganymede**:

💻 Developer: <@560865133476315156>
**--------------------**
Software information:
Written in [Python](<https://www.python.org/>) 🐍
Using, inter alia, [disnake](<https://github.com/DisnakeDev/disnake>)
Open Source via [GitHub](<https://github.com/>): """
    """[repository](<https://github.com/Asgard-GH/Ganymede>)
**--------------------**
Special thanks to:
🎨 <@764719874382888970> (symbol art)
📝 <@801450128526802984> (feedback and ideas)
❓ <@256133489454350345> (disnake and Python help)
💡 <@213396745231532032> / <@732767207783661578> (inspiration)
♥ """)
# Embed colours
DEFAULT = 15277667
SUCCESS = 6224896  # Lime
WARNING = 16776960  # Yellow
EXCEPTION = 16711680  # Red
LOG_CHANNELS = typing.Literal[
    "Message Log", "Moderation Log", "Reports", "Server Log"
]
FILE_PATH = os.path.dirname(__file__)
ACTION_LITERAL = typing.Literal[
    # Every action only a staff member can take.
    "access_record",
    "ban",
    "change_tier",
    "edit_blacklist",
    "edit_member_tier",
    "inspection_mark",
    "kick",
    "lockdown",
    "mute",
    "query_channel",
    "quarantine",
    "remove_channel",
    "revoke_verif",
    "set_tier_role",
    "set_util_role",
    "slowmode",
    "tempban",
    "tempmute",
    "unquarantine",
    "warn",
]
MEMBER_ACTION_LITERAL = typing.Literal[
    "ban",
    "kick",
    "mute",
    "quarantine",
    "tempban",
    "tempmute",
    "unquarantine",
    "warn",
]
REQ_CLEARANCE = {
    # Numbers represent (1-5):  Trial Moderator, Moderator, Head Moderator,
    #                           Server Administrator, Owner
    # Having a higher clearance tier than required works, too.
    "query_channel": 1,
    "query_tier": 1,
    "access_record": 1,
    "kick": 1,
    "mute": 1,
    "tempmute": 1,
    "warn": 1,
    "ban": 2,
    "inspection_mark": 2,
    "quarantine": 2,
    "tempban": 2,
    "slowmode": 3,
    "unquarantine": 3,
    "set_channel": 4,
    "edit_member_tier": 4,
    "lockdown": 4,
    "remove_channel": 5,
    "revoke_verif": 4,
    "change_tier": 5,
    "edit_blacklist": 5,
    "set_tier": 5,
    "set_util_role": 5,
    "set_visible_category": 4
}
DEV_ID = 560865133476315156
CAPTCHA_CONSEQUENCES = ["None", "1h timeout", "2h timeout", "1d timeout", "Kick", "Permanent ban"]
QUARANTINE_OVERWRITE = disnake.PermissionOverwrite(
    administrator=False, ban_members=False, change_nickname=False, connect=False, create_forum_threads=False,
    kick_members=False, read_messages=False, send_messages=False, send_messages_in_threads=False,
    send_tts_messages=False, speak=False, view_audit_log=False, view_channel=False, view_guild_insights=False,
)
MUTE_OVERWRITE = disnake.PermissionOverwrite(
    administrator=False, ban_members=False, change_nickname=False, connect=False, create_forum_threads=False,
    kick_members=False, read_messages=True, send_messages=False, send_messages_in_threads=False,
    send_tts_messages=False, speak=False, view_audit_log=False, view_channel=True, view_guild_insights=False,
)
