import os
import random
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Set
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from lxml import etree
from requests import Response, TooManyRedirects

from app.settings import settings
from app.utils.utils import trim
from app.utils.xpath import Pagination

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 "
    "Safari/537.36"
)

# Transfermarkt sits behind CloudFront, which issues a verdict per source IP:
# a clean IP reaches the origin (200 from nginx), a flagged one gets 202 with an
# empty body, and a hard-banned one gets 403. The verdict is stable per IP and
# does not respond to pacing or backoff, so the only workable strategy is to
# send each request from an IP that is currently clean.
#
# The pool is supplied by the caller via PROXY_POOL ("ip:port,ip:port,...")
# rather than hardcoded here, for two reasons: the provider rotates roughly a
# third of its IPs a year, and only the caller knows which of its proxies are
# sticky IPs reserved for per-customer provider credentials and so must never be
# spent on scraping. With PROXY_POOL unset every request goes out directly,
# which keeps local development working unchanged.
MAX_PROXY_ATTEMPTS = 6

# A 404 is a real answer about a real player rather than evidence of a blocked
# IP, so it is raised to the caller immediately instead of being retried across
# the whole pool.
#
# 405 looks like a route problem but is not: the same URL returns 200 through
# most proxies and 405 through a few, so it is IP-dependent and belongs here.
BLOCKED_STATUSES = frozenset({202, 403, 405, 429})

_proxy_lock = threading.Lock()
_demoted_proxies: Set[str] = set()


def _proxy_setting(name: str) -> str:
    """Read a proxy setting, preferring the live environment over `settings`.

    `settings` is instantiated at import time. The caller builds the pool at
    runtime (it has to query its proxy provider first), which can happen after
    this module was imported, so the frozen value would be stale or empty.
    """
    return os.environ.get(name) or getattr(settings, name, "") or ""


def proxy_pool() -> List[str]:
    return [p.strip() for p in _proxy_setting("PROXY_POOL").split(",") if p.strip()]


def _pick_proxy(pool: List[str]) -> str:
    """Choose a proxy that has not yet been seen to fail."""
    with _proxy_lock:
        usable = [p for p in pool if p not in _demoted_proxies]
        if not usable:
            # Every proxy has failed at least once. Verdicts drift and these
            # demotions may be stale, so forget them rather than give up.
            _demoted_proxies.clear()
            usable = list(pool)
    return random.choice(usable)


def _demote_proxy(proxy: str) -> None:
    with _proxy_lock:
        _demoted_proxies.add(proxy)


def _proxies_for(proxy: str) -> dict:
    user = _proxy_setting("PROXY_USERNAME")
    password = _proxy_setting("PROXY_PASSWORD")
    url = f"http://{user}:{password}@{proxy}"
    return {"http": url, "https": url}


@dataclass
class TransfermarktBase:
    """
    Base class for making HTTP requests to Transfermarkt and extracting data from the web pages.

    Args:
        URL (str): The URL for the web page to be fetched.
    Attributes:
        page (ElementTree): The parsed web page content.
        response (dict): A dictionary to store the response data.
    """

    URL: str
    page: ElementTree = field(default_factory=lambda: None, init=False)
    response: dict = field(default_factory=lambda: {}, init=False)

    def make_request(self, url: Optional[str] = None) -> Response:
        """
        Make an HTTP GET request to the specified URL.

        Args:
            url (str, optional): The URL to make the request to. If not provided, the class's URL
                attribute will be used.

        Returns:
            Response: An HTTP Response object containing the server's response to the request.

        Raises:
            HTTPException: If there are too many redirects, or if the server returns a client or
                server error status code.
        """
        url = self.URL if not url else url
        pool = proxy_pool()
        if not pool:
            return self._raise_for_status(self._get(url), url)

        # Rotate over the pool: a blocked IP is a property of the IP, so the same
        # request from a different one usually succeeds.
        last_error: Optional[HTTPException] = None
        for _ in range(min(MAX_PROXY_ATTEMPTS, len(pool))):
            proxy = _pick_proxy(pool)
            try:
                response = self._get(url, proxies=_proxies_for(proxy))
            except HTTPException as e:
                # Could not reach Transfermarkt through this proxy at all
                # (dead proxy, timeout). Try the next one.
                _demote_proxy(proxy)
                last_error = e
                continue
            if response.status_code in BLOCKED_STATUSES:
                _demote_proxy(proxy)
                last_error = HTTPException(
                    status_code=response.status_code,
                    detail=(
                        f"Blocked by Transfermarkt ({response.status_code}) for url: {url}"
                    ),
                )
                continue
            return self._raise_for_status(response, url)

        raise last_error or HTTPException(
            status_code=502, detail=f"No usable proxy for url: {url}"
        )

    @staticmethod
    def _get(url: str, proxies: Optional[dict] = None) -> Response:
        try:
            return requests.get(
                url=url,
                headers={"User-Agent": USER_AGENT},
                proxies=proxies,
                timeout=30,
            )
        except TooManyRedirects:
            raise HTTPException(status_code=404, detail=f"Not found for url: {url}")
        except ConnectionError:
            raise HTTPException(status_code=500, detail=f"Connection error for url: {url}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error for url: {url}. {e}")

    @staticmethod
    def _raise_for_status(response: Response, url: str) -> Response:
        if 400 <= response.status_code < 500:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Client Error. {response.reason} for url: {url}",
            )
        elif 500 <= response.status_code < 600:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Server Error. {response.reason} for url: {url}",
            )
        return response

    def request_url_bsoup(self) -> BeautifulSoup:
        """
        Fetch the web page content and parse it using BeautifulSoup.

        Returns:
            BeautifulSoup: A BeautifulSoup object representing the parsed web page content.

        Raises:
            HTTPException: If there are too many redirects, or if the server returns a client or
                server error status code.
        """
        response: Response = self.make_request()
        return BeautifulSoup(markup=response.content, features="html.parser")

    @staticmethod
    def convert_bsoup_to_page(bsoup: BeautifulSoup) -> ElementTree:
        """
        Convert a BeautifulSoup object to an ElementTree.

        Args:
            bsoup (BeautifulSoup): The BeautifulSoup object representing the parsed web page content.

        Returns:
            ElementTree: An ElementTree representing the parsed web page content for further processing.
        """
        return etree.HTML(str(bsoup))

    def request_url_page(self) -> ElementTree:
        """
        Fetch the web page content, parse it using BeautifulSoup, and convert it to an ElementTree.

        Returns:
            ElementTree: An ElementTree representing the parsed web page content for further
                processing.

        Raises:
            HTTPException: If there are too many redirects, or if the server returns a client or
                server error status code.
        """
        bsoup: BeautifulSoup = self.request_url_bsoup()
        return self.convert_bsoup_to_page(bsoup=bsoup)

    def raise_exception_if_not_found(self, xpath: str):
        """
        Raise an exception if the specified XPath does not yield any results on the web page.

        Args:
            xpath (str): The XPath expression to query elements on the page.

        Raises:
            HTTPException: If the specified XPath query does not yield any results, indicating an invalid request.
        """
        if not self.get_text_by_xpath(xpath):
            raise HTTPException(status_code=404, detail=f"Invalid request (url: {self.URL})")

    def get_list_by_xpath(self, xpath: str, remove_empty: Optional[bool] = True) -> Optional[list]:
        """
        Extract a list of elements from the web page using the specified XPath expression.

        Args:
            xpath (str): The XPath expression to query elements on the page.
            remove_empty (bool, optional): If True, remove empty or whitespace-only elements from
                the list. Default is True.

        Returns:
            Optional[list]: A list of elements extracted from the web page based on the XPath query.
                If remove_empty is True, empty or whitespace-only elements are filtered out.
        """
        elements: list = self.page.xpath(xpath)
        if remove_empty:
            elements_valid: list = [trim(e) for e in elements if trim(e)]
        else:
            elements_valid: list = [trim(e) for e in elements]
        return elements_valid or []

    def get_text_by_xpath(
        self,
        xpath: str,
        pos: int = 0,
        iloc: Optional[int] = None,
        iloc_from: Optional[int] = None,
        iloc_to: Optional[int] = None,
        join_str: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extract text content from the web page using the specified XPath expression.

        Args:
            xpath (str): The XPath expression to query elements on the page.
            pos (int, optional): Index of the element to extract if multiple elements match the
                XPath. Default is 0.
            iloc (int, optional): Extract a single element by index, used as an alternative to 'pos'.
            iloc_from (int, optional): Extract a range of elements starting from the specified
                index (inclusive).
            iloc_to (int, optional): Extract a range of elements up to the specified
                index (exclusive).
            join_str (str, optional): If provided, join multiple text elements into a single string
                using this separator.

        Returns:
            Optional[str]: The extracted text content from the web page based on the XPath query and
                optional parameters. If no matching element is found, None is returned.
        """
        element = self.page.xpath(xpath)

        if not element:
            return None

        if isinstance(element, list):
            element = [trim(e) for e in element if trim(e)]

        if isinstance(iloc, int):
            element = element[iloc]

        if isinstance(iloc_from, int) and isinstance(iloc_to, int):
            element = element[iloc_from:iloc_to]

        if isinstance(iloc_to, int):
            element = element[:iloc_to]

        if isinstance(iloc_from, int):
            element = element[iloc_from:]

        if isinstance(join_str, str):
            return join_str.join([trim(e) for e in element])

        try:
            return trim(element[pos])
        except IndexError:
            return None

    def get_last_page_number(self, xpath_base: str = "") -> int:
        """
        Retrieve the last page number for a paginated result based on the provided base XPath.

        Args:
            xpath_base (str): The base XPath for extracting page number information.

        Returns:
            int: The last page number for search results. Returns 1 if no page numbers are found.
        """

        for xpath in [Pagination.PAGE_NUMBER_LAST, Pagination.PAGE_NUMBER_ACTIVE]:
            url_page = self.get_text_by_xpath(xpath_base + xpath)
            if url_page:
                return int(url_page.split("=")[-1].split("/")[-1])
        return 1
