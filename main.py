from copy import copy

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from tabulate import tabulate
from environs import Env
class phpMyAdminRequests:
    BASE_URL = "http://185.244.219.162"
    AUTH_URL = f"{BASE_URL}/phpmyadmin/index.php?route=/"

    def __init__(
            self,
            username=None,
            password=None,
            db_name=None,
            db_table=None,

    ):
        self._headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "User-Agent": UserAgent().random
        }

        self._session = requests.Session()
        self.token_form, self.session_form = None, None
        self.print_table = []
        self.print_table_header = []
        self.USERNAME = username
        self.PASSWORD = password
        self.DB_NAME = db_name
        self.DB_TABLE = db_table
        self.BD_ROUTE = "http://185.244.219.162/phpmyadmin/index.php?route=/sql&server=1&db={}&table={}&pos=0".format(
            self.DB_NAME, self.DB_TABLE)

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value


    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        session.headers = self.headers
        self._session = session

    def _get_auth_credential(self):
        response = self.session.get(self.AUTH_URL, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        if (a := soup.find("input", {"name": "token"})):
            self.token_form = a.get("value")

        if (a := soup.find("input", {"name": "set_session"})):
            self.session_form = a.get("value")

        if not all((self.token_form, self.session_form)):
            print("Не найдены token & set_session")
            return

        print(f"[INFO] TOKEN: {self.token_form}")
        print(f"[INFO] SESSION: {self.session_form}")
        credential_auth = {
            "pma_username": self.USERNAME,
            "pma_password": self.PASSWORD,
            "server": 1,
            "set_session": self.session_form,
            "token": self.token_form,
        }

        return credential_auth

    def login(self):
        credential_auth = self._get_auth_credential()

        response = self.session.post(self.AUTH_URL, data=credential_auth, verify=False)
        response.raise_for_status()
        print(f"[INFO] AUTH: COMPLETED!")

    def get_table(self):

        credential_get_db = {
            "route": "/sql",
            "server": 1,
            "db": self.DB_NAME,
            "table": self.DB_TABLE,
            "pos": 0
        }
        response = self.session.get(self.BD_ROUTE, data=credential_get_db, verify=False)
        response.raise_for_status()

        print(f"[INFO] BD_ROUTE: {self.BD_ROUTE} is LOAD")
        soup = BeautifulSoup(response.content, "html.parser")
        div_table = soup.find("div", {"class": "table-responsive-md"})
        tbody = div_table.table.tbody
        thead = div_table.thead

        for tr in thead.find_all("tr"):
            for th in tr.find_all("th"):
                if th.has_attr("data-column"):
                    self.print_table_header.append(th["data-column"].upper().strip())

        for tr in tbody.find_all("tr"):
            buffer = []
            for td in tr.find_all("td"):
                if td.has_attr("data-type"):
                    buffer.append(td.text.strip())

            self.print_table.append(copy(buffer))
            buffer.clear()
        print("\nВывод таблицы", self.DB_TABLE, end=":\n\n")
        print(tabulate(self.print_table, headers=self.print_table_header))

    def run(self):
        self.login()
        self.get_table()


if __name__ == '__main__':

    env = Env()
    env.read_env('.env')

    myRequest = phpMyAdminRequests(
        username=env.str("MY_ADMIN_USERNAME"),
        password=env.str("MY_ADMIN_PASSWORD"),
        db_name=env.str("MY_ADMIN_DB_NAME"),
        db_table=env.str("MY_ADMIN_DB_TABLE")
    )
    myRequest.run()


