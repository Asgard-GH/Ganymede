import disnake
from members.recordroles import recordroles
class Role:
    def __init__(self, id):
        self.id = id
class Guild:
    def __init__(self, id):
        self.id = id
class Member:
    def __init__(self, roles, id, guild):
        self.roles = roles
        self.id = id
        self.guild = guild
bob = Member(
    [
        Role(1234), Role(5678), Role(9012)
    ],
    909876,
    Guild(13579)
)
recordroles(bob)