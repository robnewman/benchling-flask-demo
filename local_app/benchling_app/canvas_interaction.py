"""
Canvas interaction handlers for Seqera Platform integration
"""
from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.status.errors import AppUserFacingError
from benchling_sdk.models import (
    AppCanvasUpdate,
    MarkdownUiBlock,
    MarkdownUiBlockType,
    ButtonUiBlock,
    ButtonUiBlockType,
)
from benchling_sdk.models.webhooks.v0 import CanvasInteractionWebhookV2
from local_app.lib.seqera_platform import (
    get_pipeline_runs,
    get_pipeline_run_details
)
from local_app.benchling_app.views.constants import (
    GET_WORKFLOWS_BUTTON_ID,
    GET_PIPELINE_RUN_BUTTON_ID,
    WORKFLOW_DROPDOWN_ID
)


def route_interaction_webhook(
    app: App, canvas_interaction: CanvasInteractionWebhookV2
) -> AppCanvasUpdate:
    """
    Route canvas interactions to appropriate handlers based on button_id.

    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event

    Returns:
        AppCanvasUpdate with canvas updates
    """
    # Handle button clicks
    if canvas_interaction.button_id == GET_WORKFLOWS_BUTTON_ID:
        return handle_get_workflows(app, canvas_interaction)

    # Check if it's a pipeline run detail button (format: "get_pipeline_run_button_{workflowId}")
    if canvas_interaction.button_id and canvas_interaction.button_id.startswith(GET_PIPELINE_RUN_BUTTON_ID + "_"):
        return handle_get_pipeline_run(app, canvas_interaction)

    # Handle dropdown selections
    if canvas_interaction.triggering_field_id == WORKFLOW_DROPDOWN_ID:
        return handle_workflow_selection(app, canvas_interaction)

    # No handler found, return empty update
    return AppCanvasUpdate()


def handle_get_workflows(
    app: App, canvas_interaction: CanvasInteractionWebhookV2
) -> AppCanvasUpdate:
    """
    Handle the 'Get Workflows' button click.
    Fetches pipeline runs from Seqera Platform and displays them.

    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event

    Returns:
        AppCanvasUpdate with updated canvas showing pipeline runs
    """
    try:
        # Fetch pipeline runs from Seqera
        runs = get_pipeline_runs(app)

        if not runs:
            raise AppUserFacingError(
                "No pipeline runs found or unable to connect to Seqera Platform."
            )

        # Build updated canvas with list of runs and individual buttons
        canvas_builder = CanvasBuilder(
            app_id=app.id,
            feature_id=canvas_interaction.feature_id
        )

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

            # Create run info
            run_info = f"**{run_name}** [{project_name}]  \nStatus: {status} | Started: {start_time} | Owner: {user_name}"

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

        # Update the canvas
        app.benchling.apps.update_canvas(
            canvas_interaction.canvas_id,
            canvas_builder.to_update()
        )

        return AppCanvasUpdate()

    except AppUserFacingError:
        raise
    except Exception as e:
        raise AppUserFacingError(f"Error fetching workflows: {str(e)}")


def handle_get_pipeline_run(
    app: App, canvas_interaction: CanvasInteractionWebhookV2
) -> AppCanvasUpdate:
    """
    Handle the 'Get pipeline run' button click.
    Fetches details for the selected pipeline run and displays them.

    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event

    Returns:
        AppCanvasUpdate with pipeline run details
    """
    try:
        # Extract workflow ID from button ID (format: "get_pipeline_run_button_{workflowId}")
        button_id = canvas_interaction.button_id
        if not button_id or not button_id.startswith(GET_PIPELINE_RUN_BUTTON_ID + "_"):
            raise AppUserFacingError("Invalid button ID format")

        # Extract the workflow ID part after the button prefix and underscore
        workflow_id = button_id[len(GET_PIPELINE_RUN_BUTTON_ID) + 1:]

        if not workflow_id:
            raise AppUserFacingError("Could not extract workflow ID from button")

        # Fetch detailed information about the workflow
        workflow_details = get_pipeline_run_details(app, workflow_id)

        if not workflow_details:
            raise AppUserFacingError(f"Could not find workflow: {workflow_id}")

        # Format the details as markdown
        details_md = f"""## Pipeline Run Details

**Run Name:** {workflow_details.get('runName', 'N/A')}
**Workflow ID:** {workflow_details.get('id', 'N/A')}
**Status:** {workflow_details.get('status', 'N/A')}
**Project:** {workflow_details.get('projectName', 'N/A')}
**Start Time:** {workflow_details.get('start', 'N/A')}
**Complete Time:** {workflow_details.get('complete', 'N/A')}
**Duration:** {workflow_details.get('duration', 'N/A')}
**Owner:** {workflow_details.get('userName', 'N/A')}
"""

        # Build updated canvas with details
        canvas_builder = CanvasBuilder(
            app_id=app.id,
            feature_id=canvas_interaction.feature_id
        )

        canvas_builder.blocks.append([
            MarkdownUiBlock(
                id="pipeline_run_details",
                type=MarkdownUiBlockType.MARKDOWN,
                value=details_md
            )
        ])

        # Update the canvas
        app.benchling.apps.update_canvas(
            canvas_interaction.canvas_id,
            canvas_builder.to_update()
        )

        return AppCanvasUpdate()

    except AppUserFacingError:
        raise
    except Exception as e:
        raise AppUserFacingError(f"Error fetching pipeline run details: {str(e)}")


def handle_workflow_selection(
    app: App, canvas_interaction: CanvasInteractionWebhookV2
) -> AppCanvasUpdate:
    """
    Handle when a user selects a workflow from the dropdown.
    
    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event
        
    Returns:
        AppCanvasUpdate with any field updates based on the selection
    """
    # Get the selected workflow ID from the interaction
    selected_workflow_id = canvas_interaction.entry.field_value(WORKFLOW_DROPDOWN_ID)
    
    if not selected_workflow_id:
        return AppCanvasUpdate()
    
    try:
        # Fetch details about the selected workflow
        workflow_details = get_pipeline_run_details(app, selected_workflow_id)
        
        if not workflow_details:
            raise AppUserFacingError(f"Could not find workflow: {selected_workflow_id}")
        
        # You can update other fields based on the selection here
        # For now, just return empty update
        return AppCanvasUpdate()
        
    except AppUserFacingError:
        raise
    except Exception as e:
        raise AppUserFacingError(f"Error loading workflow details: {str(e)}")