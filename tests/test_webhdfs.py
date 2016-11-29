from six.moves import http_client
import unittest
import types

import requests

from mock import MagicMock
from mock import patch

from pywebhdfs import errors
from pywebhdfs.webhdfs import PyWebHdfsClient, _raise_pywebhdfs_exception
from pywebhdfs import operations


class WhenTestingPyWebHdfsConstructor(unittest.TestCase):

    def test_init_default_args(self):
        webhdfs = PyWebHdfsClient()
        self.assertEqual('localhost', webhdfs.host)
        self.assertEqual('50070', webhdfs.port)
        self.assertIsNone(webhdfs.user_name)
        self.assertEqual(3, webhdfs.max_tries)

    def test_init_args_provided(self):
        host = '127.0.0.1'
        port = '50075'
        user_name = 'myUser'
        max_tries = 5

        webhdfs = PyWebHdfsClient(host=host, port=port, user_name=user_name,
                                  max_tries=max_tries)
        self.assertEqual(host, webhdfs.host)
        self.assertEqual(port, webhdfs.port)
        self.assertEqual(user_name, webhdfs.user_name)
        self.assertEqual(max_tries, webhdfs.max_tries)

    def test_init_path_to_hosts_provided(self):
        path_to_hosts = [('.*', ['localhost'])]
        webhdfs = PyWebHdfsClient(path_to_hosts=path_to_hosts)
        self.assertIsNotNone(webhdfs.path_to_hosts)


class WhenTestingCreateOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.location = 'redirect_uri'
        self.path = 'user/hdfs'
        self.file_data = '010101'
        self.init_response = MagicMock()
        self.init_response.headers = {'location': self.location}
        self.response = MagicMock()
        self.expected_headers = {'content-type': 'application/octet-stream'}

    def test_create_throws_exception_for_no_redirect(self):

        self.init_response.status_code = http_client.BAD_REQUEST
        self.response.status_code = http_client.CREATED
        self.requests.side_effect = [self.init_response, self.response]
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.create_file(self.path, self.file_data)

    def test_create_throws_exception_for_not_created(self):

        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.BAD_REQUEST
        self.requests.side_effect = [self.init_response, self.response]
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.create_file(self.path, self.file_data)

    def test_create_returns_file_location(self):

        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.CREATED
        self.requests.side_effect = [self.init_response, self.response]
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.create_file(self.path, self.file_data)
        self.assertTrue(result)
        self.requests.assert_called_with(
            self.location, headers=self.expected_headers, data=self.file_data)

    def test_create_handles_failures(self):
        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.CREATED
        self.requests.side_effect = [
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            self.response]
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.create_file(self.path, self.file_data)
        self.assertTrue(result)
        self.requests.assert_called_with(
            self.location, headers=self.expected_headers, data=self.file_data)

    def test_create_retries_at_most_max_tries(self):
        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.CREATED
        self.requests.side_effect = [
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            self.response]
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(requests.exceptions.ConnectionError):
                self.webhdfs.create_file(self.path, self.file_data)


class WhenTestingAppendOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.location = 'redirect_uri'
        self.path = 'user/hdfs'
        self.file_data = '010101'
        self.init_response = MagicMock()
        self.init_response.header = {'location': self.location}
        self.response = MagicMock()

    def test_append_throws_exception_for_no_redirect(self):

        self.init_response.status_code = http_client.BAD_REQUEST
        self.response.status_code = http_client.OK
        self.requests.side_effect = [self.init_response, self.response]
        with patch('requests.sessions.Session.post', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.append_file(self.path, self.file_data)

    def test_append_throws_exception_for_not_ok(self):

        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.BAD_REQUEST
        self.requests.side_effect = [self.init_response, self.response]
        with patch('requests.sessions.Session.post', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.append_file(self.path, self.file_data)

    def test_append_returns_true(self):

        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.OK
        self.requests.side_effect = [self.init_response, self.response]
        with patch('requests.sessions.Session.post', self.requests):
            result = self.webhdfs.append_file(self.path, self.file_data)
        self.assertTrue(result)

    def test_append_handles_failures(self):
        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.OK
        self.requests.side_effect = [
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            self.response]
        with patch('requests.sessions.Session.post', self.requests):
            result = self.webhdfs.append_file(self.path, self.file_data)
        self.assertTrue(result)

    def test_append_retries_at_most_max_tries(self):
        self.init_response.status_code = http_client.TEMPORARY_REDIRECT
        self.response.status_code = http_client.OK
        self.requests.side_effect = [
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            requests.exceptions.ConnectionError,
            self.init_response,
            self.response]
        with patch('requests.sessions.Session.post', self.requests):
            with self.assertRaises(requests.exceptions.ConnectionError):
                self.webhdfs.append_file(self.path, self.file_data)


class WhenTestingOpenOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs'
        self.file_data = u'010101'
        self.response = MagicMock()
        self.response.content = self.file_data

    def test_read_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.read_file(self.path)

    def test_read_returns_file(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.read_file(self.path)
        self.assertEqual(result, self.file_data)

    def test_stream_returns_generator(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.stream_file(self.path)
        self.assertIsInstance(result, types.GeneratorType)


class WhenTestingMkdirOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs'
        self.response = MagicMock()

    def test_mkdir_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.make_dir(self.path)

    def test_mkdir_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.make_dir(self.path)
        self.assertTrue(result)


class WhenTestingRenameOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.new_path = '/user/hdfs/new_dir'
        self.response = MagicMock()
        self.rename = {"boolean": True}
        self.response.json = MagicMock(return_value=self.rename)

    def test_rename_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.rename_file_dir(self.path, self.new_path)

    def test_rename_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.rename_file_dir(self.path, self.new_path)
        self.assertEqual(result, {"boolean": True})


class WhenTestingDeleteOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()

    def test_rename_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.delete', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.delete_file_dir(self.path)

    def test_rename_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.delete', self.requests):
            result = self.webhdfs.delete_file_dir(self.path)
        self.assertTrue(result)


class WhenTestingGetFileStatusOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()
        self.file_status = {
            "FileStatus": {
                "accessTime": 0,
                "blockSize": 0,
                "group": "supergroup",
                "length": 0,
                "modificationTime": 1320173277227,
                "owner": "webuser",
                "pathSuffix": "",
                "permission": "777",
                "replication": 0,
                "type": "DIRECTORY"
            }
        }
        self.response.json = MagicMock(return_value=self.file_status)

    def test_get_status_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.get_file_dir_status(self.path)

    def test_get_status_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.get_file_dir_status(self.path)

        for key in result:
            self.assertEqual(result[key], self.file_status[key])


class WhenTestingGetContentSummaryOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()
        self.file_status = {
            "ContentSummary": {
                "directoryCount": 2,
                "fileCount": 1,
                "length": 24930,
                "quota": -1,
                "spaceConsumed": 24930,
                "spaceQuota": -1
            }
        }
        self.response.json = MagicMock(return_value=self.file_status)

    def test_get_status_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.get_content_summary(self.path)

    def test_get_status_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.get_content_summary(self.path)

        for key in result:
            self.assertEqual(result[key], self.file_status[key])


class WhenTestingGetFileChecksumOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()
        self.file_checksum = {
            "FileChecksum": {
                "algorithm": "MD5-of-1MD5-of-512CRC32",
                "bytes": ("000002000000000000000000729a144ad5e9399f70c9bedd757"
                          "2e6bf00000000"),
                "length": 28
            }
        }
        self.response.json = MagicMock(return_value=self.file_checksum)

    def test_get_status_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.get_file_checksum(self.path)

    def test_get_status_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.get_file_checksum(self.path)

        for key in result:
            self.assertEqual(result[key], self.file_checksum[key])


class WhenTestingListDirOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()
        self.file_status = {
            "FileStatuses": {
                "FileStatus": [
                    {
                        "accessTime": 0,
                        "blockSize": 0,
                        "group": "supergroup",
                        "length": 24930,
                        "modificationTime": 1320173277227,
                        "owner": "webuser",
                        "pathSuffix": "a.patch",
                        "permission": "777",
                        "replication": 0,
                        "type": "FILE"
                    },
                    {
                        "accessTime": 0,
                        "blockSize": 0,
                        "group": "supergroup",
                        "length": 0,
                        "modificationTime": 1320173277227,
                        "owner": "webuser",
                        "pathSuffix": "",
                        "permission": "777",
                        "replication": 0,
                        "type": "DIRECTORY"
                    }
                ]
            }
        }
        self.response.json = MagicMock(return_value=self.file_status)

    def test_get_status_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.list_dir(self.path)

    def test_get_status_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.list_dir(self.path)

        for key in result:
            self.assertEqual(result[key], self.file_status[key])


class WhenTestingFileExistsOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()
        self.file_status = {
            "FileStatus": {
                "accessTime": 0,
                "blockSize": 0,
                "group": "supergroup",
                "length": 0,
                "modificationTime": 1320173277227,
                "owner": "webuser",
                "pathSuffix": "",
                "permission": "777",
                "replication": 0,
                "type": "DIRECTORY"
            }
        }
        self.response.json = MagicMock(return_value=self.file_status)

    def test_exists_throws_exception_for_error(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.exists_file_dir(self.path)

    def test_exists_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            self.assertTrue(self.webhdfs.exists_file_dir(self.path))

    def test_exists_returns_false(self):

        self.response.status_code = http_client.NOT_FOUND
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            self.assertFalse(self.webhdfs.exists_file_dir(self.path))


class WhenTestingGetXattrOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.xattr = 'user.test'
        self.response = MagicMock()
        self.file_status = {
            "XAttrs": [
                {
                    "name": self.xattr,
                    "value": "1"
                }
            ]
        }
        self.response.json = MagicMock(return_value=self.file_status)

    def test_get_xattr_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.get_xattr(self.path, self.xattr)

    def test_get_xattr_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.get_xattr(self.path, self.xattr)

        for key in result:
            self.assertEqual(result[key], self.file_status[key])


class WhenTestingSetXattrOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.xattr = 'user.test'
        self.value = '1'
        self.response = MagicMock()

    def test_set_xattr_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.set_xattr(self.path, self.xattr, self.value)

    def test_set_xattr_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.set_xattr(self.path, self.xattr, self.value)

        self.assertTrue(result)

    def test_set_xattr_replace_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.set_xattr(
                self.path, self.xattr, self.value, replace=True)

        self.assertTrue(result)


class WhenTestingListXattrsOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.response = MagicMock()
        self.file_status = {
            "XAttrNames":
                [
                    "[\"XATTRNAME1\",\"XATTRNAME2\",\"XATTRNAME3\"]"
                ]
        }
        self.response.json = MagicMock(return_value=self.file_status)

    def test_list_xattrs_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.list_xattrs(self.path)

    def test_list_xattrs_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.get', self.requests):
            result = self.webhdfs.list_xattrs(self.path)

        for key in result:
            self.assertEqual(result[key], self.file_status[key])


class WhenTestingDeleteXattrOperation(unittest.TestCase):

    def setUp(self):

        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)
        self.response = MagicMock()
        self.requests = MagicMock(return_value=self.response)
        self.path = 'user/hdfs/old_dir'
        self.xattr = 'user.test'
        self.response = MagicMock()

    def test_delete_xattr_throws_exception_for_not_ok(self):

        self.response.status_code = http_client.BAD_REQUEST
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            with self.assertRaises(errors.PyWebHdfsException):
                self.webhdfs.delete_xattr(self.path, self.xattr)

    def test_delete_xattr_returns_true(self):

        self.response.status_code = http_client.OK
        self.requests.return_value = self.response
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs.delete_xattr(self.path, self.xattr)

        self.assertTrue(result)


class WhenTestingCreateUri(unittest.TestCase):

    def setUp(self):
        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.path = 'user/hdfs'
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)

    def test_create_uri_no_kwargs(self):
        op = operations.CREATE
        uri = 'http://{{host}}:{port}/webhdfs/v1/' \
              '{path}?op={op}&user.name={user}'\
              .format(port=self.port, path=self.path,
                      op=op, user=self.user_name)
        result = self.webhdfs._create_uri(self.path, op)
        self.assertEqual(uri, result)

    def test_create_uri_with_kwargs(self):
        op = operations.CREATE
        mykey = 'mykey'
        myval = 'myval'
        uri = 'http://{{host}}:{port}/webhdfs/v1/' \
              '{path}?op={op}&{key}={val}' \
              '&user.name={user}' \
              .format(
                  port=self.port, path=self.path,
                  op=op, key=mykey, val=myval, user=self.user_name)
        result = self.webhdfs._create_uri(self.path, op,
                                          mykey=myval)
        self.assertEqual(uri, result)

    def test_create_uri_with_leading_slash(self):
        op = operations.CREATE
        uri_path_no_slash = self.webhdfs._create_uri(self.path, op)
        uri_path_with_slash = self.webhdfs._create_uri('/' + self.path, op)
        self.assertEqual(uri_path_no_slash, uri_path_with_slash)

    def test_create_uri_with_unicode_path(self):
        op = operations.CREATE
        mykey = 'mykey'
        myval = 'myval'
        path = u'die/Stra\xdfe'
        quoted_path = 'die/Stra%C3%9Fe'
        uri = 'http://{{host}}:{port}/webhdfs/v1/' \
              '{path}?op={op}&{key}={val}' \
              '&user.name={user}' \
              .format(
                  port=self.port, path=quoted_path,
                  op=op, key=mykey, val=myval, user=self.user_name)
        result = self.webhdfs._create_uri(path, op, mykey=myval)
        self.assertEqual(uri, result)


class WhenTestingResolveHost(unittest.TestCase):

    def setUp(self):
        self.host = 'hostname'
        self.port = '00000'
        self.user_name = 'username'
        self.path = 'user/hdfs'
        self.timeout = None
        self.webhdfs = PyWebHdfsClient(host=self.host, port=self.port,
                                       user_name=self.user_name)

        self.session = requests.Session()
        self.data = '01011010'
        self.headers = {'content-type': 'application/octet-stream'}

        self.response = MagicMock()
        self.response.status_code = http_client.TEMPORARY_REDIRECT
        self.requests = MagicMock(return_value=self.response)

    def test_method_is_called_with_correct_arguments(self):
        uri = self.webhdfs._create_uri(self.path, 'CREATE').format(host=self.host)
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs._resolve_host(
                self.session.put, True, self.path, 'CREATE')
        self.assertTrue(result)
        self.assertEqual(len(self.requests.mock_calls), 1)
        self.requests.assert_called_with(uri, allow_redirects=True, timeout=self.timeout)

    def test_retries_are_made_max_tries(self):
        self.requests.side_effect = [
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            self.response]
        with patch('requests.sessions.Session.put', self.requests):
            result = self.webhdfs._resolve_host(
                self.session.put, True, self.path, 'CREATE')
        self.assertTrue(result)
        self.assertEqual(len(self.requests.mock_calls), 3)

    def test_retries_are_made_at_most_max_tries(self):
        self.requests.side_effect = [
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectionError,
            self.response]
        with self.assertRaises(requests.exceptions.ConnectionError):
            with patch('requests.sessions.Session.put', self.requests):
                self.webhdfs._resolve_host(
                    self.session.put, True, self.path, 'CREATE')

    def test_non_requests_exceptions_bubble_up(self):
        self.requests.side_effect = errors.FileNotFound
        with self.assertRaises(errors.FileNotFound):
            with patch('requests.sessions.Session.put', self.requests):
                self.webhdfs._resolve_host(
                    self.session.put, True, self.path, 'CREATE')


class WhenTestingRaiseExceptions(unittest.TestCase):

    def test_400_raises_bad_request(self):
        with self.assertRaises(errors.BadRequest):
            _raise_pywebhdfs_exception(http_client.BAD_REQUEST)

    def test_401_raises_unuathorized(self):
        with self.assertRaises(errors.Unauthorized):
            _raise_pywebhdfs_exception(http_client.UNAUTHORIZED)

    def test_404_raises_not_found(self):
        with self.assertRaises(errors.FileNotFound):
            _raise_pywebhdfs_exception(http_client.NOT_FOUND)

    def test_all_other_raises_pywebhdfs_exception(self):
        with self.assertRaises(errors.PyWebHdfsException):
            _raise_pywebhdfs_exception(http_client.GATEWAY_TIMEOUT)
