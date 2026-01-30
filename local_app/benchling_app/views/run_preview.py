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
    WID_KEY,
    CREATE_BUTTON_ID,
    SEARCH_TEXT_ID,
    GET_PIPELINE_RUN_BUTTON_ID,
    CANCEL_DETAIL_BUTTON_ID,
)
from local_app.lib.pub_chem import image_url


def render_runs_list_canvas(
    runs: list[dict[str, Any]],
    canvas_builder: CanvasBuilder,
) -> CanvasBuilder:
    """
    Render a list of pipeline runs with View Details buttons.

    Args:
        runs: List of pipeline run dictionaries
        canvas_builder: CanvasBuilder to add blocks to

    Returns:
        Updated CanvasBuilder with runs list
    """
    # Add header
    canvas_builder.blocks.append([
        MarkdownUiBlock(
            id="workflow_results_header",
            type=MarkdownUiBlockType.MARKDOWN,
            value="## Pipeline Runs"
        )
    ])

    # Add each run as a markdown block with a button
    for i, run in enumerate(runs[:20]):  # Limit to 20 runs
        workflow_id = run.get('workflowId', '')
        run_name = run.get('runName', 'Unknown')
        project_name = run.get('projectName', 'Unknown')
        status = run.get('status', 'Unknown')
        start_time = run.get('startTime', 'Unknown')
        user_name = run.get('userName', 'Unknown')
        labels = run.get('labels', '')

        # Create run info
        run_info = f"**Run name: {run_name}**\n\n_Pipeline: {project_name}_\n\nLaunched by: {user_name}\n\n**Status: {status}** (started: {start_time})"

        # Add labels if present
        if labels:
            run_info += f"\n\nLabels: {labels}"

        canvas_builder.blocks.append([
            MarkdownUiBlock(
                id=f"run_info_{i}",
                type=MarkdownUiBlockType.MARKDOWN,
                value=run_info
            )
        ])

        # Add button with workflow ID encoded in button ID
        canvas_builder.blocks.append([
            ButtonUiBlock(
                id=f"{GET_PIPELINE_RUN_BUTTON_ID}_{workflow_id}",
                type=ButtonUiBlockType.BUTTON,
                text="View Details"
            )
        ])

    # Add a Cancel button at the end
    canvas_builder.blocks.append([
        ButtonUiBlock(
            id=CANCEL_DETAIL_BUTTON_ID,
            type=ButtonUiBlockType.BUTTON,
            text="Cancel"
        )
    ])

    return canvas_builder


def render_preview_canvas(
    results: list[dict[str, Any]] | None,
    canvas_id: str,
    canvas_builder: CanvasBuilder,
    session: SessionContextManager,
) -> None:
    if results:
        # Just take the first result, as an example
        chemical = results[0]
        # Add the result to the canvas as data that won't be shown to the user but can be retrieved later
        canvas_builder = canvas_builder\
            .with_blocks(_preview_blocks(chemical))\
            .with_data({WID_KEY: chemical["cid"]})\
            .with_enabled()
        session.app.benchling.apps.update_canvas(
            canvas_id,
            canvas_builder.to_update(),
        )
    else:
        user_input = canvas_builder.inputs_to_dict()[SEARCH_TEXT_ID]
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
                    f"Couldn't find any chemicals for '{user_input}'",
                    style=AppSessionMessageStyle.INFO,
                ),
            ],
        )


def _preview_blocks(chemical: dict[str, Any]) -> list[UiBlock]:
    return [
        MarkdownUiBlock(
            id="results",
            type=MarkdownUiBlockType.MARKDOWN,
            value="We found the following runs based on your search:",
        ),
        MarkdownUiBlock(
            id="run_preview",
            type=MarkdownUiBlockType.MARKDOWN,
            value=(
                f"**Name**: {chemical['name']}\n\n**Structure**: {chemical['smiles']}"
            ),
        ),
        MarkdownUiBlock(
            id="chemical_image",
            type=MarkdownUiBlockType.MARKDOWN,
            value=f'![{chemical["name"]}]({image_url(chemical["cid"])})',
        ),
        MarkdownUiBlock(
            id="user_prompt",
            type=MarkdownUiBlockType.MARKDOWN,
            value="Would you like to link it in Benchling?",
        ),
        SectionUiBlock(
            id="preview_buttons",
            type=SectionUiBlockType.SECTION,
            children=[
                ButtonUiBlock(
                    id=CREATE_BUTTON_ID,
                    text="Add run",
                    type=ButtonUiBlockType.BUTTON,
                ),
                ButtonUiBlock(
                    id=CANCEL_BUTTON_ID,
                    text="Cancel",
                    type=ButtonUiBlockType.BUTTON,
                ),
            ],
        ),
    ]