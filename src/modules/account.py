import time

from .core.discord import Discord
from .core.utilities import build_ctx_properties, b64_decode
from .core.discord_ws import DiscordWS
from .core.fingerprint import Fingerprint


class Account:
    def __init__(self, token: str):
        self.token: str = token
        self.token_id: int = b64_decode(token.split(".")[0] + "==")

    def initialize(self, fingerprint: Fingerprint, proxy: str):
        self.discord = Discord(self.token, fingerprint, proxy)

        success, response = self.discord.index()
        if not success:
            return False, "Failed to send index request."

        self.discord_ws = DiscordWS(self.token, self.discord.fingerprint)
        self.discord_ws.connect()
        retries = 0
        while self.discord_ws.session_id == "" and retries < 0.1 * 10 * 60:
            time.sleep(0.1)
            retries += 1
        if self.discord_ws.session_id == "":
            return False, "Failed to fetch session id."

        return True, ""

    def get_server_info(self, invite_code: str):
        success, response = self.discord.get_server_info(invite_code)
        if not success:
            return False, f"Request failed. (get_server_info) ({response})"

        server_info = response.json()
        server_id = server_info.get("guild_id")
        if not server_id:
            return False, "Invalid server invite."

        return True, server_info

    def join_server(
        self, invite_code: str, captcha_key: str = None, captcha_rqtoken: str = None
    ):
        success, server_info = self.get_server_info(invite_code)
        if not success:
            return False, server_info
        server_id = server_info["guild_id"]

        success, response = self.discord.join_server(
            self.discord_ws.session_id,
            build_ctx_properties(
                server_id, server_info["channel"]["id"], server_info["channel"]["type"]
            ),
            invite_code,
            captcha_key,
            captcha_rqtoken,
        )
        if not success:
            return False, f"Request failed. (join_server) ({response})"
        data = response.json()
        if data.get("captcha_sitekey"):
            return False, data
        if not data.get("guild_id"):
            return False, f"Failed to join server. ({response.text})"

        return True, ""
