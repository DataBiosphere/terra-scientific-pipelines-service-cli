"""
Custom local HTTP server logic used for OAuth2 flow
"""

from http.server import HTTPServer
from typing import Optional
from urllib.parse import parse_qs

from oauth2_cli_auth.http_server import OAuthRedirectHandler
from oauth2_cli_auth._timeout import TimeoutException, _method_with_timeout


class CustomOAuthRedirectHandler(OAuthRedirectHandler):
    """
    HTTPRequest Handler that is intended to be used as oauth2 callback page.
    Customized for terralab to receive and parse a POST request from the redirect.
    """

    def do_GET(self):
        """For security reasons, we don't ever want to process a GET request."""
        return NotImplementedError("GET request not supported for authentication flow.")

    def do_POST(self) -> None:
        ctype = self.headers.get("Content-Type")
        if ctype == "application/x-www-form-urlencoded":
            length = int(self.headers.get("Content-Length"))
            raw_data = self.rfile.read(length)
            params = parse_qs(raw_data.decode(encoding="utf_8"))
        else:
            params = {}

        has_error = (
            "code" not in params
            or len(params["code"]) != 1
            or params["code"][0].strip() == ""
        )

        if has_error:
            self.send_response(400)
            self._serve_callback_page(
                title="Oh snap!",
                message="Something went wrong trying to authenticate you. Please try going back in your browser, or restart the auth process.",
                has_error=True,
            )
        else:
            self.send_response(200)
            self.server._code = params["code"][0]
            self._serve_callback_page(
                title="Success",
                message="You have been authenticated successfully. You may close this browser window now and go back to the terminal",
                has_error=False,
            )


class CustomOAuthCallbackHttpServer(HTTPServer):
    """
    Simplistic HTTP Server to provide local callback URL for oauth2 provider.
    Same as the OAuthCallbackHttpServer from oauth2_cli_auth, except uses our CustomOAuthRedirectHandler.
    """

    def __init__(self, port):
        super().__init__(("", port), CustomOAuthRedirectHandler)

        self._code: str | None = None

    def get_code(self) -> str | None:
        """
        This method should only be called after the request was done and might be None when no token is given.

        :return: Authorization code or None if the request was not performed yet
        """
        return self._code

    @property
    def callback_url(self) -> str:
        """
        Callback URL for the HTTP-Server
        """
        return f"http://localhost:{self.server_port}"

    def wait_for_code(self, attempts: int = 3, timeout_per_attempt=10) -> Optional[str]:
        """
        Wait for the server to open the callback page containing the code query parameter.

        It tries for #attempts with a timeout of #timeout_per_attempts for each attempt.
        This prevents the CLI from getting stuck by unsolved callback URls

        :param attempts: Amount of attempts
        :param timeout_per_attempt: Timeout for each attempt to be successful
        :return: Code from callback page or None if the callback page is not called successfully
        """
        for _ in range(0, attempts):
            try:
                _method_with_timeout(
                    self.handle_request, timeout_seconds=timeout_per_attempt
                )
            except TimeoutException:
                continue
            if self.get_code() is not None:
                return self.get_code()

        return None
