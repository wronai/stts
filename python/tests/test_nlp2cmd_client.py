import json
import unittest
from unittest.mock import MagicMock, patch

from stts_core import nlp2cmd_client


class TestNlp2cmdClient(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_query_ex_success_builds_request_and_parses_json(self, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = b"{\"success\": true, \"command\": \"echo hi\"}"
        mock_urlopen.return_value.__enter__.return_value = resp

        data, err = nlp2cmd_client.nlp2cmd_service_query_ex(
            query="hello",
            url="http://localhost:8123",
            execute=False,
            timeout=1.5,
        )

        self.assertIsNone(err)
        self.assertEqual(data.get("success"), True)
        self.assertEqual(data.get("command"), "echo hi")

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args.args[0]
        timeout = mock_urlopen.call_args.kwargs.get("timeout")
        self.assertEqual(timeout, 1.5)

        self.assertEqual(getattr(req, "full_url", ""), "http://localhost:8123/query")

        payload = json.loads((req.data or b"{}").decode("utf-8"))
        self.assertEqual(payload.get("query"), "hello")
        self.assertEqual(payload.get("dsl"), "shell")
        self.assertEqual(payload.get("execute"), False)

    @patch("urllib.request.urlopen")
    def test_query_ex_error_returns_exception(self, mock_urlopen):
        mock_urlopen.side_effect = RuntimeError("boom")

        data, err = nlp2cmd_client.nlp2cmd_service_query_ex(query="x", url="http://h", timeout=0.1)

        self.assertIsNone(data)
        self.assertIsInstance(err, RuntimeError)

    @patch("urllib.request.urlopen")
    def test_health_ex_healthy(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = b"{\"status\": \"healthy\"}"
        mock_urlopen.return_value.__enter__.return_value = resp

        ok, err = nlp2cmd_client.nlp2cmd_service_health_ex("http://localhost:8123", timeout=0.2)

        self.assertTrue(ok)
        self.assertIsNone(err)
        mock_urlopen.assert_called_once_with("http://localhost:8123/health", timeout=0.2)

    @patch("urllib.request.urlopen")
    def test_health_ex_non_200_status(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 503
        resp.read.return_value = b"{\"status\": \"healthy\"}"
        mock_urlopen.return_value.__enter__.return_value = resp

        ok, err = nlp2cmd_client.nlp2cmd_service_health_ex("http://localhost:8123", timeout=0.2)

        self.assertFalse(ok)
        self.assertIsNone(err)

    @patch("urllib.request.urlopen")
    def test_health_ex_error_returns_exception(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("no route")

        ok, err = nlp2cmd_client.nlp2cmd_service_health_ex("http://localhost:8123", timeout=0.2)

        self.assertFalse(ok)
        self.assertIsInstance(err, OSError)


if __name__ == "__main__":
    unittest.main()
