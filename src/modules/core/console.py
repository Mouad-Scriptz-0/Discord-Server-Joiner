import os, threading, time

from typing import Tuple
from pystyle import Colors as Clrs, Center, Colorate
from datetime import datetime

from .config import config


lock = threading.Lock()
Clrs.bg_reset = "\033[0m"


def get_bg_color(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


def get_fg_color(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def get_colored_time(clr_one: str = Clrs.gray, clr_two: str = Clrs.light_gray) -> str:
    now = datetime.now().strftime(
        f"{clr_one}%H{clr_two}:{clr_one}%M{clr_two}:{clr_one}%S"
    )
    return now


def get_prefix(
    string: str,
    color: Tuple[int, int, int] = (255, 255, 255),
    bg_color: Tuple[int, int, int] = (128, 128, 128),
) -> str:
    time_part = (
        f" {get_colored_time()} {Clrs.dark_gray}|"
        if config["console"]["show time"]
        else ""
    )
    return (
        f"{time_part}{Clrs.reset} "
        f"{get_bg_color(*bg_color)}{get_fg_color(*color)}{string}{Clrs.bg_reset} "
        f"{Clrs.dark_gray}|{Clrs.reset}"
    )


separator = f"{Clrs.light_gray}>>{Clrs.reset}"

_replacers = {
    ":": f"{Clrs.gray}:{Clrs.reset}",
    "|": f"{Clrs.gray}|{Clrs.reset}",
}


def replace(string: str) -> str:
    for old, new in _replacers.items():
        string = string.replace(old, new)
    return string


class Console:
    @staticmethod
    def clear() -> None:
        os.system("cls")

    @staticmethod
    def input(text: str) -> str:
        prefix = get_prefix("  INPUT  ", (255, 255, 255), (26, 214, 54))
        print(f"{prefix} {text}{Clrs.reset} {Clrs.gray}>>{Clrs.reset} ", end="")
        return input()

    @staticmethod
    def adv_input(text: str, expected_type: str = "digit", config_default=None) -> str:
        value = None
        while value is None:
            value: str = Console.input(text)
            if len(value) == 0:
                if config_default:
                    value = config_default
                    break
                else:
                    Console.error("Blank input.")
                    time.sleep(2)
                    Console.clear()
                    continue

            if expected_type == "digit":
                if not value.isdigit():
                    Console.error(f"Expected: a digit, got <{value}>.")
                    time.sleep(2)
                    Console.clear()
                    continue
            if expected_type == "digit":
                value = int(value)
        return value

    @staticmethod
    def _log(
        prefix_text: str,
        text_color: Tuple[int, int, int],
        bg_color: Tuple[int, int, int],
        text: str,
        content: str,
        content_color: Tuple[int, int, int],
        custom: bool,
    ) -> None:
        if not custom:
            text = replace(text)
            content = replace(content) if content else ""

        prefix = get_prefix(prefix_text, text_color, bg_color)
        message = f"{prefix} {text}{Clrs.reset}"

        if content:
            content_clr = get_fg_color(*content_color)
            message += f" {separator} {content_clr}{content}{Clrs.reset}"

        with lock:
            print(message)

    @staticmethod
    def success(text: str, content: str = "", custom: bool = False) -> None:
        Console._log(
            "   SUC   ",
            (255, 255, 255),
            (66, 245, 111),
            text,
            content,
            (92, 255, 195),
            custom,
        )

    @staticmethod
    def captcha(text: str, content: str = "", custom: bool = False) -> None:
        Console._log(
            " CAPTCHA ",
            (255, 255, 255),
            (125, 209, 255),
            text,
            content,
            (87, 195, 255),
            custom,
        )

    @staticmethod
    def error(text: str, content: str = "", custom: bool = False) -> None:
        Console._log(
            "  ERROR  ", (180, 0, 0), (255, 0, 0), text, content, (255, 0, 0), custom
        )

    @staticmethod
    def information(text: str, content: str = "", custom: bool = False) -> None:
        Console._log(
            "  INFO   ",
            (180, 180, 0),
            (255, 255, 0),
            text,
            content,
            (255, 255, 0),
            custom,
        )

    @staticmethod
    def debug(text: str, content: str = "", custom: bool = False) -> None:
        if not config["console"]["debug"]:
            return
        Console._log(
            "   DBG   ",
            (180, 180, 0),
            (255, 255, 0),
            text,
            content,
            (255, 255, 0),
            custom,
        )

    @staticmethod
    def banner():
        print(
            Colorate.Diagonal(
                Clrs.green_to_cyan,
                Center.XCenter(
                    """   _____                             _   __                
  / ___/__  ______  ___  _____      / | / /___ _   ______ _
  \__ \/ / / / __ \/ _ \/ ___/_____/  |/ / __ \ | / / __ `/
 ___/ / /_/ / /_/ /  __/ /  /_____/ /|  / /_/ / |/ / /_/ / 
/____/\__,_/ .___/\___/_/        /_/ |_/\____/|___/\__,_/  
          /_/                                              
"""
                ),
                1,
            )
        )

    @staticmethod
    def resize(cols: int, lines: int) -> None:
        os.system(f"mode con:cols={cols} lines={lines}")

    @staticmethod
    def sub_banner(text: str):
        print(Colorate.DiagonalBackwards(Clrs.cyan_to_green, Center.XCenter(text)))
        print()
