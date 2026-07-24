import re

import httpx


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


class MinecraftLookupError(ValueError):
    pass


async def fetch_minecraft_profile(ign: str) -> dict[str, str]:
    username = ign.strip()
    if not USERNAME_RE.fullmatch(username):
        raise MinecraftLookupError("Minecraft IGN must be 3-16 characters and use only letters, numbers, or underscores.")

    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)

    if response.status_code == 204 or response.status_code == 404:
        raise MinecraftLookupError("That Minecraft username was not found.")
    if response.status_code >= 400:
        raise MinecraftLookupError("Minecraft profile lookup failed. Try again later.")

    data = response.json()
    uuid = data.get("id")
    name = data.get("name")
    if not uuid or not name:
        raise MinecraftLookupError("Minecraft returned an incomplete profile.")

    return {
        "ign": name,
        "uuid": uuid,
        "account_type": "premium",
        "premium": True,
        "head_url": f"https://mc-heads.net/head/{uuid}/128",
        "avatar_url": f"https://mc-heads.net/avatar/{uuid}/128",
    }


def create_cracked_profile(ign: str) -> dict:
    username = ign.strip()
    if not USERNAME_RE.fullmatch(username):
        raise MinecraftLookupError("Minecraft IGN must be 3-16 characters and use only letters, numbers, or underscores.")

    default_skin = "MHF_Steve" if sum(ord(char) for char in username) % 2 == 0 else "MHF_Alex"
    return {
        "ign": username,
        "uuid": None,
        "account_type": "cracked",
        "premium": False,
        "head_url": f"https://mc-heads.net/head/{default_skin}/128",
        "avatar_url": f"https://mc-heads.net/avatar/{default_skin}/128",
    }


async def resolve_minecraft_profile(ign: str, account_type: str) -> dict:
    if account_type == "premium":
        return await fetch_minecraft_profile(ign)
    if account_type == "cracked":
        return create_cracked_profile(ign)
    raise MinecraftLookupError("Choose Premium or Cracked account type.")
