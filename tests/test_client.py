from unittest import TestCase
import requests_mock

from elastic_app_search import Client
from elastic_app_search.exceptions import InvalidDocument

class TestClient(TestCase):

    def setUp(self):
        self.engine_name = 'some-engine-name'
        self.client = Client('host_identifier', 'api_key')

        self.document_index_url = "{}/{}".format(
            self.client.session.base_url,
            "engines/{}/documents".format(self.engine_name)
        )

    def test_deprecated_init_support_with_old_names(self):
        self.client = Client(account_host_key='host_identifier', api_key='api_key')
        self.assertEqual(self.client.account_host_key, 'host_identifier')

    def test_deprecated_init_support_with_new_names(self):
        self.client = Client(host_identifier='host_identifier', api_key='api_key')
        self.assertEqual(self.client.account_host_key, 'host_identifier')

    def test_deprecated_init_support_with_positional(self):
        self.client = Client('host_identifier', 'api_key', 'example.com', False)
        self.assertEqual(self.client.account_host_key, 'host_identifier')

    def test_host_identifier_is_optional(self):
        client = Client('', 'api_key', 'localhost:3002/api/as/v1', False)
        query = 'query'

        with requests_mock.Mocker() as m:
            url = "http://localhost:3002/api/as/v1/engines/some-engine-name/search"
            m.register_uri('GET', url, json={}, status_code=200)
            client.search(self.engine_name, query, {})

    def test_index_document_processing_error(self):
        invalid_document = {'id': 'something', 'bad': {'no': 'nested'}}
        error = 'some processing error'
        stubbed_return = [{'id': 'something', 'errors': [error]}]
        with requests_mock.Mocker() as m:
            m.register_uri('POST', self.document_index_url, json=stubbed_return, status_code=200)

            with self.assertRaises(InvalidDocument) as context:
                self.client.index_document(self.engine_name, invalid_document)
                self.assertEqual(str(context.exception), error)

    def test_index_document_no_error_key_in_response(self):
        document_without_id = {'body': 'some value'}
        stubbed_return = [{'id': 'auto generated', 'errors': []}]

        with requests_mock.Mocker() as m:
            m.register_uri('POST', self.document_index_url, json=stubbed_return, status_code=200)
            response = self.client.index_document(self.engine_name, document_without_id)
            self.assertEqual(response, {'id': 'auto generated'})

    def test_index_documents(self):
        id = 'INscMGmhmX4'
        valid_document = {'id': id}
        other_document = { 'body': 'some value' }

        expected_return = [
            {'id': id, 'errors': []},
            {'id': 'some autogenerated id', 'errors': []}
        ]

        with requests_mock.Mocker() as m:
            m.register_uri('POST', self.document_index_url, json=expected_return, status_code=200)
            response = self.client.index_documents(self.engine_name, [valid_document, other_document])
            self.assertEqual(response, expected_return)

    def test_update_documents(self):
        id = 'INscMGmhmX4'
        valid_document = {'id': id}
        other_document = { 'body': 'some value' }

        expected_return = [
            {'id': id, 'errors': []},
            {'id': 'some autogenerated id', 'errors': []}
        ]

        with requests_mock.Mocker() as m:
            m.register_uri('PATCH', self.document_index_url, json=expected_return, status_code=200)
            response = self.client.update_documents(self.engine_name, [valid_document, other_document])
            self.assertEqual(response, expected_return)

    def test_get_documents(self):
        id = 'INscMGmhmX4'
        expected_return = [
            {
                'id': id,
                'url': 'http://www.youtube.com/watch?v=v1uyQZNg2vE',
                'title': 'The Original Grumpy Cat',
                'body': 'this is a test'
            }
        ]

        with requests_mock.Mocker() as m:
            m.register_uri('GET', self.document_index_url, json=expected_return, status_code=200)
            response = self.client.get_documents(self.engine_name, [id])
            self.assertEqual(response, expected_return)

    def test_list_documents(self):
        expected_return = {
            'meta': {
                'page': {'current': 1, 'total_results': 1, 'total_pages': 1, 'size': 20},
                'results': [
                    {'body': 'this is a test', 'id': '1'},
                    {'body': 'this is also a test', 'id': '2'}
                ]
            }
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/documents/list".format(self.client.session.base_url, self.engine_name)
            m.register_uri('GET',
                url,
                additional_matcher=lambda x: x.text == '{"page": {"current": 1, "size": 20}}',
                json=expected_return,
                status_code=200
            )

            response = self.client.list_documents(self.engine_name)
            self.assertEqual(response, expected_return)

    def test_destroy_documents(self):
        id = 'INscMGmhmX4'
        expected_return = [
            {'id': id, 'result': True}
        ]

        with requests_mock.Mocker() as m:
            m.register_uri('DELETE', self.document_index_url, json=expected_return, status_code=200)
            response = self.client.destroy_documents(self.engine_name, [id])
            self.assertEqual(response, expected_return)

    def test_get_schema(self):
        expected_return = {
            'square_km': 'text'
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/schema".format(self.client.session.base_url, self.engine_name)
            m.register_uri('GET',
                url,
                json=expected_return,
                status_code=200
            )

            response = self.client.get_schema(self.engine_name)
            self.assertEqual(response, expected_return)

    def test_update_schema(self):
        expected_return = {
            'square_mi': 'number',
            'square_km': 'number'
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/schema".format(self.client.session.base_url, self.engine_name)
            m.register_uri('POST',
                url,
                json=expected_return,
                status_code=200
            )

            response = self.client.update_schema(self.engine_name, expected_return)
            self.assertEqual(response, expected_return)

    def test_list_engines(self):
        expected_return = [
            { 'name': 'myawesomeengine' }
        ]

        with requests_mock.Mocker() as m:
            url = "{}/{}".format(self.client.session.base_url, 'engines')
            m.register_uri('GET',
                url,
                additional_matcher=lambda x: x.text == '{"page": {"current": 1, "size": 20}}',
                json=expected_return,
                status_code=200
            )
            response = self.client.list_engines()
            self.assertEqual(response, expected_return)

    def test_list_engines_with_paging(self):
        expected_return = [
            {'name': 'myawesomeengine'}
        ]

        with requests_mock.Mocker() as m:
            url = "{}/{}".format(self.client.session.base_url, 'engines')
            m.register_uri(
                'GET',
                url,
                additional_matcher=lambda x: x.text == '{"page": {"current": 10, "size": 2}}',
                json=expected_return,
                status_code=200
            )
            response = self.client.list_engines(current=10, size=2)
            self.assertEqual(response, expected_return)

    def test_get_engine(self):
        engine_name = 'myawesomeengine'
        expected_return = [
            { 'name': engine_name }
        ]

        with requests_mock.Mocker() as m:
            url = "{}/{}/{}".format(self.client.session.base_url,
                                    'engines',
                                    engine_name)
            m.register_uri('GET', url, json=expected_return, status_code=200)
            response = self.client.get_engine(engine_name)
            self.assertEqual(response, expected_return)

    def test_create_engine(self):
        engine_name = 'myawesomeengine'
        expected_return = {'name': engine_name, 'language': 'en'}

        with requests_mock.Mocker() as m:
            url = "{}/{}".format(self.client.session.base_url, 'engines')
            m.register_uri('POST', url, json=expected_return, status_code=200)
            response = self.client.create_engine(engine_name, 'en')
            self.assertEqual(response, expected_return)

    def test_destroy_engine(self):
        engine_name = 'myawesomeengine'
        expected_return = {'deleted': True}

        with requests_mock.Mocker() as m:
            url = "{}/{}/{}".format(self.client.session.base_url,
                                    'engines',
                                    engine_name)
            m.register_uri('DELETE', url, json=expected_return, status_code=200)
            response = self.client.destroy_engine(engine_name)
            self.assertEqual(response, expected_return)

    def test_list_synonym_sets(self):
        expected_return = {
            'meta': {
                'page': {
                    'current': 1,
                    'total_pages': 1,
                    'total_results': 3,
                    'size': 20
                }
            },
            'results': [
                {
                    'id': 'syn-5b11ac66c9f9292013220ad3',
                    'synonyms': [
                        'park',
                        'trail'
                    ]
                },
                {
                    'id': 'syn-5b11ac72c9f9296b35220ac9',
                    'synonyms': [
                        'protected',
                        'heritage'
                    ]
                },
                {
                    'id': 'syn-5b11ac66c9f9292013220ad3',
                    'synonyms': [
                        'hectares',
                        'acres'
                    ]
                }
            ]
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/synonyms".format(
                self.client.session.base_url,
                self.engine_name
            )
            m.register_uri(
                'GET',
                url,
                additional_matcher=lambda x: x.text == '{"page": {"current": 1, "size": 20}}',
                json=expected_return,
                status_code=200
            )

            response = self.client.list_synonym_sets(self.engine_name)

    def test_get_synonym_set(self):
        synonym_id = 'syn-5b11ac66c9f9292013220ad3'
        expected_return = {
            'id': synonym_id,
            'synonyms': [
                'park',
                'trail'
            ]
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/synonyms/{}".format(
                self.client.session.base_url,
                self.engine_name,
                synonym_id
            )
            m.register_uri(
                'GET',
                url,
                json=expected_return,
                status_code=200
            )

            response = self.client.get_synonym_set(
                self.engine_name,
                synonym_id
            )
            self.assertEqual(response, expected_return)

    def test_create_synonym_set(self):
        synonym_set = ['park', 'trail']
        expected_return = {
            'id': 'syn-5b11ac72c9f9296b35220ac9',
            'synonyms': [
                'park',
                'trail'
            ]
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/synonyms".format(
                self.client.session.base_url,
                self.engine_name
            )
            m.register_uri(
                'POST',
                url,
                json=expected_return,
                status_code=200
            )

            response = self.client.create_synonym_set(
                self.engine_name,
                synonym_set
            )
            self.assertEqual(response, expected_return)

    def test_update_synonym_set(self):
        synonym_id = 'syn-5b11ac72c9f9296b35220ac9'
        synonym_set = ['park', 'trail', 'ground']
        expected_return = {
            'id': synonym_id,
            'synonyms': [
                'park',
                'trail',
                'ground'
            ]
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/synonyms/{}".format(
                self.client.session.base_url,
                self.engine_name,
                synonym_id
            )
            m.register_uri(
                'PUT',
                url,
                json=expected_return,
                status_code=200
            )

            response = self.client.update_synonym_set(
                self.engine_name,
                synonym_id,
                synonym_set
            )
            self.assertEqual(response, expected_return)

    def test_destroy_synonym_set(self):
        synonym_id = 'syn-5b11ac66c9f9292013220ad3'
        expected_return = {
            'deleted': True
        }

        with requests_mock.Mocker() as m:
            url = "{}/engines/{}/synonyms/{}".format(
                self.client.session.base_url,
                self.engine_name,
                synonym_id
            )
            m.register_uri(
                'DELETE',
                url,
                json=expected_return,
                status_code=200
            )

            response = self.client.destroy_synonym_set(
                self.engine_name,
                synonym_id
            )
            self.assertEqual(response, expected_return)

    def test_search(self):
        query = 'query'
        expected_return = { 'meta': {}, 'results': []}

        with requests_mock.Mocker() as m:
            url = "{}/{}".format(
                self.client.session.base_url,
                "engines/{}/search".format(self.engine_name)
            )
            m.register_uri('GET', url, json=expected_return, status_code=200)
            response = self.client.search(self.engine_name, query, {})
            self.assertEqual(response, expected_return)

    def test_multi_search(self):
        expected_return = [{ 'meta': {}, 'results': []}, { 'meta': {}, 'results': []}]

        with requests_mock.Mocker() as m:
            url = "{}/{}".format(
                self.client.session.base_url,
                "engines/{}/multi_search".format(self.engine_name)
            )
            m.register_uri('GET', url, json=expected_return, status_code=200)
            response = self.client.multi_search(self.engine_name, {})
            self.assertEqual(response, expected_return)

    def test_query_suggestion(self):
        query = 'query'
        expected_return = { 'meta': {}, 'results': {}}

        with requests_mock.Mocker() as m:
            url = "{}/{}".format(
                self.client.session.base_url,
                "engines/{}/query_suggestion".format(self.engine_name)
            )
            m.register_uri('GET', url, json=expected_return, status_code=200)
            response = self.client.query_suggestion(self.engine_name, query, {})
            self.assertEqual(response, expected_return)

    def test_click(self):
        with requests_mock.Mocker() as m:
            url = "{}/{}".format(
                self.client.session.base_url,
                "engines/{}/click".format(self.engine_name)
            )
            m.register_uri('POST', url, json={}, status_code=200)
            self.client.click(self.engine_name, {'query': 'cat', 'document_id': 'INscMGmhmX4'})
