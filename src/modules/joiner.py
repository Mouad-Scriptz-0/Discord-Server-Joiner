import random, time, math

from typing import List
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor, as_completed

from .core.solver import Solver
from .core.config import config
from .core.console import Console
from .core.utilities import format_proxy, get_lines, get_proxy_info
from .core.discord_ws import DiscordWS
from .core.fingerprint import get_fingerprints

from .account import Account


class Joiner:
    def __init__(
        self,
        build_number: int,
        mode: str = "d",
        threads: int = 10,
        join_delay: int = 60 * 5,
    ):
        self.build_number = build_number
        self.mode = mode
        self.threads = threads
        self.join_delay = join_delay

        self.tokens: List[str] = []
        self.proxies: List[str] = []
        self.invites: List[str] = []

        self.proxies_cycle: cycle = None

        self.total_joins: int = 0
        self.total_fails: int = 0

        Console.clear()

    def _get_settings(self):
        self.mode = Console.adv_input(
            "Mode (ja[join all] | d[distribute invites])", "string"
        )
        self.threads = Console.adv_input("Threads", "digit")
        self.join_delay = Console.adv_input("Delay between joins (in seconds)", "digit")
        Console.clear()
        Console.information(
            f"Mode: {self.mode} | Threads: {self.threads} | Join delay: {self.join_delay}"
        )

    def _get_resources(self):
        # Tokens
        self.tokens = get_lines("input/tokens.txt", True)
        self.tokens_count = len(self.tokens)
        if self.tokens_count == 0:
            Console.error("No tokens detected in input/tokens.txt")
            time.sleep(2)
            exit(-1)
        if config["shuffle tokens"]:
            random.shuffle(self.tokens)
        Console.information("Loaded tokens", str(self.tokens_count))

        # Proxies
        proxies = get_lines("input/proxies.txt", True)
        if config["shuffle proxies"]:
            random.shuffle(proxies)
        if len(proxies) == 0:
            Console.error("No proxies detected in input/proxies.txt")
            time.sleep(2)
            exit(-1)
        formatted_proxies = []
        for proxy in proxies:
            success, proxy = format_proxy(proxy)
            if not success:
                continue
            formatted_proxies.append(proxy)
        if len(formatted_proxies) == 0:
            Console.error("Failed to format proxies. (Recommended: user:pass@ip:port)")
            time.sleep(2)
            exit(-1)
        self.proxies = formatted_proxies
        self.proxies_count = len(self.proxies)
        self.proxies_cycle = cycle(formatted_proxies)

        # Invites
        self.invites = get_lines("input/server-invites.txt", True)
        self.invites_count = len(self.invites)
        if self.invites_count == 0:
            Console.error("No invites detected in input/server-invites.txt")
            time.sleep(2)
            exit(-1)
        Console.information("Loaded invites", str(self.invites_count))

    def _get_fingerprint(self, proxy: str):
        fp = random.choice(get_fingerprints())
        success, data = get_proxy_info(proxy)
        if not success:
            return False, data
        fp.build_number = self.build_number
        fp.timezone = data["timezone"]["name"]
        return True, fp

    def _skip_token(self, token: str, token_id: str, discord_ws: DiscordWS):
        with open(f"output/tokens/{token_id}.txt", "a") as f:
            f.write("- Token skipped.\n")
        with open("output/skipped.txt", "a") as f:
            f.write(f"{token}\n")
        Console.error("Skipping token.", token)
        if discord_ws:
            discord_ws.app.close()
            discord_ws.keep_running = False

    def _process_token(self, token: str, invite_codes: str, proxy: str = None):
        joins = 0
        fails = 0

        account = Account(token)

        success, fingerprint = self._get_fingerprint(proxy)
        if not success:
            Console.error("Failed to get a fingerprint.")
            self._skip_token(token, account.token_id, account.discord_ws)
            return joins, fails

        Console.information("Initializing token...", account.token_id)
        success, error_text = account.initialize(fingerprint, proxy)
        if not success:
            Console.error("account.initialize", error_text)
            self._skip_token(token, account.token_id, account.discord_ws)
            return joins, fails
        Console.information("Initialized token.", account.token_id)

        for invite_code in invite_codes:
            Console.information(
                "Joining server...", f"{account.token_id} | {invite_code}"
            )

            success, error_text = account.join_server(invite_code)

            if not success:
                fails += 1
            else:
                joins += 1

            if isinstance(error_text, dict):  # Captcha
                data = error_text
                Console.error("Captcha detected.")
                if config["captcha"]["solve"]:
                    Console.captcha("Solving captcha...")
                    solver = Solver(proxy)
                    success, key = solver.solve(
                        data["captcha_sitekey"],
                        "https://discord.com/channels/@me",
                        data["captcha_rqdata"],
                        proxy,
                    )
                    if not success:
                        Console.captcha("Failed to solve captcha.", str(key))
                        self._skip_token(token, account.token_id, account.discord_ws)
                        return joins, fails
                    Console.captcha("Solved captcha.", f"{key}")

                    success, error_text = account.join_server(
                        invite_code, key, data["captcha_rqtoken"]
                    )
                    if type(error_text) == dict:
                        Console.captcha("Captcha key not accepted.")
                        continue
                else:
                    Console.captcha(
                        "Solving captcha disabled. Skipping token.", account.token_id
                    )
                    self._skip_token(token, account.token_id, account.discord_ws)
                    return joins, fails

            if not success and type(error_text) != dict:
                Console.error("Failed to join server", error_text)
                with open(f"output/tokens/{account.token_id}.txt", "a") as f:
                    f.write(f"- Failed to join [{invite_code}]\n")
            else:
                with open(f"output/tokens/{account.token_id}.txt", "a") as f:
                    f.write(f"+ Joined [{invite_code}]\n")
                Console.success("Joined server.", f"{account.token_id} | {invite_code}")

            if not len(invite_codes) == 1:
                delay = self.join_delay + random.randint(
                    int(self.join_delay / 4), int(self.join_delay / 2)
                )
                Console.information("Token sleeping.", f"{account.token_id} | {delay}s")
                time.sleep(delay)

        return joins, fails

    # Modes
    def _join_all(self) -> dict:
        tokens_invites = {}
        for token in self.tokens:
            tokens_invites[token] = self.invites
        return tokens_invites

    def _distribute(self) -> dict:
        invites_per_token = math.floor(self.tokens_count / self.invites_count)
        invites_cycle = cycle(self.invites)
        tokens_invites = {}
        for token in self.tokens:
            tokens_invites[token] = list(
                set([next(invites_cycle) for _ in range(invites_per_token)])
            )
        return tokens_invites

    # Run
    def run(self):
        self._get_settings()
        self._get_resources()
        print()

        if self.mode in ["ja", "join all"]:
            tokens_invites = self._join_all()
        else:
            tokens_invites = self._distribute()

        if self.threads == 1:
            for token, invite_codes in tokens_invites.items():
                joins, fails = self._process_token(
                    token, invite_codes, next(self.proxies_cycle)
                )
                self.total_joins += joins
                self.total_fails += fails
        else:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = []
                for token, invite_codes in tokens_invites.items():
                    futures.append(
                        executor.submit(
                            self._process_token,
                            token,
                            invite_codes,
                            next(self.proxies_cycle),
                        )
                    )

                for future in as_completed(futures):
                    try:
                        (joins, fails) = future.result()
                        self.total_joins += joins
                        self.total_fails += fails
                    except Exception as e:
                        Console.error(f"Error processing token: {e}")

        Console.information(
            "Processed all tokens.",
            f"Joins: {self.total_joins} | Fails: {self.total_fails}",
        )
        return self.total_joins, self.total_fails
