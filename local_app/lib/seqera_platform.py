"""
Functions for interacting with Seqera Platform API
"""
import os
from typing import Optional

import requests
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.types import ManifestMessageCreate, ManifestMessageKind
from benchling_sdk.helpers.serialization_helpers import fields


def get_seqera_config(app: App) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get Seqera Platform configuration from app config.
    
    Returns:
        Tuple of (api_endpoint, platform_token, workspace_id)
    """
    seqera_endpoint = app.app_config_item("seqera_api_endpoint")
    seqera_token = app.app_config_item("seqera_platform_token")
    workspace_id = app.app_config_item("workspaceId")
    
    return seqera_endpoint, seqera_token, workspace_id


def get_pipeline_runs(app: App, workspace_id: Optional[str] = None) -> list[dict]:
    """
    Fetch pipeline runs from Seqera Platform API.
    
    Args:
        app: Benchling App instance
        workspace_id: Optional workspace ID to filter runs (overrides config)
        
    Returns:
        List of pipeline run dictionaries with 'id', 'runName', 'workflowId', 'status'
    """
    seqera_endpoint, seqera_token, config_workspace_id = get_seqera_config(app)
    
    if not seqera_endpoint or not seqera_token:
        app.messages.create(
            ManifestMessageCreate(
                message="Seqera Platform configuration is missing. Please configure 'Seqera API endpoint' and 'Seqera Platform token' in app settings.",
                kind=ManifestMessageKind.ERROR,
            )
        )
        return []
    
    # Use provided workspace_id if given, otherwise use config value
    workspace_id = workspace_id or config_workspace_id
    
    try:
        # Construct the API URL
        url = f"{seqera_endpoint.rstrip('/')}/workflow"
        
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
        app.messages.create(
            ManifestMessageCreate(
                message=f"Failed to fetch pipeline runs from Seqera Platform: {str(e)}",
                kind=ManifestMessageKind.ERROR,
            )
        )
        return []
    except Exception as e:
        app.messages.create(
            ManifestMessageCreate(
                message=f"Unexpected error fetching pipeline runs: {str(e)}",
                kind=ManifestMessageKind.ERROR,
            )
        )
        return []


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
    seqera_endpoint, seqera_token, _ = get_seqera_config(app)
    
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
        app.messages.create(
            ManifestMessageCreate(
                message=f"Failed to fetch pipeline run details: {str(e)}",
                kind=ManifestMessageKind.ERROR,
            )
        )
        return None