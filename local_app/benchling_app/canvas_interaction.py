"""
Canvas interaction handlers for Seqera Platform integration
"""
import re
from urllib.parse import quote

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
from local_app.benchling_app.views.canvas_initialize import input_blocks
from local_app.benchling_app.views.run_preview import render_preview_canvas
from local_app.benchling_app.views.completed import render_completed_canvas

from benchling_sdk.models.webhooks.v0 import CanvasInteractionWebhookV2
from local_app.lib.seqera_platform import (
    get_pipeline_runs,
    get_pipeline_run_details
)
from local_app.benchling_app.views.constants import (
    GET_WORKFLOWS_BUTTON_ID,
    GET_PIPELINE_RUN_BUTTON_ID,
    ADD_TO_NOTEBOOK_BUTTON_ID,
    CANCEL_DETAIL_BUTTON_ID,
    CANCEL_BUTTON_ID,
    SEARCH_TEXT_ID,
    WID_KEY,
    WORKFLOW_ID_KEY
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

    # Check if it's add to notebook button (format: "add_to_notebook_button_{workflowId}")
    if canvas_interaction.button_id and canvas_interaction.button_id.startswith(ADD_TO_NOTEBOOK_BUTTON_ID + "_"):
        return handle_add_to_notebook(app, canvas_interaction)

    # Handle cancel button to return to landing page (from detail view)
    if canvas_interaction.button_id == CANCEL_DETAIL_BUTTON_ID:
        return handle_cancel_detail(app, canvas_interaction)

    # Handle cancel button from runs list (format: "cancel_button_{i}")
    if canvas_interaction.button_id and canvas_interaction.button_id.startswith(CANCEL_BUTTON_ID + "_"):
        return handle_cancel_detail(app, canvas_interaction)

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
    canvas_id = canvas_interaction.canvas_id

    with app.create_session_context("Search Pipeline Runs", timeout_seconds=20) as session:
        session.attach_canvas(canvas_id)

        try:
            from benchling_sdk.models import AppSessionMessageCreate, AppSessionMessageStyle, AppSessionUpdateStatus

            # Extract input values from canvas by fetching the current canvas state
            current_canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
            canvas_builder_temp = CanvasBuilder.from_canvas(current_canvas)
            canvas_inputs = canvas_builder_temp.inputs_to_dict_single_value()
            sanitized_inputs = _validate_and_sanitize_inputs(canvas_inputs)

            # Get search text if provided
            search_text = sanitized_inputs[SEARCH_TEXT_ID]

            # Validate that search text is provided
            if not search_text:
                raise AppUserFacingError("Please enter a pipeline name to search for")

            # Fetch pipeline runs from Seqera with search filter
            runs = get_pipeline_runs(app, search_query=search_text)

            # Build canvas and render runs (or error if no runs found)
            canvas_builder = CanvasBuilder(
                app_id=app.id,
                feature_id=canvas_interaction.feature_id
            )

            success = render_preview_canvas(runs, canvas_id, canvas_builder, session, search_text)

            # Close session with success message only if runs were found
            # Note: render_preview_canvas handles closing session with info message if no runs
            if success:
                search_msg = f" matching '{search_text}'" if search_text else ""
                session.close_session(
                    AppSessionUpdateStatus.SUCCEEDED,
                    messages=[
                        AppSessionMessageCreate(
                            f"Found {len(runs)} pipeline run(s){search_msg}",
                            style=AppSessionMessageStyle.SUCCESS,
                        ),
                    ],
                )

        except AppUserFacingError:
            raise
        except Exception as e:
            raise AppUserFacingError(f"Error fetching workflows: {str(e)}")

    return AppCanvasUpdate()


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
    canvas_id = canvas_interaction.canvas_id

    with app.create_session_context("Load Pipeline Run Details", timeout_seconds=20) as session:
        session.attach_canvas(canvas_id)

        try:
            from benchling_sdk.models import AppSessionMessageCreate, AppSessionMessageStyle, AppSessionUpdateStatus

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

            # Extract and format labels
            labels_array = workflow_details.get('labels', [])
            filtered_labels = []
            if isinstance(labels_array, list):
                for label in labels_array:
                    label_name = label.get("name", "")
                    if label_name not in ["owner", "workspace"]:
                        label_value = label.get("value", "")
                        filtered_labels.append(f"{label_name}:{label_value}")

            labels_string = ", ".join(filtered_labels) if filtered_labels else "None"

            # Format the details as markdown
            details_md = f"""## Pipeline Run Details\n
---\n
**Run Name:** {workflow_details.get('runName', 'N/A')}\n\n
**Workflow ID:** {workflow_details.get('id', 'N/A')}\n\n
**Pipeline:** {workflow_details.get('projectName', 'N/A')}\n
---\n
**Start Time:** {workflow_details.get('start', 'N/A')}\n\n
**Complete Time:** {workflow_details.get('complete', 'N/A')}\n\n
**Duration:** {workflow_details.get('duration', 'N/A')}\n\n
**Launched by:** {workflow_details.get('userName', 'N/A')}\n\n
**Status:** {workflow_details.get('status', 'N/A')}\n\n
**Labels:** {labels_string}\n\n
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

            # Add action buttons with workflow ID encoded
            canvas_builder.blocks.append([
                ButtonUiBlock(
                    id=f"{ADD_TO_NOTEBOOK_BUTTON_ID}_{workflow_id}",
                    type=ButtonUiBlockType.BUTTON,
                    text="Add to notebook"
                )
            ])

            canvas_builder.blocks.append([
                ButtonUiBlock(
                    id=CANCEL_DETAIL_BUTTON_ID,
                    type=ButtonUiBlockType.BUTTON,
                    text="Cancel"
                )
            ])

            # Update the canvas
            app.benchling.apps.update_canvas(
                canvas_id,
                canvas_builder.to_update()
            )

            # Close session with success message
            run_name = workflow_details.get('runName', 'pipeline run')
            session.close_session(
                AppSessionUpdateStatus.SUCCEEDED,
                messages=[
                    AppSessionMessageCreate(
                        f"Loaded details for {run_name}",
                        style=AppSessionMessageStyle.SUCCESS,
                    ),
                ],
            )

        except AppUserFacingError:
            raise
        except Exception as e:
            raise AppUserFacingError(f"Error fetching pipeline run details: {str(e)}")

    return AppCanvasUpdate()


def handle_cancel_detail(
    app: App, canvas_interaction: CanvasInteractionWebhookV2
) -> AppCanvasUpdate:
    """
    Handle cancel button click - return to the landing page.

    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event

    Returns:
        AppCanvasUpdate with landing page
    """
    from local_app.benchling_app.views.canvas_initialize import input_blocks

    canvas_builder = CanvasBuilder(
        app_id=app.id,
        feature_id=canvas_interaction.feature_id
    )

    canvas_builder.blocks.append(input_blocks())

    # Update the canvas
    app.benchling.apps.update_canvas(
        canvas_interaction.canvas_id,
        canvas_builder.to_update()
    )

    return AppCanvasUpdate()


def handle_add_to_notebook(
    app: App, canvas_interaction: CanvasInteractionWebhookV2
) -> AppCanvasUpdate:
    """
    Handle 'Add to notebook' button click - sync workflow run to Benchling.

    Args:
        app: Benchling App instance
        canvas_interaction: The canvas interaction webhook event

    Returns:
        AppCanvasUpdate with success message
    """
    canvas_id = canvas_interaction.canvas_id

    with app.create_session_context("Add Workflow to Notebook", timeout_seconds=20) as session:
        session.attach_canvas(canvas_id)

        try:
            # Extract workflow ID from button ID (format: "add_to_notebook_button_{workflowId}")
            button_id = canvas_interaction.button_id
            if not button_id or not button_id.startswith(ADD_TO_NOTEBOOK_BUTTON_ID + "_"):
                raise AppUserFacingError("Invalid button ID format")

            workflow_id = button_id[len(ADD_TO_NOTEBOOK_BUTTON_ID) + 1:]

            if not workflow_id:
                raise AppUserFacingError("Could not extract workflow ID from button")

            # Fetch workflow details
            workflow_details = get_pipeline_run_details(app, workflow_id)

            if not workflow_details:
                raise AppUserFacingError(f"Could not find workflow: {workflow_id}")

            # Get configuration
            workflow_schema_id = app.config_store.config_by_path(["workflowSchema"]).value()
            sync_folder_id = app.config_store.config_by_path(["syncFolder"]).value()

            if not workflow_schema_id or not sync_folder_id:
                raise AppUserFacingError(
                    "Missing configuration: workflowSchema or syncFolder not configured"
                )

            # Extract and format labels
            labels_array = workflow_details.get('labels', [])
            filtered_labels = []
            if isinstance(labels_array, list):
                for label in labels_array:
                    label_name = label.get("name", "")
                    if label_name not in ["owner", "workspace"]:
                        label_value = label.get("value", "")
                        filtered_labels.append(f"{label_name}:{label_value}")

            labels_string = ", ".join(filtered_labels) if filtered_labels else ""

            # Create entry in Benchling
            from benchling_sdk.models import (
                EntryCreate,
                AppSessionMessageCreate,
                AppSessionMessageStyle,
                AppSessionUpdateStatus
            )
            from benchling_sdk.apps.status.helpers import ref

            entry_name = workflow_details.get('runName', 'Unknown Run')

            entry = EntryCreate(
                name=entry_name,
                schema_id=workflow_schema_id,
                folder_id=sync_folder_id,
                fields={
                    "workflowId": {"value": workflow_details.get('id', '')},
                    "runName": {"value": workflow_details.get('runName', '')},
                    "status": {"value": workflow_details.get('status', '')},
                    "projectName": {"value": workflow_details.get('projectName', '')},
                    "startTime": {"value": workflow_details.get('start', '')},
                    "ownerId": {"value": workflow_details.get('userName', '')},
                    "labels": {"value": labels_string}
                }
            )

            created_entry = app.benchling.entries.create(entry)

            # Show success message
            canvas_builder = CanvasBuilder(
                app_id=app.id,
                feature_id=canvas_interaction.feature_id
            )

            success_msg = f"""## Success!

Workflow run **{entry_name}** has been added to your notebook.

**Entry ID:** {created_entry.id}
"""

            canvas_builder.blocks.append([
                MarkdownUiBlock(
                    id="success_message",
                    type=MarkdownUiBlockType.MARKDOWN,
                    value=success_msg
                )
            ])

            canvas_builder.blocks.append([
                ButtonUiBlock(
                    id=GET_WORKFLOWS_BUTTON_ID,
                    type=ButtonUiBlockType.BUTTON,
                    text="Search more runs"
                )
            ])

            # Update the canvas
            app.benchling.apps.update_canvas(
                canvas_id,
                canvas_builder.to_update()
            )

            # Close session with success message using ref() for clickable entry chip
            session.close_session(
                AppSessionUpdateStatus.SUCCEEDED,
                messages=[
                    AppSessionMessageCreate(
                        f"Created workflow entry {ref(created_entry)} in Benchling!",
                        style=AppSessionMessageStyle.SUCCESS,
                    ),
                ],
            )

        except AppUserFacingError:
            raise
        except Exception as e:
            raise AppUserFacingError(f"Error adding workflow to notebook: {str(e)}")

    return AppCanvasUpdate()


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
    

def _validate_and_sanitize_inputs(inputs: dict[str, str]) -> dict[str, str]:
    sanitized_inputs = {}
    if not inputs[SEARCH_TEXT_ID]:
        # AppFacingUserError is a special error that will propagate the error message as-is back to the user
        # via the App's session and end control flow
        raise AppUserFacingError("Please enter a workflow name to search for")
    if not re.match("^[a-zA-Z\\d\\s\\-]+$", inputs[SEARCH_TEXT_ID]):
        raise AppUserFacingError("The workflow name can only contain letters, numbers, spaces, and hyphens")
    sanitized_inputs[SEARCH_TEXT_ID] = quote(inputs[SEARCH_TEXT_ID])
    return sanitized_inputs