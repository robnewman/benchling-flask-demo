"""
Functions for interacting with Seqera Platform API
"""
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


def get_pipeline_runs(app: App, workspace_id: Optional[str] = None) -> list[dict]:
    """
    Fetch pipeline runs from Seqera Platform API.
    
    Args:
        app: Benchling App instance
        workspace_id: Optional workspace ID to filter runs
        
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

        # Add workspace filter if available
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        
        # Make the API request
        headers = {
            "Authorization": f"Bearer {seqera_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()

        # Extract workflow runs from response
        # The Seqera API returns a "workflows" array
        if "workflows" in data:
            runs = data["workflows"]
        else:
            runs = data if isinstance(data, list) else []

        # Transform to standard format
        pipeline_runs = []
        for run in runs:
            workflow = run.get("workflow", {})
            # Extract fields from the workflow object
            pipeline_runs.append({
                "id": workflow.get("id", ""),
                "workflowId": workflow.get("id", ""),
                "runName": workflow.get("runName", "Unknown"),
                "status": workflow.get("status", ""),
                "projectName": workflow.get("projectName", ""),
                "startTime": workflow.get("start", ""),
                "userName": workflow.get("userName", workflow.get("owner", {}).get("userName", "")),
                "labels": run.get("labels", ""),
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
    seqera_endpoint, seqera_token, _, _, _ = get_seqera_config(app)
    
    if not seqera_endpoint or not seqera_token:
        return None
    
    try:
        url = f"{seqera_endpoint.rstrip('/')}/workflow/{run_id}"
        
        headers = {
            "Authorization": f"Bearer {seqera_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise AppUserFacingError(f"Failed to fetch pipeline run details: {str(e)}")