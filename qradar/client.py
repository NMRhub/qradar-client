class QRadarError(Exception):
    """Raised when QRadar responds with something other than the expected
    JSON payload, e.g. an authentication failure or a bad request."""


class QRadar:
    def __init__(self, base_url, key, version, transport, verify=True):
        self.base_url = base_url
        self.key = key
        self.version = version
        self.transport = transport
        transport.verify = verify

        endpoints = self.api_endpoint_factory("GET", "/help/endpoints")(
            filter=f"version={version}",
            fields="http_method, path"
        )
        if not isinstance(endpoints, list):
            raise QRadarError(
                f"Expected a list of endpoints from /help/endpoints, got: {endpoints!r}"
            )

        self.__dict__.update({
            f"""{(method:=endpoint.get("http_method").lower())}{(path:=endpoint.get("path"))
            .translate({ord('{'): None, ord('}'): None, ord('/'): ord('_'), ord('-'): ord('_')})}""": self.api_endpoint_factory(
                method.upper(), path
            )
            for endpoint in endpoints
        })

    def api_endpoint_factory(self, method, url):
        def call(json=None, **params):
            response = self.transport.request(
                method, f"{self.base_url}/api{url}".format(**params),
                params=params, json=json,
                headers={"Accept": "application/json", "Version": self.version, "SEC": self.key}
            )
            if response.status_code >= 400:
                raise QRadarError(
                    f"{method} {url} failed with HTTP {response.status_code}: {response.text[:500]}"
                )
            return response.json()
        return call
