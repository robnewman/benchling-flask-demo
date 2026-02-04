"""Tests for run_preview module."""
from unittest.mock import MagicMock

import pytest

from local_app.benchling_app.views.run_preview import (
    _runs_list_blocks,
    render_preview_canvas,
)


@pytest.fixture
def mock_canvas_builder():
    """Create a mock CanvasBuilder instance."""
    builder = MagicMock()
    builder.with_blocks.return_value = builder
    builder.with_data.return_value = builder
    builder.with_enabled.return_value = builder
    builder.to_update.return_value = {}
    return builder


@pytest.fixture
def mock_session():
    """Create a mock session context manager."""
    session = MagicMock()
    session.app.benchling.apps.update_canvas.return_value = None
    session.close_session.return_value = None
    return session


@pytest.fixture
def sample_runs():
    """Create sample pipeline run data."""
    return [
        {
            "workflowId": "workflow_123",
            "runName": "Test Run 1",
            "projectName": "Test Project",
            "status": "SUCCEEDED",
            "startTime": "2024-01-01T00:00:00Z",
            "userName": "test_user",
            "labels": "key1:value1,key2:value2"
        },
        {
            "workflowId": "workflow_456",
            "runName": "Test Run 2",
            "projectName": "Test Project 2",
            "status": "RUNNING",
            "startTime": "2024-01-02T00:00:00Z",
            "userName": "test_user2",
            "labels": ""
        }
    ]


class TestRenderPreviewCanvas:
    """Tests for render_preview_canvas function."""

    def test_render_with_runs(self, mock_canvas_builder, mock_session, sample_runs):
        """Test rendering canvas with pipeline runs."""
        result = render_preview_canvas(
            runs=sample_runs,
            canvas_id="test_canvas",
            canvas_builder=mock_canvas_builder,
            session=mock_session,
            search_text="test"
        )

        assert result is True
        mock_canvas_builder.with_blocks.assert_called_once()
        mock_canvas_builder.with_data.assert_called_once()
        mock_canvas_builder.with_enabled.assert_called_once()
        mock_session.app.benchling.apps.update_canvas.assert_called_once()

    def test_render_with_no_runs(self, mock_canvas_builder, mock_session):
        """Test rendering canvas with no pipeline runs."""
        result = render_preview_canvas(
            runs=None,
            canvas_id="test_canvas",
            canvas_builder=mock_canvas_builder,
            session=mock_session,
            search_text="test"
        )

        assert result is False
        mock_session.close_session.assert_called_once()

    def test_render_with_empty_runs(self, mock_canvas_builder, mock_session):
        """Test rendering canvas with empty runs list."""
        result = render_preview_canvas(
            runs=[],
            canvas_id="test_canvas",
            canvas_builder=mock_canvas_builder,
            session=mock_session,
            search_text="test"
        )

        assert result is False
        mock_session.close_session.assert_called_once()


class TestRunsListBlocks:
    """Tests for _runs_list_blocks function."""

    def test_runs_list_blocks_creates_blocks(self, sample_runs):
        """Test that runs list blocks are created correctly."""
        blocks = _runs_list_blocks(sample_runs)

        assert len(blocks) > 0
        # Should have: back button, header, and for each run: info, button, divider
        # 1 (back) + 1 (header) + (3 * 2 runs) = 8 blocks
        assert len(blocks) == 8

    def test_runs_list_blocks_includes_back_button(self, sample_runs):
        """Test that runs list includes back button."""
        blocks = _runs_list_blocks(sample_runs)

        # First block should be the back button
        first_block = blocks[0]
        assert first_block.id == "cancel_button"
        assert first_block.text == "Back to Search"

    def test_runs_list_blocks_includes_header(self, sample_runs):
        """Test that runs list includes header."""
        blocks = _runs_list_blocks(sample_runs)

        # Second block should be the header
        header_block = blocks[1]
        assert header_block.id == "workflow_results_header"
        assert "Pipeline Runs" in header_block.value

    def test_runs_list_blocks_status_emojis(self, sample_runs):
        """Test that status emojis are included."""
        blocks = _runs_list_blocks(sample_runs)

        # Check that run info blocks contain status emojis
        run_info_blocks = [b for b in blocks if hasattr(b, 'id') and 'run_info_' in b.id]
        assert len(run_info_blocks) == 2

        # First run is SUCCEEDED, should have ✅
        assert "✅" in run_info_blocks[0].value

        # Second run is RUNNING, should have ⚙️
        assert "⚙️" in run_info_blocks[1].value

    def test_runs_list_blocks_with_labels(self):
        """Test that labels are included when present."""
        runs = [{
            "workflowId": "workflow_123",
            "runName": "Test Run",
            "projectName": "Test Project",
            "status": "SUCCEEDED",
            "startTime": "2024-01-01T00:00:00Z",
            "userName": "test_user",
            "labels": "key1:value1"
        }]

        blocks = _runs_list_blocks(runs)
        run_info_blocks = [b for b in blocks if hasattr(b, 'id') and 'run_info_' in b.id]

        assert "key1:value1" in run_info_blocks[0].value

    def test_runs_list_blocks_without_labels(self):
        """Test that labels section is omitted when not present."""
        runs = [{
            "workflowId": "workflow_123",
            "runName": "Test Run",
            "projectName": "Test Project",
            "status": "SUCCEEDED",
            "startTime": "2024-01-01T00:00:00Z",
            "userName": "test_user",
            "labels": ""
        }]

        blocks = _runs_list_blocks(runs)
        run_info_blocks = [b for b in blocks if hasattr(b, 'id') and 'run_info_' in b.id]

        assert "Labels:" not in run_info_blocks[0].value
