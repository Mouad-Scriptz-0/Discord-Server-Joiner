import websocket, zlib, threading, time

from .config import config
from .console import Console
from .utilities import json_to_string, string_to_json
from .fingerprint import Fingerprint


class DiscordWS:
    def __init__(self, token: str, fingerprint: Fingerprint):
        self.token = token
        self.fingerprint = fingerprint

        self.app = websocket.WebSocketApp(
            "wss://gateway.discord.gg/?encoding=json&v=9&compress=zlib-stream",
            header={
                "Accept-Language": self.fingerprint.headers["Accept-Language"],
                "User-Agent": self.fingerprint.headers["User-Agent"],
            },
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=lambda ws, error: Console.error(str(error)),
        )
        self.decompress_obj = zlib.decompressobj()
        self.token_id = self.token.split(".")[0]
        self.keep_running = True

        self.session_id: str = ""
        self.connected: bool = None
        self.s: int = 0

    def send(self, payload: dict):
        if self.keep_running:
            self.app.send(json_to_string(payload))

    def on_open(self, _):
        Console.debug("WebSocket connection opened", self.token_id)

    def keep_alive(self):
        Console.debug("Keep-alive thread running", f"Interval: {self.heartbeat}")
        while self.keep_running:
            time.sleep(self.heartbeat)
            self.send({"op": 1, "d": self.s})

    def on_message(self, _, msg):
        msg = self.decompress_obj.decompress(msg, 0)
        message = string_to_json(msg)

        Console.debug(
            "WebSocket message received", str(msg) if len(msg) < 200 else "Too long."
        )

        t = message.get("t", "UNKNOWN")
        op = message.get("op", -1)
        d = message.get("d", {})

        if message.get("s"):
            self.s = message["s"]

        if t == "GUILD_CREATE" and op == 0:
            guild_id = str(d["id"])
            self.send({"op": 36, "d": {"guild_id": guild_id}})
            self.send(
                {
                    "op": 37,
                    "d": {
                        "subscriptions": {
                            guild_id: {
                                "typing": True,
                                "activities": True,
                                "threads": True,
                            }
                        }
                    },
                }
            )
            if config["console"]["debug"]:
                Console.information("Subscribed to guild.", guild_id)

        if op == 10:  # Server hello
            self.send(
                {
                    "op": 2,
                    "d": {
                        "token": self.token,
                        "capabilities": 30717,
                        "properties": {
                            "os": "Windows",
                            "browser": "Chrome",
                            "device": "",
                            "system_locale": "en-US",
                            "has_client_mods": False,
                            "browser_user_agent": self.fingerprint.headers[
                                "User-Agent"
                            ],
                            "browser_version": self.fingerprint.browser_version,
                            "os_version": "10",
                            "referrer": "",
                            "referring_domain": "",
                            "referrer_current": "",
                            "referring_domain_current": "",
                            "release_channel": "stable",
                            "client_build_number": self.fingerprint.build_number,
                            "client_event_source": None,
                        },
                        "presence": {
                            "status": "unknown",
                            "since": 0,
                            "activities": [],
                            "afk": False,
                        },
                        "compress": False,
                        "client_state": {"guild_versions": {}},
                    },
                }
            )
            self.heartbeat = d["heartbeat_interval"] / 1000
            self.keep_alive_thread = threading.Thread(
                target=self.keep_alive, daemon=True
            )
            self.keep_alive_thread.start()

        if t == "READY" and op == 0:
            self.session_id = d["session_id"]
            Console.debug("Authenticated websocket.", self.session_id)
            self.send(
                {
                    "op": 4,
                    "d": {
                        "guild_id": None,
                        "channel_id": None,
                        "self_mute": True,
                        "self_deaf": False,
                        "self_video": False,
                        "flags": 2,
                    },
                }
            )

    def connect_thread(self, reconnect: bool = False):
        try:
            self.connected = self.app.run_forever(
                host="gateway.discord.gg",
                origin="https://discord.com",
                reconnect=reconnect,
            )
        except Exception as e:
            print(e)

    def connect(self, reconnect: bool = False):
        threading.Thread(target=self.connect_thread, args=(reconnect,)).start()
