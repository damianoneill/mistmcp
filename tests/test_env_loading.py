"""Tests for mistmcp.__main__ environment variable loading"""

import os
from unittest.mock import patch

import pytest

from mistmcp.__main__ import load_env_file, load_env_var
from mistmcp.config import ToolLoadingMode, config


class TestLoadEnvFile:
    """Test load_env_file function"""

    def test_load_env_file_with_explicit_path(self, tmp_path) -> None:
        """Test loading .env file with explicit path"""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value\n")

        # Mock environment to not have TEST_VAR initially
        with patch.dict(os.environ, {}, clear=False):
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
            if "ANOTHER_VAR" in os.environ:
                del os.environ["ANOTHER_VAR"]

            # Load the env file
            load_env_file(str(env_file))

            # Check that variables were loaded
            assert os.getenv("TEST_VAR") == "test_value"
            assert os.getenv("ANOTHER_VAR") == "another_value"

    def test_load_env_file_with_tilde_path(self, tmp_path) -> None:
        """Test loading .env file with tilde (~) in path"""
        # Create a temporary .env file in a subdirectory
        env_dir = tmp_path / "test_env"
        env_dir.mkdir()
        env_file = env_dir / ".env"
        env_file.write_text("TILDE_TEST=tilde_value\n")

        # Mock home directory
        with patch("os.path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = str(tmp_path)

            with patch.dict(os.environ, {}, clear=False):
                if "TILDE_TEST" in os.environ:
                    del os.environ["TILDE_TEST"]

                # Test with tilde path
                load_env_file("~/test_env/.env")

                # Verify expanduser was called
                mock_expanduser.assert_called_once_with("~")

                # Check that variable was loaded
                assert os.getenv("TILDE_TEST") == "tilde_value"

    def test_load_env_file_from_mist_env_file_var(self, tmp_path) -> None:
        """Test loading .env file from MIST_ENV_FILE environment variable"""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("ENV_FILE_VAR=env_file_value\n")

        with patch.dict(os.environ, {"MIST_ENV_FILE": str(env_file)}, clear=False):
            if "ENV_FILE_VAR" in os.environ:
                del os.environ["ENV_FILE_VAR"]

            # Call without explicit path (should use MIST_ENV_FILE)
            load_env_file()

            # Check that variable was loaded
            assert os.getenv("ENV_FILE_VAR") == "env_file_value"

    def test_load_env_file_default_behavior(self) -> None:
        """Test loading .env file with default behavior (current directory)"""
        # This test uses the actual load_dotenv default behavior
        with patch("mistmcp.__main__.load_dotenv") as mock_load_dotenv:
            load_env_file()

            # Should call load_dotenv with override=True but no dotenv_path
            mock_load_dotenv.assert_called_once_with(override=True)

    def test_load_env_file_dotenv_import_error(self, tmp_path, capsys) -> None:
        """Test handling of ImportError when dotenv is not available"""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")

        with patch("mistmcp.__main__.load_dotenv", side_effect=ImportError):
            load_env_file(str(env_file))

            # Check that warning was printed
            captured = capsys.readouterr()
            assert "Warning: python-dotenv not installed" in captured.err

    def test_load_env_file_no_file_no_env_var(self) -> None:
        """Test behavior when no file specified and no MIST_ENV_FILE"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("mistmcp.__main__.load_dotenv") as mock_load_dotenv:
                load_env_file()

                # Should still call load_dotenv with default behavior
                mock_load_dotenv.assert_called_once_with(override=True)


class TestLoadEnvVar:
    """Test load_env_var function"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Save original config values
        original_config = {
            "mist_apitoken": config.mist_apitoken,
            "mist_host": config.mist_host,
            "transport_mode": config.transport_mode,
            "tool_loading_mode": config.tool_loading_mode,
            "tool_categories": config.tool_categories.copy(),
            "debug": config.debug,
        }

        yield  # This is where the test runs

        # Restore original config after test
        config.mist_apitoken = original_config["mist_apitoken"]
        config.mist_host = original_config["mist_host"]
        config.transport_mode = original_config["transport_mode"]
        config.tool_loading_mode = original_config["tool_loading_mode"]
        config.tool_categories = original_config["tool_categories"]
        config.debug = original_config["debug"]

    def test_load_env_var_stdio_mode_success(self) -> None:
        """Test loading environment variables for stdio mode with all required vars"""
        test_env = {
            "MIST_APITOKEN": "test-api-token",
            "MIST_HOST": "api.mist.com",
            "MISTMCP_TRANSPORT_MODE": "stdio",
            "MISTMCP_TOOL_LOADING_MODE": "all",
            "MISTMCP_TOOL_CATEGORIES": "orgs,sites,devices",
            "MISTMCP_DEBUG": "true",
        }

        with patch.dict(os.environ, test_env, clear=False):
            (
                transport_mode,
                tool_loading_mode,
                tool_categories,
                mcp_host,
                mcp_port,
                debug,
            ) = load_env_var(
                "stdio",
                ToolLoadingMode.ALL,
                ["orgs", "sites", "devices"],
                None,
                None,
                True,
            )

            assert config.mist_apitoken == "test-api-token"
            assert config.mist_host == "api.mist.com"
            assert transport_mode == "stdio"
            assert tool_loading_mode == ToolLoadingMode.ALL
            assert tool_categories == ["orgs", "sites", "devices"]
            assert debug is True
            assert mcp_host == "127.0.0.1"
            assert mcp_port == 8000

    def test_load_env_var_http_mode(self) -> None:
        """Test loading environment variables for http mode (no required vars)"""
        test_env = {
            "MISTMCP_TRANSPORT_MODE": "http",
            "MISTMCP_TOOL_LOADING_MODE": "custom",
            "MISTMCP_TOOL_CATEGORIES": "orgs,sites",
            "MISTMCP_DEBUG": "false",
            "MISTMCP_HOST": "0.0.0.0",
        }

        with patch.dict(os.environ, test_env, clear=False):
            (
                transport_mode,
                tool_loading_mode,
                tool_categories,
                mcp_host,
                mcp_port,
                debug,
            ) = load_env_var("http", ToolLoadingMode.MANAGED, [], None, None, False)

            assert transport_mode == "http"
            assert tool_loading_mode == ToolLoadingMode.MANAGED
            assert tool_categories == []
            assert debug is False
            assert mcp_host == "0.0.0.0"
            assert mcp_port == 8000

    def test_load_env_var_invalid_tool_loading_mode(self) -> None:
        """Test handling of invalid MISTMCP_TOOL_LOADING_MODE"""
        test_env = {
            "MIST_APITOKEN": "test-token",
            "MIST_HOST": "api.mist.com",
            "MISTMCP_TOOL_LOADING_MODE": "invalid_mode",
        }

        with patch.dict(os.environ, test_env, clear=False):
            _, tool_loading_mode, _, _, _, _ = load_env_var(
                "stdio", None, None, None, None, False
            )

            # Should fallback to ALL when invalid value provided (same as default)
            assert tool_loading_mode == ToolLoadingMode.ALL

    def test_load_env_var_debug_variations(self) -> None:
        """Test different debug flag variations"""
        test_cases = [
            ("true", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("YES", True),
            ("false", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("NO", False),
            ("", False),
        ]

        base_env = {
            "MIST_APITOKEN": "test-token",
            "MIST_HOST": "api.mist.com",
        }

        for debug_value, expected in test_cases:
            test_env = {**base_env, "MISTMCP_DEBUG": debug_value}

            with patch.dict(os.environ, test_env, clear=False):
                _, _, _, _, _, debug = load_env_var(
                    "stdio", None, None, None, None, False
                )
                assert debug == expected, f"Failed for debug_value='{debug_value}'"

    def test_load_env_var_categories_parsing(self) -> None:
        """Test parsing of MISTMCP_TOOL_CATEGORIES"""
        test_cases = [
            ("orgs,sites,devices", ["orgs", "sites", "devices"]),
            ("orgs, sites, devices", ["orgs", "sites", "devices"]),  # With spaces
            (
                " orgs , sites , devices ",
                ["orgs", "sites", "devices"],
            ),  # With extra spaces
            ("orgs", ["orgs"]),  # Single category
            ("", []),  # Empty string
            ("orgs,,sites", ["orgs", "sites"]),  # Empty items filtered out
        ]

        base_env = {
            "MIST_APITOKEN": "test-token",
            "MIST_HOST": "api.mist.com",
        }

        for categories_value, expected in test_cases:
            tool_categories: list[str] = []  # Reset before each test
            test_env = {**base_env, "MISTMCP_TOOL_CATEGORIES": categories_value}

            with patch.dict(os.environ, test_env, clear=False):
                _, _, tool_categories, _, _, _ = load_env_var(
                    "stdio", None, None, None, None, False
                )
                assert tool_categories == expected, (
                    f"Failed for categories='{categories_value}'"
                )

    def test_load_env_var_no_optional_vars(self) -> None:
        """Test loading with only required vars for stdio mode"""
        test_env = {
            "MIST_APITOKEN": "test-token",
            "MIST_HOST": "api.mist.com",
        }

        # Clear optional environment variables
        optional_vars = [
            "MISTMCP_TRANSPORT_MODE",
            "MISTMCP_TOOL_LOADING_MODE",
            "MISTMCP_TOOL_CATEGORIES",
            "MISTMCP_DEBUG",
        ]

        with patch.dict(os.environ, test_env, clear=True):
            # Ensure optional vars are not set
            for var in optional_vars:
                if var in os.environ:
                    del os.environ[var]

            load_env_var("stdio", None, None, None, None, False)

            # Check that required vars were set
            assert config.mist_apitoken == "test-token"
            assert config.mist_host == "api.mist.com"

            # Optional vars should not have changed from their original values
            # (they should keep whatever was set before)

    def test_load_env_var_port_parsing(self) -> None:
        """Test parsing of MISTMCP_PORT environment variable"""
        test_cases = [
            ("8080", 8080),
            ("3000", 3000),
            ("invalid", 8000),  # Should fallback to default
            ("", 8000),  # Should fallback to default
        ]

        base_env = {
            "MIST_APITOKEN": "test-token",
            "MIST_HOST": "api.mist.com",
        }

        for port_value, expected in test_cases:
            test_env = {**base_env, "MISTMCP_PORT": port_value}

            with patch.dict(os.environ, test_env, clear=False):
                _, _, _, _, mcp_port, _ = load_env_var(
                    "stdio", None, None, None, None, False
                )
                assert mcp_port == expected, f"Failed for port='{port_value}'"

    def test_load_env_var_host_and_port_from_env(self) -> None:
        """Test loading host and port from environment variables"""
        test_env = {
            "MIST_APITOKEN": "test-token",
            "MIST_HOST": "api.mist.com",
            "MISTMCP_HOST": "0.0.0.0",
            "MISTMCP_PORT": "9000",
        }

        with patch.dict(os.environ, test_env, clear=False):
            _, _, _, mcp_host, mcp_port, _ = load_env_var(
                "stdio", None, None, None, None, False
            )

            assert mcp_host == "0.0.0.0"
            assert mcp_port == 9000
