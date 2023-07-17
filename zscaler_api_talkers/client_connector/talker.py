import json
import pdb
import time
import requests
from zscaler_api_talkers.helpers.http_calls import HttpCalls
from zscaler_api_talkers.helpers.logger import setup_logger

logger = setup_logger(name=__name__)


class ClientConnectorTalker(object):
    """
    Client Connector API talker
    Documentation: under development
    Currently in beta status
    """

    def __init__(
            self,
            cloud: str,
            client_id: str = "",
            secret_key: str = "",
    ):
        """
        :param cloud: (str) Top Level Domain (TLD) of the Zscaler cloud where tenant resides.
        :param client_id: (str) Client ID
        :param secret_key: (str) Secret Key
        """
        self.base_uri = f"https://api-mobile.{cloud}/papi"
        self.hp_http = HttpCalls(
            host=self.base_uri,
            verify=True,
        )
        self.jsession_id = None
        self.version = "beta 0.1"
        self.header = {}
        if client_id and secret_key:
            self.authenticate(
                client_id=client_id,
                secret_key=secret_key,
            )

    def authenticate(
            self,
            client_id: str,
            secret_key: str,
    ):
        """
        Method to authenticate.

        :param client_id: (str) Client id
        :param secret_key: (str) Client secret, obtained from portal.
        """
        payload = {
            "apiKey": client_id,
            "secretKey": secret_key,
        }
        url = "/auth/v1/login"
        response = self.hp_http.post_call(
            url=url,
            headers={"Accept": "*/*"},
            payload=payload,
        )
        self.header = {"auth-token": response.json()["jwtToken"]}

    def _obtain_all(
            self,
            url: str,
            cookies: dict = None,
            params: dict = None,
            headers: dict = None,
    ) -> json:
        """
        Internal method that queries all pages

        :param url: (str) URL
        :param cookies: (dict?) Cookies
        :param params: (dict) Parameters to pass in request
        :param headers: (dict) Headers to pass in request

        :return: (json) JSON of results
        """
        page = 1
        result = []
        while True:
            response = self.hp_http.get_call(
                f"{url}&page={page}",
                cookies=cookies,
                params=params,
                headers=headers,
                error_handling=True,
            )
            if response.json():
                result += response.json()
                page += 1
                time.sleep(0.5)
            else:
                break

        return result

    def list_devices(
            self,
            username: str = None,
            os_type: str = None,
    ) -> json:
        """
        Gets the list of all enrolled devices of your organization and their basic details.
        :param username: (str) Username in email format
        :param os_type: (str)  1 - iOS, 2 - Android, 3 - Windows, 4 - macOS, 5 - Linux
        :return: (json) JSON of results
        """
        url = "/public/v1/getDevices?pageSize=500"
        if username:
            url +=f'&username={username}'
        if os_type:
            url +=f'&osType={os_type}'

        response = self._obtain_all(
            url=url,
            headers=self.header,
        )

        return response

    def list_otp(
            self,
            ud_id: int,
    ) -> json:
        """
        Method to fetch the One Time Password for a specific device. These passwords are unique and tied to a device
        UDID.
        :param ud_id: (int) User device ID
        :return: (json) JSON of results
        """
        url = f"/public/v1/getOtp"
        parameters = {
            "udid": ud_id,
        }
        response = self.hp_http.get_call(
            url=url,
            params=parameters,
            headers=self.header,
        )

        return response.json()

    def list_passwords(
            self,
            company_id: int,
            ud_id: int,
    ):
        """
        Method to fetch the One Time Password for a specific device. These passwords are unique and tied to a device UDID

        :param company_id: (int) ORG ID
        :param ud_id: (int) User device ID

        :return: (json) JSON of results
        """
        url = f"/public/v1/getOtp"
        parameters = {
            "companyId": company_id,
            "udid": ud_id,
        }
        response = self.hp_http.get_call(
            url=url,
            params=parameters,
            headers=self.header,
        )

        return response.json()

    def remove_devices(
            self,
            company_id: int,
            ud_ids: list,
            os_type: int = 0,
    ) -> json:
        """
        Method to  mark the device for removal (Device Removal Pending).
        API currently can remove up to 30 devices per call

        :param company_id: type int. ORG ID
        :param ud_ids: type list. List of user devices ids
        :param os_type: 0 ALL OS types, 1 IOS, 2 Android, 3 Windows, 4 macOS, 5 Linux

        :return: (json) JSON of results
        """
        url = f"/public/v1/removeDevices"
        payload = {
            "companyId": company_id,
            "udids": ud_ids,
            "osType": os_type,
        }
        response = self.hp_http.post_call(
            url=url,
            headers=self.header,
            payload=payload,
        )

        return response.json()

    def force_remove_devices(
            self,
            ud_ids: list = None,
            os_type: int = 0,
    ) -> json:
        """
        Force Remove, has the same effect as Remove, though it additionally moves the device straight to Removed and also
        signals the cloud to invalidate the user’s session.
        API currently can remove up to 30 devices per call

        :param ud_ids: (list) List of user devices ids
        :param os_type: (int) 0 ALL OS types, 1 IOS, 2 Android, 3 Windows, 4 macOS, 5 Linux

        :return: (json) JSON of results
        """
        if ud_ids is None:
            ud_ids = []
        url = f"/public/v1/forceRemoveDevices"
        payload = {
            "udids": ud_ids,
            "osType": os_type,
        }
        response = self.hp_http.post_call(
            url=url,
            headers=self.header,
            payload=payload,
        )

        return response.json()

    def list_download_service_status(
            self,
            company_id: int,
    ) -> requests.Response.content:
        """
        Method to download Service Status

        :param company_id: (int) ORG ID

        :return: (str) String of results
        """
        url = "/public/v1/downloadServiceStatus"
        parameters = {
            "companyId": company_id,
        }
        response = self.hp_http.get_call(
            url=url,
            params=parameters,
            headers=self.header,
        )

        return response.content


class ZccTalker(ClientConnectorTalker):
    def __init__(
            self,
            cloud: str,
            client_id: str = "",
            secret_key: str = "",
    ):
        logger.warning(
            "Deprecating ZccTalker. Start using ClientConnectorTalker instead."
        )
        super().__init__(
            cloud,
            client_id,
            secret_key,
        )
