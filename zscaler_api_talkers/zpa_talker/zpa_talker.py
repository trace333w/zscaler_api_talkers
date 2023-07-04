import json

import requests
from zscaler_api_talkers.zscaler_helpers import HttpCalls


class ZpaTalker(object):
    """
    ZPA API talker
    Documentation: https://help.zscaler.com/zpa/zpa-api/api-developer-reference-guide
    """

    def __init__(
        self,
        customerID: int,
        cloud: str = "https://config.private.zscaler.com",
        client_id: str = None,
        client_secret: str = "",
    ):
        """
        :param cloud: (str) Example https://config.zpabeta.net
        :param customerID: (int) The unique identifier of the ZPA tenant
        :param client_id: (str)
        :param client_secret: (str)
        """
        self.base_uri = cloud
        # self.base_uri = f'https://config.zpabeta.net'
        self.hp_http = HttpCalls(
            host=self.base_uri,
            verify=True,
        )
        self.jsessionid = None
        self.version = "1.3"
        self.header = None
        self.customerId = customerID
        if client_id and client_secret:
            self.authenticate(
                client_id=client_id,
                client_secret=client_secret,
            )

    def _obtain_all_results(
        self,
        url: str,
    ) -> list:
        """
        API response can have multiple pages. This method return the whole response in a list

        :param url: (str) url

        :return: (list)
        """
        result = []
        if "?pagesize" not in url:
            url = f"{url}?pagesize=500"
        response = self.hp_http.get_call(
            url,
            headers=self.header,
            error_handling=True,
        )
        if "list" not in response.json().keys():
            return []
        if int(response.json()["totalPages"]) > 1:
            i = 0
            while i <= int(response.json()["totalPages"]):
                result = (
                    result
                    + self.hp_http.get_call(
                        f"{url}&page={i}",
                        headers=self.header,
                        error_handling=True,
                    ).json()["list"]
                )
                i += 1
        else:
            result = response.json()["list"]

        return result

    def authenticate(
        self,
        client_id: str,
        client_secret: str,
    ) -> json:
        """
        Method to obtain the Bearer Token. Refer to https://help.zscaler.com/zpa/adding-api-keys
        :param client_id: (str) client id
        :param client_secret. (str) client secret

        return (json))
        """
        url = f"/signin"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
        }
        response = self.hp_http.post_call(
            url,
            headers=headers,
            error_handling=True,
            payload=payload,
            urlencoded=True,
        )
        self.header = {
            "Authorization": f"{response.json()['token_type']} {response.json()['access_token']}"
        }

        return response.json()

    # app-server-controller

    def list_servers(
        self,
        query: str = False,
        serverId: int = None,
    ) -> json:
        """
        Method to obtain all the configured Servers.

        :param query: (str) Example ?page=1&pagesize=20&search=consequat
        :param serverId: (int) Unique server id number

        :return: (json)
        """
        if serverId:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/server/{serverId}"
        else:
            if not query:
                query = "?pagesize=500"
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/server{query}"
        response = self.hp_http.get_call(
            url,
            headers=self.header,
            error_handling=True,
        )

        return response.json()

    # application-controller
    def list_application_segments(
        self,
        applicationId: int = None,
    ) -> json or list:
        """
        Method to obtain application segments

        :param applicationId: (int) Application unique identified id

        :return: (json|list)
        """
        if applicationId:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/application/{applicationId}"
            response = self.hp_http.get_call(
                url,
                headers=self.header,
                error_handling=True,
            )
            return response.json()
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/application"
        response = self._obtain_all_results(url)

        return response

    def add_application_segment(
        self,
        name: str,
        healthReporting: str,
        domainNames: list,
        segmentGroupId: str,
        serverGroups: list,
        commonAppsDto: list = [],
        segmentGroupName: str = "",
        healthCheckType: str = "DEFAULT",
        clientlessApps: list = [],
        inspectionApps: list = [],
        sraApps: list = [],
        tcpPortRange: dict = {},
        tcpPortRanges: list = [],
        udpPortRanges: list = [],
        udpPortRange: dict = {},
        description: str = "",
        enabled: bool = True,
        icmpAccessType: str = "NONE",
        ipAnchored: bool = False,
        doubleEncrypt: bool = False,
        bypassType: str = "NEVER",
        isCnameEnabled: bool = True,
        selectConnectorCloseToApp: bool = False,
        passiveHealthEnabled: bool = True,
    ) -> json:
        """
        Adds a new Application Segment for a ZPA tenant.
        :param name: (str) App Name
        :param healthReporting: (str) possible values: NONE, ON_ACCESS, CONTINUOUS
        :param domainNames: (list) List of domains or IP addresses
        :param segmentGroupId: (str) Application Segment Group id
        :param serverGroups=(list) List of dictionaries, where key is id and value is serverGroupId [
        {"id": "<serverGroupId>"}
        ]
        :param commonAppsDto: (list) List of dictionaries, where appsConfig will list the apps with Browser Access
        or Inspection
        :param segmentGroupName: (str) Application Segment Group Name
        :param healthCheckType: (str)
        :param clientlessApps: (list) List of application domains in Application Segment with Browser access enabled
        :param inspectionApps: (list) List of application domains in Application Segment with Inspection enabled
        :param sraApps: (list) List of application domains in Application Segment with Privileged Remote Access enabled
        :param tcpPortRange: type dict.  [{"from":int, "to":int}]
        :param tcpPortRanges: (list)  ["from", "to"]. This will be deprecated in the future.
        :param udpPortRange: type dict.  [{"from":int, "to":int}]
        :param udpPortRanges: (list)  ["from", "to"]. This will be deprecated in the future.
        :param description: (str) Description
        :param enabled: (bool) (True|False)
        :param icmpAccessType: (str) possible values: PING_TRACEROUTING, PING, NONE
        :param ipAnchored: (bool) (True|False)
        :param doubleEncrypt: (bool) (True|False)
        :param bypassType: (str) possible values ALWAYS, NEVER, ON_NET
        :param isCnameEnabled: (bool) (True|False)
        :param selectConnectorCloseToApp: (bool) (True|False)
        :param passiveHealthEnabled: (bool) (True|False)

        :return: (json)
        """

        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/application"
        payload = {
            "name": name,
            "description": description,
            "enabled": enabled,
            "healthCheckType": healthCheckType,
            "healthReporting": healthReporting,
            "icmpAccessType": icmpAccessType,
            "ipAnchored": ipAnchored,
            "doubleEncrypt": doubleEncrypt,
            "bypassType": bypassType,
            "isCnameEnabled": isCnameEnabled,
            "clientlessApps": clientlessApps,
            "inspectionApps": inspectionApps,
            "sraApps": sraApps,
            "commonAppsDto": commonAppsDto,
            "selectConnectorCloseToApp": selectConnectorCloseToApp,
            "passiveHealthEnabled": passiveHealthEnabled,
            "tcpPortRanges": tcpPortRanges,
            "tcpPortRange": tcpPortRange,
            "udpPortRange": udpPortRange,
            "udpPortRanges": udpPortRanges,
            "domainNames": domainNames,
            "segmentGroupId": segmentGroupId,
            "segmentGroupName": segmentGroupName,
            "serverGroups": serverGroups,
        }
        response = self.hp_http.post_call(
            url=url,
            payload=payload,
            headers=self.header,
            error_handling=True,
        )

        return response.json()

    def update_application_segment(
        self,
        applicationId: int,
        payload: dict,
    ) -> requests.Response:
        """
        Updates the Application Segment details for the specified ID

        :param applicationId: (int) Application ID
        :param payload: (dict)

        :return: (requests.Response Object)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/application/{applicationId}"
        response = self.hp_http.put_call(
            url=url,
            payload=payload,
            headers=self.header,
            error_handling=True,
        )

        return response

    def delete_application_segment(
        self,
        applicationId: int,
    ) -> requests.Response:
        """
        Updates the Application Segment details for the specified ID

        :param applicationId: (int) Application ID

        :return: (requests.Response Object)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/application/{applicationId}"
        response = self.hp_http.delete_call(
            url=url,
            error_handling=True,
        )

        return response

    # segment-group-controller

    def list_segment_group(
        self,
        segmentGroupId: int = None,
        query: str = False,
    ) -> json or list:
        """
        Get all the configured Segment Groups. If segmentGroupId obtains the segment sroup details

        :param segmentGroupId: (int) The unique identifier of the Segment Group.
        :param query: (str) Example ?page=1&pagesize=20&search=consequat

        return (json|list)
        """
        if segmentGroupId:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/segmentGroup/{segmentGroupId}"
            response = self.hp_http.get_call(
                url, headers=self.header, error_handling=True
            ).json()
        else:
            if not query:
                query = "?pagesize=500"
            url = (
                f"/mgmtconfig/v1/admin/customers/{self.customerId}/segmentGroup{query}"
            )
            response = self._obtain_all_results(url)

        return response

    def add_segment_group(
        self,
        name: str,
        description: str,
        enabled: bool = True,
    ) -> json:
        """
        Add a new segment group

        :param name: (str) Name of segment Group
        :param description: (str) Description
        :param enabled: (bool): True or False
        :return: (json)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/segmentGroup"
        payload = {
            "name": name,
            "description": description,
            "enabled": enabled,
        }
        response = self.hp_http.post_call(
            url,
            headers=self.header,
            error_handling=True,
            payload=payload,
        )

        return response.json()

    # connector-controller
    def list_connector(
        self,
        connectorId: int = None,
    ) -> json or list:
        """
        Get all the configured Segment Groups. If segmentGroupId obtains the segment group details

        :param connectorId: The unique identifier of the App Connector.

        return (json|list)
        """
        if connectorId:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/connector/{connectorId}"
            return self.hp_http.get_call(
                url,
                headers=self.header,
                error_handling=True,
            ).json()
        else:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/connector"
        response = self._obtain_all_results(url)

        return response

    def delete_bulk_connector(
        self,
        ids: list,
    ) -> json:
        """
        Get all the configured Segment Groups. If segmentGroupId obtains the segment sroup details

        :param ids: (list) list of resources ids for bulk deleting the App Connectors.

        return (json)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/connector/bulkDelete"
        payload = {"ids": ids}
        response = self.hp_http.post_call(
            url=url,
            headers=self.header,
            error_handling=True,
            payload=payload,
        )

        return response.json()

    # Connector-group-controller
    def list_connector_group(
        self,
        appConnectorGroupId: int = None,
    ) -> json or list:
        """
        Gets all configured App Connector Groups for a ZPA tenant.

        :param appConnectorGroupId: (int) The unique identifier of the Connector Group.

        return (json|list)
        """
        if appConnectorGroupId:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/appConnectorGroup/{appConnectorGroupId}"
            return self.hp_http.get_call(
                url,
                headers=self.header,
                error_handling=True,
            ).json()
        else:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/appConnectorGroup"
            response = self._obtain_all_results(url)

        return response

    # ba-certificate-controller-v-2

    def list_browser_access_certificates(
        self,
    ) -> list:  # FIXME: duplicate but URL is slightly different.
        """
        Get all Browser issued certificates

        :return: (list)
        """
        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/clientlessCertificate/issued"
        response = self._obtain_all_results(url)

        return response

    # enrollment-cert-controller

    def list_enrollment_certificates(self) -> list:
        """
        Get all the Enrollment certificates

        :return: (list)
        """
        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/enrollmentCert"
        response = self._obtain_all_results(url)

        return response

    def list_browser_access_certificates(
        self,
    ) -> list:  # FIXME: duplicate but URL is slightly different.
        """
        Get all the issued certificates

        :return: (list)
        """
        url = (
            f"/mgmtconfig/v1/admin/customers/{self.customerId}/visible/versionProfiles"
        )
        response = self._obtain_all_results(url)

        return response

    # customer-version-profile-controller

    def list_customer_version_profile(
        self,
        query: str = False,
    ) -> json:
        """
        Get Version Profiles visible to a customer

        :param query: (str) Example ?page=1&pagesize=20&search=consequat

        :return: (json)
        """
        if not query:
            query = "?pagesize=500"
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/visible/versionProfiles{query}"
        response = self.hp_http.get_call(
            url,
            headers=self.header,
            error_handling=True,
        )

        return response.json()

    # cloud - connector - group - controller
    def list_cloud_connector_group(
        self,
        id: int = None,
        query: str = False,
    ) -> json:
        """
        Get all configured Cloud Connector Groups. If id, Get the Cloud Connector Group details

        :param id: (int)
        :param query: (str) Example ?page=1&pagesize=20&search=consequat

        :return: (json)
        """
        if id:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/cloudConnectorGroup/{id}"
        else:
            if not query:
                query = "?pagesize=500"
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/cloudConnectorGroup{query}"
        response = self.hp_http.get_call(
            url,
            headers=self.header,
            error_handling=True,
        )

        return response.json()

    # idp-controller-v-2
    def list_idP(
        self,
        query: str = False,
    ) -> list:
        """
        Method to Get all the idP details for a ZPA tenant

        :param query: (str) HTTP query

        :return: (list)
        """
        if not query:
            query = "?pagesize=500"
        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/idp{query}"
        response = self._obtain_all_results(url)

        return response

    # provisioningKey-controller
    def list_provisioningKey(
        self,
        associationType: str = "CONNECTOR_GRP",
    ) -> list:
        """
        Gets details of all the configured provisioning keys.

        :param associationType: (str) The supported values are CONNECTOR_GRP and SERVICE_EDGE_GRP.

        :return: (list)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/associationType/{associationType}/provisioningKey"
        response = self._obtain_all_results(url)

        return response

    # policy-set-controller

    # scim-attribute-header-controller

    def list_scim_attributes(
        self,
        idpId: int,
        query: str = False,
    ) -> json:
        """
        :param idpId: (int) The unique identifies of the Idp
        :param query: (str) ?page=1&pagesize=20&search=consequat

        :return: (json)
        """
        if not query:
            query = "?pagesize=500"
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/idp/{idpId}/scimattribute{query}"
        response = self.hp_http.get_call(
            url,
            headers=self.header,
            error_handling=True,
        )

        return response.json()

    # scim-group-controller
    def list_scim_groups(
        self,
        idpId: int,
        query: str = False,
    ) -> list:
        """
        Method to list all SCIM groups

        :param idpId: (int) The unique identifies of the Idp
        :param query: (str) ?page=1&pagesize=20&search=consequat

        :return: (list)
        """
        if not query:
            query = "?pagesize=500"
        url = (
            f"/userconfig/v1/customers/{self.customerId}/scimgroup/idpId/{idpId}{query}"
        )
        response = self._obtain_all_results(url)

        return response

    # saml-attr-controller-v-2
    def list_saml_attributes(self) -> list:
        """
        Method to get all SAML attributes

        :return: (list)
        """
        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/samlAttribute"
        response = self._obtain_all_results(url)

        return response

    # global-policy-controller

    def list_policies(
        self,
        policyType: str = "ACCESS_POLICY",
    ) -> list:
        """list policie(s)  by policy type,

        :param policyType: (str) Supported values Possible values = ACCESS_POLICY,GLOBAL_POLICY, TIMEOUT_POLICY,
        REAUTH_POLICY, SIEM_POLICY, CLIENT_FORWARDING_POLICY,BYPASS_POLICY

        :return: (list)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/policySet/rules/policyType/{policyType}"
        response = self._obtain_all_results(url)

        return response

    def list_policySet(
        self,
        policyType: str = "ACCESS_POLICY",
    ) -> json:
        """Gets the policy set for the specified policy type

        :param policyType: (str) Supported values are ACCESS_POLICY,GLOBAL_POLICY, TIMEOUT_POLICY,REAUTH_POLICY,
        SIEM_POLICY, CLIENT_FORWARDING_POLICY,BYPASS_POLICY

        :return: (json)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/policySet/policyType/{policyType}"
        response = self.hp_http.get_call(
            url,
            headers=self.header,
            error_handling=True,
        )

        return response.json()

    def add_policySet(
        self,
        app_operands: list,
        RuleName: str,
        Action: str,
        policySetId: int,
        operands: list,
        operator: str,
        MsgString: str = None,
    ) -> json:
        """
        Method to create a new access Policy

        :param app_operands: (list) List of app_operands: Examples = [{
        "objectType": "APP",
        "lhs": "id",
        "rhs": applicationId,
        }]
        :param RuleName: (str) Policy set Rule Name
        :param Action: (str) ALLOW / DENY
        :param policySetId: (int) Global Policy ID. can be obtained from list_global_policy_id
        :param operands: (list) List of operands. Example = [{
        "objectType": "SAML",
        "lhs": "<samlAttrId>",
        "rhs": "<samlAttrValue>",
        },{
        "objectType": "SCIM",
        "lhs": "<scimAttrId>",
        "rhs": "<scimAttrValue>”
        }]
        :param operator: (str)
        :param MsgString: (str)

        :return: (json)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/policySet/{policySetId}/rule"
        payload = {
            "conditions": [
                {"operands": app_operands},
                {
                    "operands": operands,
                    "operator": operator,
                },
            ],
            # Seems here needs to be AND
            "operator": "AND",
            "name": RuleName,
            "description": "Description",
            "action": Action,
            "customMsg": MsgString,
        }
        print(payload)
        response = self.hp_http.post_call(
            url=url,
            headers=self.header,
            error_handling=True,
            payload=payload,
        )

        return response.json()

    # Server Group Controller

    def list_server_groups(
        self,
        groupId: int = None,
    ) -> json or list:
        """
        Method to get all configured Server Groups. If groupI, get the Server Group details

        :param groupId: (int) The unique identifier of the Server Group.

        :return: (json|list)
        """
        if groupId:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/serverGroup/{groupId}"
            response = self.hp_http.get_call(
                url,
                headers=self.header,
                error_handling=True,
            ).json()
        else:
            url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/serverGroup"
            response = self._obtain_all_results(url)

        return response

    def add_server_groups(
        self,
        name: str,
        description: str,
        connector_group_id: list,
    ) -> json:
        """
        :param name: (str) Server Group Name
        :param description: (str) Description
        :param connector_group_id: (list) List of dictionaries with key as "id" and value connector_group_id.
        [{"id": connector_group_id}]

        :return: (json)
        """
        url = f"/mgmtconfig/v1/admin/customers/{self.customerId}/serverGroup"
        payload = {
            "enabled": True,
            "dynamicDiscovery": True,
            "name": name,
            "description": description,
            "servers": [],
            "appConnectorGroups": connector_group_id,
        }
        response = self.hp_http.post_call(
            url=url,
            headers=self.header,
            error_handling=True,
            payload=payload,
        )

        return response.json()

    def list_posture_profiles(
        self,
        query: str = False,
    ) -> list:
        """
        Method to Get all the idP details for a ZPA tenant

        :param query: (str) HTTP query

        :return: (list)
        """
        if not query:
            query = "?pagesize=500"
        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/posture{query}"
        response = self._obtain_all_results(url)

        return response

    def list_privileged_consoles(
        self,
        query: str = False,
    ) -> list:
        """
        Method to Get all the privleged_remote_consoles for a ZPA tenant

        :param query: (str) HTTP query

        :return: (list)
        """
        if not query:
            query = "?pagesize=500"
        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/privilegedConsoles{query}"
        response = self._obtain_all_results(url)

        return response

    def list_sra_consoles(self) -> list:
        """
        Method to obtain list of sra consoles from all application segments

        :return: (list)
        """
        sralist = []
        appsegments = self.list_application_segments()
        for apps in appsegments:
            srap = apps.get("sraApps")
            if srap is not None:
                sralist.extend(srap)

        return sralist

    # Certificate Controller v2
    def list_issued_certificates(
        self,
        query: str = None,
    ) -> list:
        """
        Method to get all issued certificates

        :return: (list)
        """
        if not query:
            query = "?pagesize=500"

        url = f"/mgmtconfig/v2/admin/customers/{self.customerId}/certificate/issued"
        response = self._obtain_all_results(url)

        return response