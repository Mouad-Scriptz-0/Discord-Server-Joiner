import time

from modules.core.console import Console
from modules.core.utilities import fetch_build_num

from modules.joiner import Joiner


def menu():
    Console.clear()
    # Console.resize(100, 30)
    Console.banner()
    Console.sub_banner("Server Joiner | .gg/5UzK26afzv")
    text = """ - 1 | Joiner -
- 2 | Exit   -
"""
    Console.sub_banner(text)

    option: str = Console.input("Option")

    if not option.isdigit() or option not in ["1", "2"]:
        Console.error(f"Available options: 1 | 2")
        time.sleep(2)
        menu()

    option = int(option)

    Console.clear()

    match option:
        case 2:
            Console.information("Quitting in 2 seconds...")
            time.sleep(2)
            exit()
        case 1:
            Console.information("Fetching build number...")
            build_number = fetch_build_num()
            Console.information("Fetched build number.", str(build_number))
            joiner = Joiner(build_number)
            joiner.run()


if __name__ == "__main__":
    menu()
