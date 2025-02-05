import json, base64, regex, requests

from bs4 import BeautifulSoup
from collections import Counter

from .client import Session
from .console import Console
from .fingerprint import Fingerprint


def json_to_string(data: dict):
    return json.dumps(data, separators=(",", ":"))


def string_to_json(data: str):
    return json.loads(data)


def b64_encode(data: str | bytes) -> str:
    if type(data) == str:
        data = data.encode()
    return base64.b64encode(data).decode()


def b64_decode(data: str | bytes) -> str:
    if type(data) == bytes:
        data = data.decode()
    return base64.b64decode(data).decode()


def get_lines(file_path: str, rem_dup_lines: bool = False) -> list:
    lines = []
    with open(file_path, "rb") as f:
        for line in f.read().splitlines():
            try:
                lines.append(line.decode())
            except:
                pass
    if rem_dup_lines:
        lines = list(set(lines))
    return lines


def format_proxy(proxy: str):
    try:
        colon_splitted = proxy.split(":")
        if "@" in proxy and proxy.count(":") == 2:  # username:password@host:port
            return True, proxy
        if colon_splitted[1].isdigit():
            separator_index = proxy.index(colon_splitted[1]) + len(colon_splitted[1])
            separator = proxy[separator_index]
            if separator == "@":  # host:port@username:password
                address, credentials = proxy.split("@")
                (host, port), (username, password) = address.split(
                    ":"
                ), credentials.split(":")
            elif separator == ":":  # host:port:username:password
                host, port, username, password = proxy.split(":")
            else:
                raise ValueError("Invalid proxy format")
        elif colon_splitted[3].isdigit():  # username:password:host:port
            credentials, address = proxy.split("@")
            (username, password), (host, port) = credentials.split(":"), address.split(
                ":"
            )
        else:
            raise ValueError("Invalid proxy format")

        return True, f"{username}:{password}@{host}:{port}"
    except Exception as e:
        return False, str(e)


def between(string: str, first: str, last: str):
    return string.split(first)[1].split(last)[0]


def handle_failure(function_name: str, response, custom_reason: str = None):
    if custom_reason is None:
        if type(response) == str:
            Console.error(f"discord.{function_name}", f"Message: {response}")
        else:
            Console.error(
                f"discord.{function_name}", f"Status Code: {response.status_code}"
            )
    else:
        Console.error(f"discord.{function_name}", str(custom_reason))


def build_super_properties(fingerprint: Fingerprint):
    payload = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "has_client_mods": True,
        "browser_user_agent": fingerprint.headers["User-Agent"],
        "browser_version": fingerprint.browser_version,
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": fingerprint.build_number,
        "client_event_source": None,
    }
    return b64_encode(json_to_string(payload))


def build_ctx_properties(guild_id: str, channel_id: str, channel_type: int):
    payload = {
        "location": "Join Guild",
        "location_guild_id": str(guild_id),
        "location_channel_id": str(channel_id),
        "location_channel_type": int(channel_type),
    }
    return b64_encode(json_to_string(payload))


def get_proxy_info(proxy: str):
    try:
        response = requests.get(
            "https://ipgeo.myip.link/", proxies={"https": "http://" + proxy}, timeout=10
        )
        data = response.json()
        return True, data
    except Exception as e:
        return False, str(e)


def fetch_build_num() -> int:
    try:
        session = Session("chrome_131")
        session.session.headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Priority": "u=0, i",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        response = session.request("GET", "https://discord.com/login", headers=headers)
        cookies = response.cookies
        text = response.text

        pattern = r'"(\d{6})"'
        soup = BeautifulSoup(text, "html.parser")
        all_matches = []
        for script in soup.find_all("script"):
            src = script.get("src")
            if src is None:
                continue
            headers = {
                "Accept": "*/*",
                "Referer": "https://discord.com/login",
                "Sec-Fetch-Dest": "script",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "same-origin",
            }
            response = session.request(
                "GET", "https://discord.com" + src, headers=headers, cookies=cookies
            )
            text = response.text
            if "buildNumber" not in text:
                continue
            matches = regex.finditer(pattern, text, regex.MULTILINE)
            for _match in matches:
                for group in _match.groups():
                    number = int(group)
                    if number < 364202:
                        continue
                    all_matches.append(number)
        return Counter(all_matches).most_common(1)[0][0]
    except:
        return 364202
