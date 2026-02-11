"""Tests for seqera_platform module."""
from unittest.mock import MagicMock, patch

import pytest

from local_app.lib.seqera_platform import (
    download_workflow_report,
    get_org_and_workspace_ids,
    get_pipeline_run_details,
    get_pipeline_runs,
    get_seqera_config,
)


@pytest.fixture
def mock_app():
    """Create a mock Benchling App instance."""
    app = MagicMock()
    app.config_store.config_by_path.return_value.value.return_value = "test_value"
    return app


class TestGetSeqeraConfig:
    """Tests for get_seqera_config function."""

    def test_get_seqera_config(self, mock_app):
        """Test getting Seqera configuration."""
        mock_app.config_store.config_by_path.return_value.value.side_effect = [
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        ]

        endpoint, token, org, workspace, license_key = get_seqera_config(mock_app)

        assert endpoint == "https://api.seqera.io"
        assert token == "test_token"
        assert org == "test_org"
        assert workspace == "test_workspace"
        assert license_key == "test_license"


class TestGetOrgAndWorkspaceIds:
    """Tests for get_org_and_workspace_ids function."""

    @patch("local_app.lib.seqera_platform.requests.get")
    def test_get_org_and_workspace_ids_success(self, mock_get, mock_app):
        """Test successfully getting org and workspace IDs."""
        mock_app.config_store.config_by_path.return_value.value.side_effect = [
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        ]

        # Mock user-info response and orgsAndWorkspaces response
        mock_get.return_value.json.side_effect = [
            # First call: user-info
            {
                "user": {
                    "id": 123,
                    "email": "test@example.com"
                }
            },
            # Second call: user/{user_id}/workspaces
            {
                "orgsAndWorkspaces": [
                    {
                        "orgId": 1,
                        "orgName": "test_org",
                        "workspaceId": 10,
                        "workspaceName": "test_workspace"
                    },
                    {
                        "orgId": 2,
                        "orgName": "other_org",
                        "workspaceId": 20,
                        "workspaceName": "other_workspace"
                    }
                ]
            }
        ]
        mock_get.return_value.raise_for_status.return_value = None

        org_id, workspace_id = get_org_and_workspace_ids(mock_app, "test_org", "test_workspace")

        assert org_id == "1"
        assert workspace_id == "10"

    @patch("local_app.lib.seqera_platform.requests.get")
    def test_get_org_and_workspace_ids_org_not_found(self, mock_get, mock_app):
        """Test when organization is not found."""
        mock_app.config_store.config_by_path.return_value.value.side_effect = [
            "https://api.seqera.io",
            "test_token",
            "nonexistent_org",
            "test_workspace",
            "test_license"
        ]

        # Mock user-info and orgsAndWorkspaces response with no matching org/workspace
        mock_get.return_value.json.side_effect = [
            # First call: user-info
            {
                "user": {
                    "id": 123,
                    "email": "test@example.com"
                }
            },
            # Second call: user/{user_id}/workspaces with no matching org
            {
                "orgsAndWorkspaces": [
                    {
                        "orgId": 2,
                        "orgName": "other_org",
                        "workspaceId": 20,
                        "workspaceName": "other_workspace"
                    }
                ]
            }
        ]
        mock_get.return_value.raise_for_status.return_value = None

        org_id, workspace_id = get_org_and_workspace_ids(mock_app, "nonexistent_org", "test_workspace")

        assert org_id is None
        assert workspace_id is None


class TestGetPipelineRuns:
    """Tests for get_pipeline_runs function."""

    @patch("local_app.lib.seqera_platform.get_org_and_workspace_ids")
    @patch("local_app.lib.seqera_platform.get_seqera_config")
    @patch("local_app.lib.seqera_platform.requests.get")
    def test_get_pipeline_runs_success(self, mock_get, mock_config, mock_ids, mock_app):
        """Test successfully getting pipeline runs."""
        mock_config.return_value = (
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        )
        mock_ids.return_value = ("1", "10")

        mock_get.return_value.json.return_value = {
            "workflows": [
                {
                    "workflow": {
                        "id": "123",
                        "runName": "test_run",
                        "projectName": "test_project",
                        "status": "SUCCEEDED"
                    }
                }
            ]
        }
        mock_get.return_value.raise_for_status.return_value = None

        runs = get_pipeline_runs(mock_app, search_query="test")

        assert len(runs) == 1
        assert runs[0]["runName"] == "test_run"
        assert runs[0]["status"] == "SUCCEEDED"

    @patch("local_app.lib.seqera_platform.get_org_and_workspace_ids")
    @patch("local_app.lib.seqera_platform.get_seqera_config")
    @patch("local_app.lib.seqera_platform.requests.get")
    def test_get_pipeline_runs_empty_result(self, mock_get, mock_config, mock_ids, mock_app):
        """Test getting pipeline runs with no results."""
        mock_config.return_value = (
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        )
        mock_ids.return_value = ("1", "10")

        mock_get.return_value.json.return_value = {"workflows": []}
        mock_get.return_value.raise_for_status.return_value = None

        runs = get_pipeline_runs(mock_app, search_query="nonexistent")

        assert runs == []


class TestGetPipelineRunDetails:
    """Tests for get_pipeline_run_details function."""

    @patch("local_app.lib.seqera_platform.get_org_and_workspace_ids")
    @patch("local_app.lib.seqera_platform.get_seqera_config")
    @patch("local_app.lib.seqera_platform.requests.get")
    def test_get_pipeline_run_details_success(self, mock_get, mock_config, mock_ids, mock_app):
        """Test successfully getting pipeline run details."""
        mock_config.return_value = (
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        )
        mock_ids.return_value = ("1", "10")

        mock_get.return_value.json.side_effect = [
            # First call: workflow details
            {
                "workflow": {
                    "id": "123",
                    "runName": "test_run",
                    "projectName": "test_project",
                    "status": "SUCCEEDED",
                    "start": "2024-01-01T00:00:00Z",
                    "complete": "2024-01-01T01:00:00Z",
                    "duration": 3600000,
                    "userName": "test_user",
                    "labels": [
                        {"name": "key1", "value": "value1"},
                        {"name": "owner", "value": "test"}
                    ]
                }
            },
            # Second call: reports
            {
                "reports": [
                    {"display": "Execution Report", "mimeType": "text/html"},
                    {"display": "Timeline Report", "mimeType": "text/html"}
                ]
            }
        ]
        mock_get.return_value.raise_for_status.return_value = None

        details = get_pipeline_run_details(mock_app, "123")

        assert details["id"] == "123"
        assert details["runName"] == "test_run"
        assert details["status"] == "SUCCEEDED"
        assert len(details["reports"]) == 2
        assert details["reports"][0]["display"] == "Execution Report"

    @patch("local_app.lib.seqera_platform.get_org_and_workspace_ids")
    @patch("local_app.lib.seqera_platform.get_seqera_config")
    @patch("local_app.lib.seqera_platform.requests.get")
    def test_get_pipeline_run_details_not_found(self, mock_get, mock_config, mock_ids, mock_app):
        """Test getting details for non-existent run."""
        mock_config.return_value = (
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        )
        mock_ids.return_value = ("1", "10")

        mock_get.return_value.json.side_effect = [
            # First call: empty workflow response
            {},
            # Second call: reports (still attempted)
            {"reports": []}
        ]
        mock_get.return_value.raise_for_status.return_value = None

        details = get_pipeline_run_details(mock_app, "nonexistent")

        assert details.get("reports") == []


class TestDownloadWorkflowReport:
    """Tests for download_workflow_report function."""

    @patch("local_app.lib.seqera_platform.get_org_and_workspace_ids")
    @patch("local_app.lib.seqera_platform.get_seqera_config")
    @patch("local_app.lib.seqera_platform.requests.get")
    def test_download_workflow_report_success(self, mock_get, mock_config, mock_ids, mock_app):
        """Test successfully downloading a report via content redirect endpoint."""
        mock_config.return_value = (
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        )
        mock_ids.return_value = ("1", "10")

        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.content = b"report file content"

        content = download_workflow_report(
            mock_app, "2pQ8hl45laOIwf", "1/salmon.merged.gene_tpm.tsv"
        )

        assert content == b"report file content"
        # Verify the content redirect URL was called correctly
        mock_get.assert_called_once_with(
            "https://api.seqera.io/content/redirect/reports/wsp/10/2pQ8hl45laOIwf/1/salmon.merged.gene_tpm.tsv",
            headers={"Authorization": "Bearer test_token"},
            timeout=30
        )

    @patch("local_app.lib.seqera_platform.get_seqera_config")
    def test_download_workflow_report_no_config(self, mock_config, mock_app):
        """Test download returns None when config is missing."""
        mock_config.return_value = (None, None, None, None, None)

        result = download_workflow_report(mock_app, "wf123", "1/report.tsv")

        assert result is None

    @patch("local_app.lib.seqera_platform.get_org_and_workspace_ids")
    @patch("local_app.lib.seqera_platform.get_seqera_config")
    def test_download_workflow_report_no_workspace(self, mock_config, mock_ids, mock_app):
        """Test download returns None when workspace ID cannot be resolved."""
        mock_config.return_value = (
            "https://api.seqera.io",
            "test_token",
            "test_org",
            "test_workspace",
            "test_license"
        )
        mock_ids.return_value = (None, None)

        result = download_workflow_report(mock_app, "wf123", "1/report.tsv")

        assert result is None
