from typing import Any

from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.canvas.types import UiBlock
from benchling_sdk.apps.status.framework import SessionContextManager
from benchling_sdk.models import (
    AppSessionMessageCreate,
    AppSessionMessageStyle,
    AppSessionUpdateStatus,
    ButtonUiBlock,
    ButtonUiBlockType,
    MarkdownUiBlock,
    MarkdownUiBlockType,
    SectionUiBlock,
    SectionUiBlockType,
)

from local_app.benchling_app.views.canvas_initialize import input_blocks
from local_app.benchling_app.views.constants import (
    CANCEL_BUTTON_ID,
    GET_PIPELINE_RUN_BUTTON_ID,
    SEARCH_TEXT_ID,
    WORKFLOW_ID_KEY,
    WID_KEY
)


def render_preview_canvas(
    runs: list[dict[str, Any]] | None,
    canvas_id: str,
    canvas_builder: CanvasBuilder,
    session: SessionContextManager,
    search_text: str = ""
) -> bool:
    """
    Render pipeline runs list with error handling.

    Args:
        runs: List of pipeline run dictionaries or None if no results
        canvas_id: Canvas ID to update
        canvas_builder: CanvasBuilder instance
        session: Session context manager for status messages
        search_text: The search query used (for error messages)

    Returns:
        True if runs were displayed successfully, False if no runs found
    """
    if runs and len(runs) > 0:
        # Display the list of runs
        canvas_builder = canvas_builder\
            .with_blocks(_runs_list_blocks(runs))\
            .with_data({SEARCH_TEXT_ID: search_text})\
            .with_enabled()
        session.app.benchling.apps.update_canvas(
            canvas_id,
            canvas_builder.to_update(),
        )
        return True
    else:
        # Clear the search input and re-enable canvas so user can input a new search
        canvas_builder = canvas_builder.with_blocks(input_blocks()).with_enabled()
        session.app.benchling.apps.update_canvas(
            canvas_id,
            canvas_builder.to_update(),
        )
        session.close_session(
            AppSessionUpdateStatus.SUCCEEDED,
            messages=[
                AppSessionMessageCreate(
                    f"Couldn't find any runs for '{search_text}'",
                    style=AppSessionMessageStyle.INFO,
                ),
            ],
        )
        return False


def _runs_list_blocks(runs: list[dict[str, Any]]) -> list[UiBlock]:
    """Generate UI blocks for displaying a list of pipeline runs."""
    blocks = [
        ButtonUiBlock(
            id=f"{CANCEL_BUTTON_ID}",
            text="Back to Search",
            type=ButtonUiBlockType.BUTTON,
        )
    ]
    blocks.append(
        MarkdownUiBlock(
            id="workflow_results_header",
            type=MarkdownUiBlockType.MARKDOWN,
            value="## Pipeline Runs"
        )
    )

    # Add each run as a markdown block with buttons
    for i, run in enumerate(runs):
        workflow_id = run.get('workflowId', '')
        run_name = run.get('runName', 'Unknown')
        project_name = run.get('projectName', 'Unknown')
        status = run.get('status', 'Unknown')
        start_time = run.get('startTime', 'Unknown')
        user_name = run.get('userName', 'Unknown')
        labels = run.get('labels', '')

        # Create run info with status-specific emoji
        status_lower = status.lower()
        status_emoji_map = {
            'pending': '🕐',      # Clock icon (orange/red)
            'submitted': '⏳',     # Three horizontal dots (orange)
            'running': '⚙️',      # Blue circle for running (animated progress)
            'cached': '🔄',       # Recycle icon (gray)
            'succeeded': '✅',    # Checkmark icon (green)
            'failed': '❌',       # Warning icon (red)
            'aborted': '⛔',      # Cross icon (brown)
            'cancelled': '🚫'     # Stop icon (gray)
        }

        status_emoji = status_emoji_map.get(status_lower, '⚪')  # Default to white circle
        status_display = f"{status_emoji} {status}"

        run_info = f"**Run name: {run_name}**\n\n_Pipeline: {project_name}_\n\nLaunched by: {user_name}\n\n**Status: {status_display}** (started: {start_time})"

        # Add labels if present
        if labels:
            run_info += f"\n\nLabels: {labels}"

        blocks.append(
            MarkdownUiBlock(
                id=f"run_info_{i}",
                type=MarkdownUiBlockType.MARKDOWN,
                value=run_info
            )
        )

        # Add button section with View Details and Cancel buttons
        blocks.append(
            ButtonUiBlock(
                id=f"{GET_PIPELINE_RUN_BUTTON_ID}_{workflow_id}",
                type=ButtonUiBlockType.BUTTON,
                text="View Details"
            )
        )

        # Add horizontal rule divider
        blocks.append(
            MarkdownUiBlock(
                id=f"breakpoint_{i}",
                type=MarkdownUiBlockType.MARKDOWN,
                value="\n---\n"
            )
        )

    return blocks