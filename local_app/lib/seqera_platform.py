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
    seqera_endpoint = app.app_config_item("seqeraApiEndpoint")
    seqera_token = app.app_config_item("seqeraPlatformToken")
    organization_name = app.app_config_item("organizationName")
    workspace_name = app.app_config_item("workspaceName")
    nxf_xpack_license = app.app_config_item("NXF_XPACK_LICENSE")
    
    return seqera_endpoint, seqera_token, organization_name, workspace_name, nxf_xpack_license


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
        
        # Add workspace filter if available
        params = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        elif organization_name and workspace_name:
            # Construct workspace ID from org and workspace names
            # Format depends on Seqera API - adjust as needed
            params["workspaceId"] = f"{organization_name}/{workspace_name}"
        
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
        # Adjust based on actual Seqera API response structure
        if "workflows" in data:
            runs = data["workflows"]
        else:
            runs = data if isinstance(data, list) else []
        
        # Transform to dropdown-friendly format
        pipeline_runs = []
        for run in runs:
            pipeline_runs.append({
                "id": run.get("id", ""),
                "runName": run.get("runName", run.get("id", "Unknown")),
                "workflowId": run.get("workflowId", ""),
                "status": run.get("status", ""),
                "projectName": run.get("projectName", ""),
                "start": run.get("start", ""),
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