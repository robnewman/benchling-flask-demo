"""
Canvas interaction handlers for Seqera Platform integration
"""
from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.status.errors import AppUserFacingError
from benchling_sdk.models import AppCanvasUpdate
from benchling_sdk.models.webhooks.v0 import CanvasInteractionWebhookV2
from local_app.lib.seqera_platform import (
    get_pipeline_runs,
    format_pipeline_runs_for_dropdown,
    get_pipeline_run_details
)

# Field ID constants
GET_WORKFLOWS_BUTTON_ID = "get_workflows_button"
WORKFLOW_DROPDOWN_ID = "workflow_dropdown"


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
    Fetches pipeline runs from Seqera Platform and populates the dropdown.
    
    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event
        
    Returns:
        AppCanvasUpdate with updated dropdown options
    """
    try:
        # Fetch pipeline runs from Seqera
        runs = get_pipeline_runs(app)
        
        if not runs:
            raise AppUserFacingError(
                "No pipeline runs found or unable to connect to Seqera Platform."
            )
        
        # Format for dropdown
        dropdown_options = format_pipeline_runs_for_dropdown(runs)
        
        # Build updated canvas with populated dropdown
        canvas_builder = CanvasBuilder()
        
        # Add your canvas sections and fields here
        # This needs to match your canvas structure from manifest.yaml
        canvas_builder.add_dropdown(
            id=WORKFLOW_DROPDOWN_ID,
            label="Select Workflow",
            options=dropdown_options
        )
        
        return AppCanvasUpdate(canvas=canvas_builder.to_dict())
        
    except AppUserFacingError:
        raise
    except Exception as e:
        raise AppUserFacingError(f"Error fetching workflows: {str(e)}")


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