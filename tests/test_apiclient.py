# -*- coding: utf-8 -*-
import os

from flask import json
import requests
import requests_mock
import pytest
import mock

from dmutils.apiclient import BaseAPIClient, SearchAPIClient, DataAPIClient
from dmutils.apiclient import APIError, HTTPError, InvalidResponse
from dmutils.apiclient import REQUEST_ERROR_STATUS_CODE, REQUEST_ERROR_MESSAGE


@pytest.yield_fixture
def rmock():
    with requests_mock.mock() as rmock:
        yield rmock


@pytest.yield_fixture
def raw_rmock():
    with mock.patch('dmutils.apiclient.requests.request') as rmock:
        yield rmock


@pytest.fixture
def base_client():
    return BaseAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def search_client():
    return SearchAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def data_client():
    return DataAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def service():
    """A stripped down G6-IaaS service"""
    return {
        "id": "1234567890123456",
        "supplierId": 1,
        "lot": "IaaS",
        "title": "My Iaas Service",
        "lastUpdated": "2014-12-23T14:46:17Z",
        "lastUpdatedByEmail": "supplier@digital.cabinet-office.gov.uk",
        "lastCompleted": "2014-12-23T14:46:22Z",
        "lastCompletedByEmail": "supplier@digital.cabinet-office.gov.uk",
        "serviceTypes": [
            "Compute",
            "Storage"
        ],
        "serviceName": "My Iaas Service",
        "serviceSummary": "IaaS Service Summary",
        "serviceBenefits": [
            "Free lollipop to every 10th customer",
            "It's just lovely"
        ],
        "serviceFeatures": [
            "[To be completed]",
            "This is my second \"feture\""
        ],
        "minimumContractPeriod": "Month",
        "terminationCost": True,
        "priceInterval": "",
        "trialOption": True,
        "priceUnit": "Person",
        "educationPricing": True,
        "vatIncluded": False,
        "priceString": "£10.0067 per person",
        "priceMin": 10.0067,
        "freeOption": False,
        "openStandardsSupported": True,
        "supportForThirdParties": False,
        "supportResponseTime": "3 weeks.",
        "incidentEscalation": True,
        "serviceOffboarding": True,
        "serviceOnboarding": False,
        "analyticsAvailable": False,
        "persistentStorage": True,
        "elasticCloud": True,
        "guaranteedResources": False,
        "selfServiceProvisioning": False,
        "openSource": False,
        "apiType": "SOAP, Rest | JSON",
        "apiAccess": True,
        "networksConnected": [
            "Public Services Network (PSN)",
            "Government Secure intranet (GSi)"
        ],
        "offlineWorking": True,
        "dataExtractionRemoval": False,
        "dataBackupRecovery": True,
        "datacentreTier": "TIA-942 Tier 3",
        "datacentresSpecifyLocation": True,
        "datacentresEUCode": False,
        }


class TestBaseApiClient(object):
    def test_connection_error_raises_api_error(self, base_client, raw_rmock):
        raw_rmock.side_effect = requests.exceptions.ConnectionError(
            None
        )
        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == REQUEST_ERROR_MESSAGE
        assert e.value.status_code == REQUEST_ERROR_STATUS_CODE

    def test_http_error_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            text="Internal Error",
            status_code=500)

        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == REQUEST_ERROR_MESSAGE
        assert e.value.status_code == 500

    def test_non_2xx_response_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            json={"error": "Not found"},
            status_code=404)

        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == "Not found"
        assert e.value.status_code == 404

    def test_invalid_json_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            text="Internal Error",
            status_code=200)

        with pytest.raises(InvalidResponse) as e:
            base_client._request("GET", '/')

        assert e.value.message == "No JSON object could be decoded"
        assert e.value.status_code == 200


class TestSearchApiClient(object):
    def test_init_app_sets_attributes(self, search_client):
        app = mock.Mock()
        app.config = {
            "DM_SEARCH_API_URL": "http://example",
            "DM_SEARCH_API_AUTH_TOKEN": "example-token",
            "ES_ENABLED": False,
            }
        search_client.init_app(app)

        assert search_client.base_url == "http://example"
        assert search_client.auth_token == "example-token"
        assert not search_client.enabled

    def test_get_status(self, data_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = data_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_convert_service(self, search_client, service):
        converted = search_client._convert_service(
            service['id'], service, "Supplier Name", "Framework Name")

        assert "service" in converted
        assert "service" in converted
        assert converted["service"]["id"] == "1234567890123456"
        assert converted["service"]["lot"] == "IaaS"
        assert converted["service"]["frameworkName"] == "Framework Name"
        assert converted["service"]["serviceName"] == "My Iaas Service"
        assert \
            converted["service"]["serviceSummary"] == "IaaS Service Summary"
        assert converted["service"]["serviceBenefits"] == [
            "Free lollipop to every 10th customer",
            "It's just lovely"
        ]
        assert converted["service"]["serviceFeatures"] == [
            "[To be completed]",
            "This is my second \"feture\""
        ]
        assert converted["service"]["serviceTypes"] == [
            "Compute",
            "Storage"
        ]
        assert converted["service"]["supplierName"] == "Supplier Name"
        assert not converted["service"]["freeOption"]
        assert converted["service"]["trialOption"]
        assert converted["service"]["minimumContractPeriod"] == "Month"
        assert not converted["service"]["supportForThirdParties"]
        assert not converted["service"]["selfServiceProvisioning"]
        assert not converted["service"]["datacentresEUCode"]
        assert converted["service"]["dataBackupRecovery"]
        assert not converted["service"]["dataExtractionRemoval"]
        assert converted["service"]["networksConnected"] == [
            "Public Services Network (PSN)",
            "Government Secure intranet (GSi)"
        ]
        assert converted["service"]["apiAccess"]
        assert converted["service"]["openStandardsSupported"]
        assert not converted["service"]["openSource"]
        assert converted["service"]["persistentStorage"]
        assert not converted["service"]["guaranteedResources"]
        assert converted["service"]["elasticCloud"]

    def test_convert_service_with_minimum_fields_for_indexing(
            self, search_client, service):
        del service["serviceTypes"]
        del service["serviceBenefits"]
        del service["serviceFeatures"]

        converted = search_client._convert_service(
            service['id'], service, "Supplier Name", "Framework Name")

        assert "service" in converted
        assert converted["service"]["id"] == "1234567890123456"
        assert converted["service"]["lot"] == "IaaS"
        assert converted["service"]["frameworkName"] == "Framework Name"
        assert converted["service"]["serviceName"] == "My Iaas Service"
        assert \
            converted["service"]["serviceSummary"] == "IaaS Service Summary"
        assert "serviceBenefits" not in converted
        assert "serviceFeatures" not in converted
        assert "serviceTypes" not in converted
        assert converted["service"]["supplierName"] == "Supplier Name"

    def test_post_to_index_with_type_and_service_id(
            self, search_client, rmock, service):
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            "12345",
            service,
            "Supplier name",
            "Framework Name")
        assert result == {'message': 'acknowledged'}

    def test_delete_to_delete_method_service_id(
            self, search_client, rmock):
        rmock.delete(
            'http://baseurl/g-cloud/services/12345',
            json={"services": {
                "_id": "12345",
                "_index": "g-cloud",
                "_type": "services",
                "_version": 1,
                "found": True
            }},
            status_code=200)
        result = search_client.delete("12345")
        assert result['services']['found'] is True

    def test_should_not_call_search_api_is_es_disabled(
            self, search_client, rmock, service):
        search_client.enabled = False
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            "12345",
            service,
            "Supplier name",
            "Framework Name")
        assert result is None
        assert not rmock.called

    def test_should_raise_error_on_failure(
            self, search_client, rmock, service):
        with pytest.raises(APIError):
            rmock.put(
                'http://baseurl/g-cloud/services/12345',
                json={'error': 'some error'},
                status_code=400)
            search_client.index(
                "12345",
                service,
                "Supplier name",
                "Framework Name")

    def test_search_services(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?q=foo&'
            'filter_minimumContractPeriod=a,b&'
            'filter_something=a&filter_something=b',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(
            q='foo',
            minimumContractPeriod=['a', 'b'],
            something=['a', 'b'])
        assert result == {'services': "myresponse"}

    def test_search_services_with_blank_query(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(q='')
        assert result == {'services': "myresponse"}
        assert rmock.last_request.query == ''

    def test_search_services_with_pagination(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?page=10',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(q='', page=10)
        assert result == {'services': "myresponse"}
        assert rmock.last_request.query == 'page=10'

    @staticmethod
    def load_example_listing(name):
        file_path = os.path.join("example_listings", "{}.json".format(name))
        with open(file_path) as f:
            return json.load(f)


class TestDataApiClient(object):
    def test_request_id_is_added_if_available(
            self, data_client, rmock, app_with_logging):
        headers = {'DM-Request-Id': 'generated'}
        with app_with_logging.test_request_context('/', headers=headers):
            rmock.get(
                "http://baseurl/_status",
                json={"status": "ok"},
                status_code=200)

            data_client.get_status()

            assert rmock.last_request.headers["DM-Request-Id"] == "generated"

    def test_request_id_is_not_added_if_logging_is_not_loaded(
            self, data_client, rmock, app):
        headers = {'DM-Request-Id': 'generated'}
        with app.test_request_context('/', headers=headers):
            rmock.get(
                "http://baseurl/_status",
                json={"status": "ok"},
                status_code=200)

            data_client.get_status()

            assert "DM-Request-Id" not in rmock.last_request.headers

    def test_init_app_sets_attributes(self, data_client):
        app = mock.Mock()
        app.config = {
            "DM_DATA_API_URL": "http://example",
            "DM_DATA_API_AUTH_TOKEN": "example-token",
            }
        data_client.init_app(app)

        assert data_client.base_url == "http://example"
        assert data_client.auth_token == "example-token"

    def test_get_status(self, data_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = data_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_get_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_service(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_service_returns_none_on_404(self, data_client, rmock):
        rmock.get(
            'http://baseurl/services/123',
            json={'services': 'result'},
            status_code=404)

        result = data_client.get_service(123)

        assert result is None

    def test_get_service_raises_on_non_404(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.get(
                'http://baseurl/services/123',
                json={'services': 'result'},
                status_code=400)

            data_client.get_service(123)

    def test_find_services(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services()

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_services_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?page=2",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(page=2)

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_services_adds_supplier_id_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=1",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(supplier_id=1)

        assert result == {"services": "result"}
        assert rmock.called

    def test_create_service(self, data_client, rmock):
        rmock.put(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=201,
        )

        result = data_client.create_service(
            123, {"foo": "bar"}, "person", "reason")

        assert result == {"services": "result"}
        assert rmock.called

    def test_update_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service(
            123, {"foo": "bar"}, "person", "reason")

        assert result == {"services": "result"}
        assert rmock.called

    def test_update_service_status(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123/status/published",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service_status(
            123, "published", "person", "reason")

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_user_by_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/1234",
            json=self.user(),
            status_code=200)
        user = data_client.get_user(user_id=1234)

        assert user == self.user()

    def test_get_user_by_email_address(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?email=myemail",
            json=self.user(),
            status_code=200)
        user = data_client.get_user(email_address="myemail")

        assert user == self.user()

    def test_get_user_fails_if_both_email_and_id_are_provided(
            self, data_client, rmock):

        with pytest.raises(ValueError):
            data_client.get_user(user_id=123, email_address="myemail")

    def test_get_user_fails_if_neither_email_or_id_are_provided(
            self, data_client, rmock):

        with pytest.raises(ValueError):
            data_client.get_user()

    def test_get_user_returns_none_on_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/123",
            json={"not": "found"},
            status_code=404)

        user = data_client.get_user(user_id=123)

        assert user is None

    def test_authenticate_user_is_called_with_correct_params(
            self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/auth",
            json=self.user(),
            status_code=200)

        user = data_client.authenticate_user(
            "email_address", "password")['users']

        assert user['id'] == "id"
        assert user['email_address'] == "email_address"
        assert user['supplier']['supplier_id'] == 1234
        assert user['supplier']['name'] == "name"

    def test_authenticate_user_returns_none_on_404(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=404)

        user = data_client.authenticate_user(
            "email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_403(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=403)

        user = data_client.authenticate_user(
            "email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_400(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=400)

        user = data_client.authenticate_user(
            "email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_non_supplier(
            self, data_client, rmock):
        user_with_no_supplier = self.user()
        del user_with_no_supplier['users']['supplier']

        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps(user_with_no_supplier),
            status_code=200)

        user = data_client.authenticate_user(
            "email_address", "password")

        assert user is None

    def test_authenticate_user_raises_on_500(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.post(
                'http://baseurl/users/auth',
                text=json.dumps({'authorization': False}),
                status_code=500)

            data_client.authenticate_user("email_address", "password")

    def test_create_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users",
            json={"users": "result"},
            status_code=201)

        result = data_client.create_user({"foo": "bar"})

        assert result == {"users": "result"}
        assert rmock.called

    def test_update_user_password(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        assert data_client.update_user_password(123, "newpassword")
        assert rmock.last_request.json() == {
            "users": {"password": "newpassword"}
        }

    def test_update_user_password_returns_false_on_non_200(
            self, data_client, rmock):
        for status_code in [400, 403, 404, 500]:
            rmock.post(
                "http://baseurl/users/123",
                json={},
                status_code=status_code)
            assert not data_client.update_user_password(123, "newpassword")

    @staticmethod
    def user():
        return {'users': {
            'id': 'id',
            'email_address': 'email_address',
            'name': 'name',
            'role': 'role',
            'active': 'active',
            'locked': False,
            'created_at': "2015-05-05T05:05:05",
            'updated_at': "2015-05-05T05:05:05",
            'password_changed_at': "2015-05-05T05:05:05",
            'supplier': {
                'supplier_id': 1234,
                'name': 'name'
            }
        }}

    def test_find_suppliers_with_no_prefix(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers()

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_prefix(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?prefix=a",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(prefix='a')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_supplier_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?page=2",
            json={"suppliers": "result"},
            status_code=200)

        result = data_client.find_suppliers(page=2)

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_find_services_by_supplier(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=123",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(supplier_id=123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_supplier_by_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_supplier(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_create_supplier(self, data_client, rmock):
        rmock.put(
            "http://baseurl/suppliers/123",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.create_supplier(123, {"foo": "bar"})

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_update_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.update_supplier(123, {"foo": "bar"}, 'supplier')

        assert result == {"suppliers": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'suppliers': {'foo': 'bar'}, 'updated_by': 'supplier'
        }

    def test_update_contact_information(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/contact-information/2",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.update_contact_information(
            123, 2, {"foo": "bar"}, 'supplier'
        )

        assert result == {"suppliers": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'contactInformation': {'foo': 'bar'}, 'updated_by': 'supplier'
        }

    def test_find_draft_services(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services?supplier_id=2",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.find_draft_services(2)

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_get_draft_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services/2/draft",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.get_draft_service(2)

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_delete_draft_service(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/services/2/draft",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.delete_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'update_details': {
                'update_reason': 'deprecated', 'updated_by': 'user'
            }
        }

    def test_create_draft_service(self, data_client, rmock):
        rmock.put(
            "http://baseurl/services/2/draft",
            json={"done": "it"},
            status_code=201,
        )

        result = data_client.create_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'update_details': {
                'update_reason': 'deprecated', 'updated_by': 'user'
            }
        }

    def test_update_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/2/draft",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'update_details': {
                'update_reason': 'deprecated', 'updated_by': 'user'
            }
        }

    def test_launch_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/2/draft/publish",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.launch_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'update_details': {
                'update_reason': 'deprecated', 'updated_by': 'user'
            }
        }
