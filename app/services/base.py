from dataclasses import dataclass, field
import random
from typing import Optional
from xml.etree import ElementTree

from requests import ConnectionError, Session
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from fastapi import HTTPException
from lxml import etree
from requests import Response, TooManyRedirects

from app.settings import settings
from app.utils.utils import trim
from app.utils.xpath import Pagination

proxies_list = [
    "45.38.101.189:6122",
    "171.22.251.78:5608",
    "107.174.25.198:5652",
    "204.217.245.199:6790",
    "104.239.104.241:6465",
    "38.170.168.136:5411",
    "149.57.17.6:5474",
    "45.92.77.125:6147",
    "46.203.196.11:5457",
    "50.114.15.6:5991",
    "38.170.168.196:5471",
    "104.239.104.224:6448",
    "145.223.44.70:5753",
    "185.198.37.175:5862",
    "148.135.148.135:6128",
    "104.252.20.230:6162",
    "64.137.73.52:5140",
    "89.213.137.32:6907",
    "108.165.69.218:6180",
    "23.129.253.41:6659",
    "92.112.228.21:6102",
    "31.59.27.118:6695",
    "148.135.254.90:6137",
    "64.137.89.4:6077",
    "92.112.228.65:6146",
    "148.135.254.220:6267",
    "31.58.18.126:6395",
    "77.81.103.165:5682",
    "89.213.188.247:6123",
    "64.137.60.240:5304",
    "104.253.91.59:6492",
    "140.99.203.237:6114",
    "216.173.122.52:5779",
    "82.23.223.164:8008",
    "104.253.91.242:6675",
    "45.83.57.54:6571",
    "45.43.82.251:6245",
    "64.137.59.45:6638",
    "92.112.170.171:6140",
    "31.58.9.182:6255",
    "155.254.39.117:6075",
    "140.99.212.87:7963",
    "185.72.241.223:7515",
    "104.252.136.24:6941",
    "23.109.208.192:6716",
    "176.113.67.241:6204",
    "64.137.14.243:5909",
    "104.252.136.160:7077",
    "107.181.132.129:6107",
    "104.249.31.124:6208",
    "92.112.200.216:6799",
    "31.223.188.44:5721",
    "104.252.20.61:5993",
    "45.141.80.64:5790",
    "45.43.70.12:6299",
    "91.123.10.208:6750",
    "45.141.81.164:6224",
    "145.223.45.134:7168",
    "23.109.219.99:6323",
    "77.81.103.35:5552",
    "31.223.189.122:6388",
    "108.165.69.2:5964",
    "45.141.80.81:5807",
    "104.239.23.37:5798",
    "84.33.224.55:6079",
    "104.249.31.160:6244",
    "185.101.252.2:7033",
    "92.112.136.131:6075",
    "64.137.96.27:6594",
    "46.203.210.58:5505",
    "46.203.202.230:6176",
    "104.253.90.158:5578",
    "45.43.191.84:6045",
    "138.128.148.228:6788",
    "31.223.188.5:5682",
    "104.239.76.65:6724",
    "31.58.24.92:6163",
    "92.112.228.67:6148",
    "64.137.96.192:6759",
    "92.112.228.89:6170",
    "91.223.126.139:6751",
    "92.112.236.12:6444",
    "23.109.208.230:6754",
    "104.249.31.127:6211",
    "38.225.2.69:5852",
    "45.43.191.139:6100",
    "140.233.166.254:7287",
    "82.22.234.31:7881",
    "185.171.254.247:6279",
    "185.101.252.54:7085",
    "45.43.185.55:6061",
    "64.137.14.202:5868",
    "45.159.53.101:7473",
    "92.112.217.83:5855",
    "38.225.15.79:5359",
    "64.137.96.217:6784",
    "45.43.191.223:6184",
    "91.223.126.75:6687",
    "104.239.76.118:6777",
    "45.150.176.193:6066"
]

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
    _session: Session = field(default=None, init=False)

    def __post_init__(self):
        self.ensure_session()

    def ensure_session(self):
        if self._session is None:
            self._session = self._create_session()

    @classmethod
    def _create_session(cls) -> Session:
        status_forcelist = [500, 502, 503, 504]
        retries = Retry(total=10, backoff_factor=0.25, status_forcelist=status_forcelist)
        session = Session()
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 "
                "Safari/537.36"
            ),
        })
        return session

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
        self.ensure_session()  # Ensure the session is created if not already

        url = self.URL if not url else url
        try:
            proxy = random.choice(proxies_list)
            proxy_url = f"http://{settings.PROXY_USERNAME}:{settings.PROXY_PASSWORD}@{proxy}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }
            print("Using proxy:", proxy_url)
            print("IP address used: ", self._session.get("http://httpbin.org/ip").json()["origin"])
            response: Response = self._session.get(
                url=url,
                proxies=proxies,
            )
        except TooManyRedirects:
            raise HTTPException(status_code=404, detail=f"Not found for url: {url}")
        except ConnectionError:
            raise HTTPException(status_code=500, detail=f"Connection error for url: {url}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error for url: {url}. {e}")
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
