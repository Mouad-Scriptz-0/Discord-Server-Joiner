import primp


class Session:
    def __init__(
        self, client_id: str = "chrome_132", proxy: str = None, timeout: int = 120
    ):
        if proxy is not None:
            proxy = "http://" + proxy

        self.session = primp.Client(
            timeout=timeout,
            cookie_store=False,
            proxy=proxy,
            impersonate=client_id,
            follow_redirects=False,
        )

    def request(self, method: str, url: str, **args):
        return self.session.request(method, url, **args)
