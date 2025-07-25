"""Tests for mistmcp __main__ module"""

from unittest.mock import Mock, patch

import pytest
from mistmcp.__main__ import main, print_help, start
from mistmcp.config import ToolLoadingMode


class TestPrintHelp:
    """Test print_help function"""

    def test_print_help_output(self, capsys) -> None:
        """Test help message is printed correctly"""
        print_help()
        captured = capsys.readouterr()
        assert (
            "Mist MCP Server - AI-Powered Network Management Assistant" in captured.out
        )
        assert "TOOL LOADING MODES:" in captured.out
        assert "managed" in captured.out
        assert "all" in captured.out


class TestStart:
    """Test start function"""

    @patch("mistmcp.__main__.create_mcp_server")
    def test_start_http_managed(self, mock_create_server) -> None:
        """Test starting with HTTP transport and managed mode"""
        mock_server = Mock()
        mock_create_server.return_value = mock_server

        start("http", ToolLoadingMode.MANAGED, [], "127.0.0.1", 8000, debug=True)

        mock_create_server.assert_called_once()
        config_arg = mock_create_server.call_args[0][0]

        assert config_arg.tool_loading_mode == ToolLoadingMode.MANAGED
        assert config_arg.debug is True
        assert config_arg.transport_mode == "http"
        mock_server.run.assert_called_once_with(
            transport="streamable-http", host="127.0.0.1", port=8000
        )

    @patch("mistmcp.__main__.create_mcp_server")
    def test_start_http_managed_with_custom_mcp_host(self, mock_create_server) -> None:
        """Test starting with HTTP transport and managed mode"""
        mock_server = Mock()
        mock_create_server.return_value = mock_server

        start(
            "http",
            ToolLoadingMode.MANAGED,
            [],
            mcp_host="0.0.0.0",
            mcp_port=8000,
            debug=True,
        )

        mock_create_server.assert_called_once()
        config_arg = mock_create_server.call_args[0][0]

        assert config_arg.tool_loading_mode == ToolLoadingMode.MANAGED
        assert config_arg.debug is True
        assert config_arg.transport_mode == "http"
        mock_server.run.assert_called_once_with(
            transport="streamable-http", host="0.0.0.0", port=8000
        )

    @patch("mistmcp.__main__.create_mcp_server")
    def test_start_keyboard_interrupt(self, mock_create_server, capsys) -> None:
        """Test handling of KeyboardInterrupt"""
        mock_server = Mock()
        mock_server.run.side_effect = KeyboardInterrupt()
        mock_create_server.return_value = mock_server

        start(
            "stdio",
            ToolLoadingMode.MANAGED,
            [],
            mcp_host="127.0.0.1",
            mcp_port=8000,
            debug=False,
        )

        captured = capsys.readouterr()
        assert "stopped by user" in captured.err

    @patch("mistmcp.__main__.create_mcp_server")
    def test_start_exception_without_debug(self, mock_create_server, capsys) -> None:
        """Test handling of exceptions without debug mode"""
        mock_create_server.side_effect = Exception("Test error")

        start(
            "stdio",
            ToolLoadingMode.MANAGED,
            [],
            mcp_host="127.0.0.1",
            mcp_port=8000,
            debug=False,
        )

        captured = capsys.readouterr()
        assert "Mist MCP Error: Test error" in captured.err

    @patch("mistmcp.__main__.create_mcp_server")
    @patch("traceback.print_exc")
    def test_start_exception_with_debug(
        self, mock_traceback, mock_create_server, capsys
    ) -> None:
        """Test handling of exceptions with debug mode"""
        mock_create_server.side_effect = Exception("Test error")

        start(
            "stdio",
            ToolLoadingMode.MANAGED,
            [],
            mcp_host="127.0.0.1",
            mcp_port=8000,
            debug=True,
        )

        captured = capsys.readouterr()
        assert "Mist MCP Error: Test error" in captured.err
        mock_traceback.assert_called_once()

    @patch("mistmcp.__main__.create_mcp_server")
    def test_start_debug_output(self, mock_create_server, capsys) -> None:
        """Test debug output is printed"""
        mock_server = Mock()
        mock_create_server.return_value = mock_server

        start(
            "http",
            ToolLoadingMode.MANAGED,
            [],
            mcp_host="127.0.0.1",
            mcp_port=8000,
            debug=True,
        )

        captured = capsys.readouterr()
        assert "Starting Mist MCP Server with configuration" in captured.err
        assert "TRANSPORT: http" in captured.err
        assert "TOOL LOADING MODE: managed" in captured.err


class TestMain:
    """Test main function"""

    @patch("mistmcp.__main__.start")
    def test_main_default_args(self, mock_start) -> None:
        """Test main with default arguments"""
        with patch("sys.argv", ["mistmcp"]):
            main()

        mock_start.assert_called_once_with(
            "stdio", ToolLoadingMode.ALL, [], "127.0.0.1", 8000, False
        )

    @patch("mistmcp.__main__.start")
    def test_main_all_mode(self, mock_start) -> None:
        """Test main with all mode"""
        with patch("sys.argv", ["mistmcp", "--mode", "all", "--debug"]):
            main()

        mock_start.assert_called_once_with(
            "stdio", ToolLoadingMode.ALL, [], "127.0.0.1", 8000, True
        )

    def test_main_invalid_mode(self, capsys) -> None:
        """Test main with invalid mode"""
        with patch("sys.argv", ["mistmcp", "--mode", "invalid"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "invalid choice: 'invalid'" in captured.err

    def test_main_help_exits(self) -> None:
        """Test that --help exits appropriately"""
        with patch("sys.argv", ["mistmcp", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

    @patch("sys.argv", ["mistmcp", "--invalid-arg"])
    def test_main_invalid_arg_exits(self) -> None:
        """Test that invalid arguments cause exit"""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2

    @patch("mistmcp.__main__.start")
    def test_main_custom_host_and_port(self, mock_start) -> None:
        """Test main with custom host and port"""
        with patch(
            "sys.argv",
            [
                "mistmcp",
                "--transport",
                "http",
                "--host",
                "0.0.0.0",
                "--port",
                "9000",
            ],
        ):
            main()

        mock_start.assert_called_once_with(
            "http", ToolLoadingMode.ALL, [], "0.0.0.0", 9000, False
        )
