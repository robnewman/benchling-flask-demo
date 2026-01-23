"""
Canvas interaction handlers for Seqera Platform integration
"""
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.types import (
    CanvasInteraction,
    CanvasUpdateResponse,
    FieldDefinitionUpdate,
    ManifestMessageCreate,
    ManifestMessageKind,
)
from local_app.lib.seqera_platform import (
    get_pipeline_runs,
    format_pipeline_runs_for_dropdown,
    get_pipeline_run_details
)

# Field ID constants
GET_WORKFLOWS_BUTTON_ID = "get_workflows_button"
WORKFLOW_DROPDOWN_ID = "workflow_dropdown"


def route_interaction_webhook(app: App, canvas_interaction: CanvasInteraction) -> CanvasUpdateResponse:
    """
    Route canvas interactions to appropriate handlers based on button_id or triggering_field_id.
    
    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction event
        
    Returns:
        CanvasUpdateResponse from the appropriate handler
    """
    # Handle button clicks
    if canvas_interaction.button_id == GET_WORKFLOWS_BUTTON_ID:
        return handle_get_workflows(app, canvas_interaction)
    
    # Handle dropdown selections
    if canvas_interaction.triggering_field_id == WORKFLOW_DROPDOWN_ID:
        return handle_workflow_selection(app, canvas_interaction)
    
    # No handler found, return empty update
    return CanvasUpdateResponse(field_definitions={})


def handle_get_workflows(app: App, canvas_interaction: CanvasInteraction) -> CanvasUpdateResponse:
    """
    Handle the 'Get Workflows' button click.
    Fetches pipeline runs from Seqera Platform and populates the dropdown.
    
    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction event
        
    Returns:
        CanvasUpdateResponse with updated dropdown options
    """
    try:
        # Fetch pipeline runs from Seqera
        runs = get_pipeline_runs(app)
        
        if not runs:
            app.messages.create(
                ManifestMessageCreate(
                    message="No pipeline runs found or unable to connect to Seqera Platform.",
                    kind=ManifestMessageKind.WARNING,
                )
            )
            # Return empty update
            return CanvasUpdateResponse(
                field_definitions={}
            )
        
        # Format for dropdown
        dropdown_options = format_pipeline_runs_for_dropdown(runs)
        
        # Show success message
        app.messages.create(
            ManifestMessageCreate(
                message=f"Successfully fetched {len(runs)} pipeline runs from Seqera Platform.",
                kind=ManifestMessageKind.SUCCESS,
            )
        )
        
        # Update the workflow dropdown field with the fetched options
        return CanvasUpdateResponse(
            field_definitions={
                WORKFLOW_DROPDOWN_ID: FieldDefinitionUpdate(
                    dropdown_options=dropdown_options
                )
            }
        )
        
    except Exception as e:
        app.messages.create(
            ManifestMessageCreate(
                message=f"Error fetching workflows: {str(e)}",
                kind=ManifestMessageKind.ERROR,
            )
        )
        return CanvasUpdateResponse(
            field_definitions={}
        )


def handle_workflow_selection(app: App, canvas_interaction: CanvasInteraction) -> CanvasUpdateResponse:
    """
    Handle when a user selects a workflow from the dropdown.
    
    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction event
        
    Returns:
        CanvasUpdateResponse with any field updates based on the selection
    """
    # Get the selected workflow ID from the interaction
    selected_workflow_id = canvas_interaction.field_values.get(WORKFLOW_DROPDOWN_ID)
    
    if not selected_workflow_id:
        return CanvasUpdateResponse(field_definitions={})
    
    try:
        # Fetch details about the selected workflow
        workflow_details = get_pipeline_run_details(app, selected_workflow_id)
        
        if workflow_details:
            app.messages.create(
                ManifestMessageCreate(
                    message=f"Selected workflow: {workflow_details.get('runName', selected_workflow_id)}",
                    kind=ManifestMessageKind.INFO,
                )
            )
        
        # You can update other fields based on the selection here
        # For example, populate additional detail fields with workflow information
        return CanvasUpdateResponse(field_definitions={})
        
    except Exception as e:
        app.messages.create(
            ManifestMessageCreate(
                message=f"Error loading workflow details: {str(e)}",
                kind=ManifestMessageKind.ERROR,
            )
        )
        return CanvasUpdateResponse(field_definitions={})