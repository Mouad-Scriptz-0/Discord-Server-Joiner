import requests, time

from .config import config


class Solver:
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.service = config["captcha"]["service"]
        self.api_key = config["captcha"]["api key"]

    def solve(
        self, site_key: str, page_url: str = None, rqdata: str = None, proxy: str = None
    ):
        if "razorcap" in self.service.lower():
            return self.razorcap(site_key, rqdata, proxy)
        elif "24cap" in self.service.lower():
            return self.captcha24(site_key, page_url, rqdata, proxy)

    def razorcap(self, site_key: str, rqdata: str = None, proxy: str = None):
        # Creating a task
        payload = {
            "key": self.api_key,
            "type": "enterprise" if rqdata is not None else "hcaptcha_basic",
            "data": {
                "sitekey": site_key,
                "siteurl": "discord.com",
                "proxy": f"http://{proxy or self.proxy}",
                "rqdata": rqdata,
            },
        }
        try:
            response = requests.post(
                "https://api.razorcap.xyz/create_task", json=payload
            )
        except Exception as e:
            return False, f"Failed to create a task. ({e})"
        task_id = None
        try:
            data = response.json()
            task_id = data.get("task_id")
        except:
            return False, f"Failed to fetch task id (1). ({response.text})"
        if task_id is None:
            return False, f"Failed to fetch task id (2). ({response.text})"

        # Waiting for task to be solved
        while True:
            try:
                response = requests.get(
                    f"https://api.razorcap.xyz/get_result/{task_id}"
                )
            except Exception as e:
                return False, f"Failed to fetch task result (1). ({e})"
            try:
                data = response.json()
                status = data.get("status")
            except:
                return False, f"Failed to fetch task result (2). ({response.text})"
            if status == "solved":
                return True, data["response_key"]
            elif status != "solving":
                return False, f"Failed to solve. ({response.text})"
            time.sleep(0.5)

    def captcha24(
        self,
        site_key: str,
        page_url: str = "https://discord.com/channels/@me",
        rqdata: str = None,
        proxy: str = None,
    ):
        # Creating a task
        payload = {
            "key": self.api_key,
            "sitekey": site_key,
            "pageurl": page_url,
            "json": 0,
            "method": "hcaptcha",
            "proxy": proxy or self.proxy,
            "proxytype": "HTTPS",
            "rqdata": rqdata,
            "enterprise": True,
        }
        try:
            response = requests.post("https://24captcha.online/in.php", json=payload)
        except Exception as e:
            return False, f"Failed to create a task. ({e})"
        task_id = None
        try:
            task_id = response.text.split("|")[1]
        except:
            return False, f"Failed to fetch task id (1). ({response.text})"
        if task_id is None:
            return False, f"Failed to fetch task id (2). ({response.text})"

        # Waiting for task to be solved
        payload = {"key": self.api_key, "id": task_id, "action": "get", "json": 0}
        while True:
            try:
                response = requests.get(
                    "https://24captcha.online/res.php", json=payload
                )
            except Exception as e:
                return False, f"Failed to fetch task result (1). ({e})"
            text = response.text
            if text.startswith("OK"):
                return True, text.split("|")[1]
            elif text == "ERROR_CAPTCHA_UNSOLVABLE":
                return False, "Failed to solve. (ERROR_CAPTCHA_UNSOLVABLE)"
            elif text != "CAPCHA_NOT_READY":
                return False, f"Failed to solve (2). ({response.text})"
            time.sleep(2)
