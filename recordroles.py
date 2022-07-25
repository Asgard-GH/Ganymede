from pathlib import Path

import disnake
import os
import json

def recordroles(member) -> list:
    """Record a members roles and save them to the respective JSON file.
    
    The function is called when a member leaves or was kicked/banned by a
    moderator with the moderator choosing to preserve their roles. They can
    use /restoreroles after joining back to automatically restore their roles.
    
    Parameters
    ----------
    member: `disanke.Member` The member that left / was kicked or banned.
    """
    script_parent_dir = (os.path.pardir(__file__))
    guild_id = member.guild.id
    member_role_ids = [role.id for role in member.roles]
    with open(f"{script_parent_dir}/guild_roles/{guild_id}.json", "w") as f:
        pass  # create file if not existent
    with open(f"{script_parent_dir}/guild_roles/{guild_id}.json", "r+") as f:
        guild_roles = json.load(f)
        guild_roles[member.id] = member_role_ids
        json.dump(guild_roles, f)