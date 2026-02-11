"""
Functions for interacting with Seqera Platform API
"""
import logging
from typing import Optional
import requests
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.status.errors import AppUserFacingError


def get_seqera_config(app: App) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Get Seqera Platform configuration from app config.

    Returns:
        Tuple of (api_endpoint, platform_token, organization_name, workspace_name, nxf_xpack_license)
    """
    seqera_endpoint = app.config_store.config_by_path(["seqeraApiEndpoint"]).value()
    seqera_token = app.config_store.config_by_path(["seqeraPlatformToken"]).value()
    organization_name = app.config_store.config_by_path(["organizationName"]).value()
    workspace_name = app.config_store.config_by_path(["workspaceName"]).value()
    nxf_xpack_license = app.config_store.config_by_path(["NXF_XPACK_LICENSE"]).value()

    return seqera_endpoint, seqera_token, organization_name, workspace_name, nxf_xpack_license


def get_org_and_workspace_ids(app: App, organization_name: str, workspace_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Get the organization ID and workspace ID from their names.

    Args:
        app: Benchling App instance
        organization_name: Name of the organization
        workspace_name: Name of the workspace

    Returns:
        Tuple of (organization_id, workspace_id) or (None, None) if not found
    """
    seqera_endpoint, seqera_token, _, _, _ = get_seqera_config(app)

    if not seqera_endpoint or not seqera_token:
        return None, None

    try:
        # First, get the user ID from user-info
        user_info_url = f"{seqera_endpoint.rstrip('/')}/user-info"

        headers = {
            "Authorization": f"Bearer {seqera_token}",
            "Accept": "application/json"
        }

        response = requests.get(user_info_url, headers=headers, timeout=10)
        response.raise_for_status()

        user_info = response.json()
        user_id = user_info.get("user", {}).get("id")

        if not user_id:
            raise AppUserFacingError("Could not retrieve user ID from user-info")

        # Now get all orgs and workspaces the user has access to
        workspaces_url = f"{seqera_endpoint.rstrip('/')}/user/{user_id}/workspaces"

        response = requests.get(workspaces_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Loop through orgsAndWorkspaces to find matching org and workspace names
        orgs_and_workspaces = data.get("orgsAndWorkspaces", [])
        for item in orgs_and_workspaces:
            if (item.get("orgName") == organization_name and
                item.get("workspaceName") == workspace_name):
                org_id = str(item.get("orgId"))
                workspace_id = str(item.get("workspaceId"))
                return org_id, workspace_id

        return None, None

    except requests.exceptions.RequestException as e:
        raise AppUserFacingError(f"Failed to fetch organization and workspace IDs: {str(e)}")


def get_pipeline_runs(app: App, workspace_id: Optional[str] = None, search_query: Optional[str] = None) -> list[dict]:
    """
    Fetch pipeline runs from Seqera Platform API.

    Args:
        app: Benchling App instance
        workspace_id: Optional workspace ID to filter runs
        search_query: Optional search query to filter runs

    Returns:
        List of pipeline run dictionaries with 'id', 'runName', 'workflowId', 'status'
    """
    seqera_endpoint, seqera_token, organization_name, workspace_name, nxf_xpack_license = get_seqera_config(app)

    if not seqera_endpoint or not seqera_token:
        raise AppUserFacingError(
            "Seqera Platform configuration is missing. Please configure 'seqeraApiEndpoint' and 'seqeraPlatformToken' in app settings."
        )

    # Note: nxf_xpack_license available for future use if needed

    try:
        # Construct the API URL
        url = f"{seqera_endpoint.rstrip('/')}/workflow"

        # Resolve workspace ID if not provided
        if not workspace_id and organization_name and workspace_name:
            org_id, workspace_id = get_org_and_workspace_ids(app, organization_name, workspace_name)
            if not workspace_id:
                raise AppUserFacingError(
                    f"Could not find workspace '{workspace_name}' in organization '{organization_name}'"
                )

        # Add parameters for performance and filtering
        params = {
            "offset": 0,
            "max": 25,
            "attributes": "labels,minimal",
            "includeTotalSize": "false"
        }

        if workspace_id:
            params["workspaceId"] = workspace_id

        if search_query:
            params["search"] = search_query
        
        # Make the API request
        headers = {
            "Authorization": f"Bearer {seqera_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        # Debug logging
        logging.info(f"Seqera API search query: {search_query}")
        logging.info(f"Seqera API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict) and "workflows" in data:
            logging.info(f"Number of workflows returned: {len(data['workflows'])}")

        # Extract workflow runs from response
        # The Seqera API returns a "workflows" array
        if "workflows" in data:
            runs = data["workflows"]
        else:
            runs = data if isinstance(data, list) else []

        logging.info(f"Total runs after extraction: {len(runs)}")

        # Transform to standard format
        pipeline_runs = []
        for run in runs:
            workflow = run.get("workflow", {})

            # Extract and format labels, filtering out "owner" and "workspace"
            labels_array = workflow.get("labels", [])
            filtered_labels = []
            if isinstance(labels_array, list):
                for label in labels_array:
                    label_name = label.get("name", "")
                    if label_name not in ["owner", "workspace"]:
                        label_value = label.get("value", "")
                        filtered_labels.append(f"{label_name}:{label_value}")

            labels_string = ", ".join(filtered_labels) if filtered_labels else ""

            # Extract fields from the workflow object
            pipeline_runs.append({
                "id": workflow.get("id", ""),
                "workflowId": workflow.get("id", ""),
                "runName": workflow.get("runName", "Unknown"),
                "status": workflow.get("status", ""),
                "projectName": workflow.get("projectName", ""),
                "startTime": workflow.get("start", ""),
                "userName": workflow.get("userName", workflow.get("owner", {}).get("userName", "")),
                "labels": labels_string,
            })

        return pipeline_runs
        
    except requests.exceptions.RequestException as e:
        raise AppUserFacingError(f"Failed to fetch pipeline runs from Seqera Platform: {str(e)}")
    except Exception as e:
        raise AppUserFacingError(f"Unexpected error fetching pipeline runs: {str(e)}")


def format_pipeline_runs_for_dropdown(pipeline_runs: list[dict]) -> list[dict]:
    """
    Format pipeline runs for use in a Benchling dropdown field.
    
    Args:
        pipeline_runs: List of pipeline run dictionaries
        
    Returns:
        List of dicts with 'value' and 'label' keys for dropdown options
    """
    options = []
    for run in pipeline_runs:
        # Create a descriptive label
        label = f"{run.get('runName', 'Unknown')} ({run.get('status', 'N/A')})"
        if run.get('projectName'):
            label += f" - {run['projectName']}"
        
        options.append({
            "value": run.get("id", ""),
            "label": label
        })
    
    return options


def get_pipeline_run_details(app: App, run_id: str) -> Optional[dict]:
    """
    Fetch detailed information about a specific pipeline run.

    Args:
        app: Benchling App instance
        run_id: Pipeline run ID

    Returns:
        Dictionary with pipeline run details or None if not found
    """
    seqera_endpoint, seqera_token, organization_name, workspace_name, _ = get_seqera_config(app)

    if not seqera_endpoint or not seqera_token:
        return None

    try:
        # Resolve workspace ID
        workspace_id = None
        if organization_name and workspace_name:
            org_id, workspace_id = get_org_and_workspace_ids(app, organization_name, workspace_name)
            if not workspace_id:
                raise AppUserFacingError(
                    f"Could not find workspace '{workspace_name}' in organization '{organization_name}'"
                )

        url = f"{seqera_endpoint.rstrip('/')}/workflow/{run_id}"

        headers = {
            "Authorization": f"Bearer {seqera_token}",
            "Accept": "application/json"
        }

        # Add workspace parameter if available
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Debug: Log the top-level keys to understand structure
        logging.info(f"Pipeline run details response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

        # The response might have the workflow nested inside a "workflow" key
        # Try to extract it, otherwise return as-is
        if isinstance(data, dict) and "workflow" in data:
            workflow_data = data["workflow"]
            logging.info(f"Found nested workflow, keys: {list(workflow_data.keys())}")
        else:
            workflow_data = data

        # Fetch reports for this workflow
        try:
            reports_url = f"{seqera_endpoint.rstrip('/')}/workflow/{run_id}/reports"
            reports_response = requests.get(reports_url, headers=headers, params=params, timeout=10)
            reports_response.raise_for_status()
            reports_data = reports_response.json()
            workflow_data["reports"] = reports_data.get("reports", reports_data)
            logging.info(f"Fetched {len(workflow_data['reports'])} reports for workflow {run_id}")
        except Exception as e:
            logging.warning(f"Failed to fetch reports for workflow {run_id}: {e}")
            workflow_data["reports"] = []

        return workflow_data

    except requests.exceptions.RequestException as e:
        raise AppUserFacingError(f"Failed to fetch pipeline run details: {str(e)}")


def download_workflow_report(app: App, workflow_id: str, report_path: str, workspace_id: Optional[str] = None) -> Optional[bytes]:
    """
    Download a workflow report file via the Seqera Platform content redirect endpoint.

    Uses GET /content/redirect/reports/wsp/{workspaceId}/{workflowId}/{reportPath}
    which returns a redirect to a presigned download URL.

    Args:
        app: Benchling App instance
        workflow_id: The workflow run ID
        report_path: The report's path field (e.g. "1/salmon.merged.gene_tpm.tsv")
        workspace_id: Optional pre-resolved workspace ID to avoid redundant API calls

    Returns:
        Raw bytes of the report file, or None if download fails
    """
    seqera_endpoint, seqera_token, organization_name, workspace_name, _ = get_seqera_config(app)

    if not seqera_endpoint or not seqera_token:
        return None

    # Resolve workspace ID if not provided
    if not workspace_id:
        if organization_name and workspace_name:
            _, workspace_id = get_org_and_workspace_ids(app, organization_name, workspace_name)

    if not workspace_id:
        logging.warning("Could not resolve workspace ID for report download")
        return None

    headers = {
        "Authorization": f"Bearer {seqera_token}",
    }

    url = f"{seqera_endpoint.rstrip('/')}/content/redirect/reports/wsp/{workspace_id}/{workflow_id}/{report_path}"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return response.content