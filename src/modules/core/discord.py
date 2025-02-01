import time

from .client import Session
from .utilities import build_super_properties
from .fingerprint import Fingerprint


def get_nonce():
    str((int(time.time() * 1000) * 1000 - 1420070400000) * 4194304)


class Discord:
    def __init__(self, token: str, fingerprint: Fingerprint, proxy: str | None = None):
        self.fingerprint = fingerprint
        self.fingerprint.super_properties = build_super_properties(self.fingerprint)

        self.session = Session(self.fingerprint.client_identifier, proxy)

        self.cookies = {}
        self.token = token

    def request(self, method: str, url: str, **args):
        try:
            return self.session.request(method, url, **args)
        except Exception as e:
            raise Exception(f"Failed to send request. ({e})")

    def index(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": self.fingerprint.headers["Accept-Language"],
            "Priority": "u=0, i",
            "Sec-Ch-Ua": self.fingerprint.headers["Sec-Ch-Ua"],
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.fingerprint.headers["User-Agent"],
        }
        try:
            response = self.request(
                "GET", "https://discord.com/channels/@me", headers=headers
            )
        except Exception as e:
            return False, e
        self.cookies = response.cookies
        return True, response

    def get_server_info(self, invite_code: str):
        headers = {
            "Accept": "*/*",
            "Accept-Language": self.fingerprint.headers["Accept-Language"],
            "Authorization": self.token,
            "Priority": "u=1, i",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Ch-Ua": self.fingerprint.headers["Sec-Ch-Ua"],
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.fingerprint.headers["User-Agent"],
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": self.fingerprint.timezone,
            "X-Super-Properties": self.fingerprint.super_properties,
        }
        params = {
            "inputValue": invite_code,
            "with_counts": "true",
            "with_expiration": "true",
            "with_permissions": "false",
        }
        try:
            response = self.request(
                "GET",
                f"https://discord.com/api/v9/invites/{invite_code}",
                params=params,
                headers=headers,
                cookies=self.cookies,
            )
        except Exception as e:
            return False, e
        return True, response

    def join_server(
        self,
        sess_id: str,
        ctx_properties: dict,
        invite_code: str,
        captcha_key: str = None,
        captcha_rqtoken: str = None,
    ):
        headers = {
            "Accept": "*/*",
            "Accept-Language": self.fingerprint.headers["Accept-Language"],
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Origin": "https://discord.com",
            "Priority": "u=1, i",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Ch-Ua": self.fingerprint.headers["Sec-Ch-Ua"],
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.fingerprint.headers["User-Agent"],
            "X-Context-Properties": ctx_properties,
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": self.fingerprint.timezone,
            "X-Super-Properties": self.fingerprint.super_properties,
        }
        if captcha_key is not None:
            headers["X-Captcha-Key"] = captcha_key
            headers["X-Captcha-Rqtoken"] = captcha_rqtoken
        payload = {"session_id": sess_id}
        try:
            response = self.request(
                "POST",
                f"https://discord.com/api/v9/invites/{invite_code}",
                headers=headers,
                json=payload,
                cookies=self.cookies,
            )
        except Exception as e:
            return False, e
        return True, response
