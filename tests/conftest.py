"""Test configuration and fixtures for mistmcp tests"""

from unittest.mock import Mock

import pytest

from mistmcp.config import ServerConfig, ToolLoadingMode


@pytest.fixture
def mock_mcp_instance():
    """Create a mock MCP instance for testing"""
    mock = Mock()
    mock.tool = Mock(return_value=lambda func: func)
    mock.get_tools = Mock(return_value={})
    mock.get_tool = Mock()
    return mock


@pytest.fixture
def basic_config():
    """Create a basic server configuration for testing"""
    return ServerConfig(
        tool_loading_mode=ToolLoadingMode.MANAGED, tool_categories=[], debug=False
    )


@pytest.fixture
def all_config():
    """Create an all mode server configuration for testing"""
    return ServerConfig(
        tool_loading_mode=ToolLoadingMode.ALL, tool_categories=[], debug=False
    )


@pytest.fixture
def managed_config():
    """Create a managed mode server configuration for testing"""
    return ServerConfig(
        tool_loading_mode=ToolLoadingMode.MANAGED,
        debug=False,
    )


@pytest.fixture
def mock_http_request():
    """Create a mock HTTP request for testing"""
    mock_request = Mock()
    mock_request.client = Mock()
    mock_request.client.host = "127.0.0.1"
    mock_request.client.port = 8080
    mock_request.query_params = {}
    mock_request.headers = {}
    return mock_request
