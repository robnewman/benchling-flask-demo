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
