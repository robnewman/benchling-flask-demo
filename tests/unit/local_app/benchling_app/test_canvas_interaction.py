"""Tests for canvas_interaction module."""
from unittest.mock import MagicMock, patch

import pytest

from local_app.benchling_app.canvas_interaction import (
    handle_add_to_notebook,
    handle_cancel_detail,
    handle_cancel_to_landing,
    handle_get_pipeline_run,
    handle_get_workflows,
    route_interaction_webhook,
)


@pytest.fixture
def mock_app():
    """Create a mock Benchling App instance."""
    app = MagicMock()
    app.id = "test_app_id"
    app.benchling.apps.get_canvas_by_id.return_value = MagicMock(data={})
    app.benchling.apps.update_canvas.return_value = None
    app.config_store.config_by_path.return_value.value.return_value = "test_value"
    return app


@pytest.fixture
def mock_canvas_interaction():
    """Create a mock canvas interaction webhook."""
    interaction = MagicMock()
    interaction.canvas_id = "test_canvas_id"
    interaction.feature_id = "test_feature_id"
    interaction.button_id = None
    return interaction


class TestRouteInteractionWebhook:
    """Tests for route_interaction_webhook function."""

    def test_route_get_workflows_button(self, mock_app, mock_canvas_interaction):
        """Test routing to get workflows handler."""
        mock_canvas_interaction.button_id = "get_workflows_button"

        with patch("local_app.benchling_app.canvas_interaction.handle_get_workflows") as mock_handler:
            route_interaction_webhook(mock_app, mock_canvas_interaction)
            mock_handler.assert_called_once_with(mock_app, mock_canvas_interaction)

    def test_route_pipeline_run_button(self, mock_app, mock_canvas_interaction):
        """Test routing to get pipeline run handler."""
        mock_canvas_interaction.button_id = "get_pipeline_run_button_123"

        with patch("local_app.benchling_app.canvas_interaction.handle_get_pipeline_run") as mock_handler:
            route_interaction_webhook(mock_app, mock_canvas_interaction)
            mock_handler.assert_called_once_with(mock_app, mock_canvas_interaction)

    def test_route_add_to_notebook_button(self, mock_app, mock_canvas_interaction):
        """Test routing to add to notebook handler."""
        mock_canvas_interaction.button_id = "add_to_notebook_button_123"

        with patch("local_app.benchling_app.canvas_interaction.handle_add_to_notebook") as mock_handler:
            route_interaction_webhook(mock_app, mock_canvas_interaction)
            mock_handler.assert_called_once_with(mock_app, mock_canvas_interaction)

    def test_route_cancel_detail_button(self, mock_app, mock_canvas_interaction):
        """Test routing to cancel detail handler."""
        mock_canvas_interaction.button_id = "cancel_detail_button"

        with patch("local_app.benchling_app.canvas_interaction.handle_cancel_detail") as mock_handler:
            route_interaction_webhook(mock_app, mock_canvas_interaction)
            mock_handler.assert_called_once_with(mock_app, mock_canvas_interaction)

    def test_route_cancel_button(self, mock_app, mock_canvas_interaction):
        """Test routing to cancel landing handler."""
        mock_canvas_interaction.button_id = "cancel_button"

        with patch("local_app.benchling_app.canvas_interaction.handle_cancel_to_landing") as mock_handler:
            route_interaction_webhook(mock_app, mock_canvas_interaction)
            mock_handler.assert_called_once_with(mock_app, mock_canvas_interaction)

    def test_route_no_handler(self, mock_app, mock_canvas_interaction):
        """Test routing with no matching handler returns empty update."""
        mock_canvas_interaction.button_id = "unknown_button"

        result = route_interaction_webhook(mock_app, mock_canvas_interaction)
        assert result is not None


class TestHandleGetWorkflows:
    """Tests for handle_get_workflows function."""

    @patch("local_app.benchling_app.canvas_interaction.get_pipeline_runs")
    @patch("local_app.benchling_app.canvas_interaction.render_preview_canvas")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_get_workflows_success(
        self, mock_builder, mock_render, mock_get_runs, mock_app, mock_canvas_interaction
    ):
        """Test successful workflow retrieval."""
        mock_app.benchling.apps.get_canvas_by_id.return_value.data = {"search_text": "test"}
        mock_get_runs.return_value = [{"runName": "test_run"}]
        mock_render.return_value = True

        mock_canvas_builder = MagicMock()
        mock_canvas_builder.inputs_to_dict_single_value.return_value = {"search_text": "test"}
        mock_builder.from_canvas.return_value = mock_canvas_builder

        result = handle_get_workflows(mock_app, mock_canvas_interaction)

        mock_get_runs.assert_called_once()
        mock_render.assert_called_once()
        assert result is not None


class TestHandleGetPipelineRun:
    """Tests for handle_get_pipeline_run function."""

    @patch("local_app.benchling_app.canvas_interaction.get_pipeline_run_details")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_get_pipeline_run_uploads_config(
        self, mock_builder, mock_get_details, mock_app, mock_canvas_interaction
    ):
        """Test that pipeline params are uploaded as a JSON blob."""
        mock_canvas_interaction.button_id = "get_pipeline_run_button_abc123"
        mock_get_details.return_value = {
            "id": "abc123",
            "runName": "test_run",
            "status": "succeeded",
            "projectName": "nf-core/rnaseq",
            "start": "2024-01-01",
            "complete": "2024-01-02",
            "duration": "1h",
            "userName": "user1",
            "labels": [],
            "params": {"input": "s3://bucket/data", "outdir": "s3://bucket/results"},
        }

        mock_blob = MagicMock()
        mock_blob.id = "blob_123"
        mock_app.benchling.blobs.create_from_bytes.return_value = mock_blob

        mock_blob_url = MagicMock()
        mock_blob_url.download_url = "https://benchling.com/blobs/blob_123/download"
        mock_app.benchling.blobs.download_url.return_value = mock_blob_url

        mock_canvas_builder = MagicMock()
        mock_builder.return_value = mock_canvas_builder

        handle_get_pipeline_run(mock_app, mock_canvas_interaction)

        mock_app.benchling.blobs.create_from_bytes.assert_called_once()
        call_args = mock_app.benchling.blobs.create_from_bytes.call_args
        assert call_args.kwargs["name"] == "abc123.json"
        assert call_args.kwargs["mime_type"] == "application/json"
        mock_app.benchling.blobs.download_url.assert_called_once_with("blob_123")

    @patch("local_app.benchling_app.canvas_interaction.get_pipeline_run_details")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_get_pipeline_run_no_params(
        self, mock_builder, mock_get_details, mock_app, mock_canvas_interaction
    ):
        """Test that no blob upload occurs when params is empty."""
        mock_canvas_interaction.button_id = "get_pipeline_run_button_abc123"
        mock_get_details.return_value = {
            "id": "abc123",
            "runName": "test_run",
            "status": "succeeded",
            "projectName": "nf-core/rnaseq",
            "start": "2024-01-01",
            "complete": "2024-01-02",
            "duration": "1h",
            "userName": "user1",
            "labels": [],
        }

        mock_canvas_builder = MagicMock()
        mock_builder.return_value = mock_canvas_builder

        handle_get_pipeline_run(mock_app, mock_canvas_interaction)

        mock_app.benchling.blobs.create_from_bytes.assert_not_called()

    @patch("local_app.benchling_app.canvas_interaction.get_pipeline_run_details")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_get_pipeline_run_blob_upload_failure(
        self, mock_builder, mock_get_details, mock_app, mock_canvas_interaction
    ):
        """Test that blob upload failure doesn't crash the detail view."""
        mock_canvas_interaction.button_id = "get_pipeline_run_button_abc123"
        mock_get_details.return_value = {
            "id": "abc123",
            "runName": "test_run",
            "status": "succeeded",
            "projectName": "nf-core/rnaseq",
            "start": "2024-01-01",
            "complete": "2024-01-02",
            "duration": "1h",
            "userName": "user1",
            "labels": [],
            "params": {"input": "s3://bucket/data"},
        }

        mock_app.benchling.blobs.create_from_bytes.side_effect = Exception("Upload failed")

        mock_canvas_builder = MagicMock()
        mock_builder.return_value = mock_canvas_builder

        # Should not raise - blob upload failure is handled gracefully
        result = handle_get_pipeline_run(mock_app, mock_canvas_interaction)
        assert result is not None

    @patch("local_app.benchling_app.canvas_interaction.get_org_and_workspace_ids")
    @patch("local_app.benchling_app.canvas_interaction.get_seqera_config")
    @patch("local_app.benchling_app.canvas_interaction.download_workflow_report")
    @patch("local_app.benchling_app.canvas_interaction.get_pipeline_run_details")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_get_pipeline_run_uploads_reports(
        self, mock_builder, mock_get_details, mock_download_report, mock_seqera_config, mock_ids, mock_app, mock_canvas_interaction
    ):
        """Test that each report is downloaded via Seqera content redirect API and uploaded as a blob."""
        mock_canvas_interaction.button_id = "get_pipeline_run_button_abc123"
        mock_get_details.return_value = {
            "id": "abc123",
            "runName": "test_run",
            "status": "succeeded",
            "projectName": "nf-core/rnaseq",
            "start": "2024-01-01",
            "complete": "2024-01-02",
            "duration": "1h",
            "userName": "user1",
            "labels": [],
            "reports": [
                {
                    "display": "Gene counts",
                    "mimeType": "text/tab-separated-values",
                    "path": "0/salmon.merged.gene_counts.tsv",
                    "fileName": "salmon.merged.gene_counts.tsv",
                    "externalPath": "s3://bucket/results/salmon.merged.gene_counts.tsv",
                    "size": 3761,
                },
                {
                    "display": "MultiQC Report",
                    "mimeType": "text/html",
                    "path": "1/multiqc_report.html",
                    "fileName": "multiqc_report.html",
                    "externalPath": "s3://bucket/results/multiqc_report.html",
                    "size": 12345,
                },
            ],
        }

        # Mock workspace resolution (done once before report loop)
        mock_seqera_config.return_value = ("https://api.seqera.io", "token", "org", "ws", None)
        mock_ids.return_value = ("1", "10")

        # Mock downloading report content via Seqera content redirect API
        mock_download_report.return_value = b"report file content"

        mock_blob = MagicMock()
        mock_blob.id = "blob_456"
        mock_app.benchling.blobs.create_from_bytes.return_value = mock_blob

        mock_blob_url = MagicMock()
        mock_blob_url.download_url = "https://benchling.com/blobs/blob_456/download"
        mock_app.benchling.blobs.download_url.return_value = mock_blob_url

        mock_canvas_builder = MagicMock()
        mock_builder.return_value = mock_canvas_builder

        handle_get_pipeline_run(mock_app, mock_canvas_interaction)

        # Verify reports were downloaded via content redirect API with path and pre-resolved workspace_id
        assert mock_download_report.call_count == 2
        mock_download_report.assert_any_call(mock_app, "abc123", "0/salmon.merged.gene_counts.tsv", workspace_id="10")
        mock_download_report.assert_any_call(mock_app, "abc123", "1/multiqc_report.html", workspace_id="10")

        # Verify blobs uploaded with correct filenames and mime types
        assert mock_app.benchling.blobs.create_from_bytes.call_count == 2
        call_args_list = mock_app.benchling.blobs.create_from_bytes.call_args_list
        assert call_args_list[0].kwargs["name"] == "salmon.merged.gene_counts.tsv"
        assert call_args_list[0].kwargs["mime_type"] == "text/tab-separated-values"
        assert call_args_list[1].kwargs["name"] == "multiqc_report.html"
        assert call_args_list[1].kwargs["mime_type"] == "text/html"


class TestHandleCancelToLanding:
    """Tests for handle_cancel_to_landing function."""

    @patch("local_app.benchling_app.canvas_interaction.input_blocks")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_cancel_to_landing(
        self, mock_builder, mock_input_blocks, mock_app, mock_canvas_interaction
    ):
        """Test cancel to landing page."""
        mock_input_blocks.return_value = []
        mock_canvas_builder = MagicMock()
        mock_builder.return_value = mock_canvas_builder

        result = handle_cancel_to_landing(mock_app, mock_canvas_interaction)

        mock_input_blocks.assert_called_once()
        mock_app.benchling.apps.update_canvas.assert_called_once()
        assert result is not None


class TestHandleCancelDetail:
    """Tests for handle_cancel_detail function."""

    @patch("local_app.benchling_app.canvas_interaction.input_blocks")
    @patch("local_app.benchling_app.canvas_interaction.CanvasBuilder")
    def test_handle_cancel_detail_no_stored_search(
        self, mock_builder, mock_input_blocks, mock_app, mock_canvas_interaction
    ):
        """Test cancel detail with no stored search text."""
        mock_app.benchling.apps.get_canvas_by_id.return_value.data = {}
        mock_input_blocks.return_value = []
        mock_canvas_builder = MagicMock()
        mock_builder.return_value = mock_canvas_builder
        mock_builder.from_canvas.return_value = mock_canvas_builder

        result = handle_cancel_detail(mock_app, mock_canvas_interaction)

        mock_input_blocks.assert_called_once()
        mock_app.benchling.apps.update_canvas.assert_called_once()
        assert result is not None
