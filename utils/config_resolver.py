import json
from typing import Dict, Any, Union

def _resolve_json_pointer(ref_path: str, root: Dict[str, Any]) -> Any:
    """Resolve a JSON Pointer path (#/format) in the root object."""
    if not ref_path.startswith("#/"):
        return None
    
    parts = ref_path[2:].split("/")
    current = root
    
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Cannot resolve reference: {ref_path}")
        current = current[part]
    
    return current

def _resolve_dict_references(obj: Dict[str, Any], root: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve references in a dictionary object."""
    result = {}
    
    for key, value in obj.items():
        if key == "$ref" and isinstance(value, str):
            resolved = _resolve_json_pointer(value, root)
            if isinstance(resolved, dict):
                resolved_copy = _resolve_object_recursive(resolved, root)
                result.update(resolved_copy)
            else:
                result[key] = resolved
        elif isinstance(value, dict):
            result[key] = _resolve_dict_references(value, root)
        elif isinstance(value, list):
            result[key] = _resolve_list_references(value, root)
        else:
            result[key] = value
    
    return result

def _resolve_list_references(obj: list, root: Dict[str, Any]) -> list:
    """Resolve references in a list object."""
    return [_resolve_object_recursive(item, root) for item in obj]

def _resolve_object_recursive(obj: Union[Dict, list, Any], root: Dict[str, Any]) -> Union[Dict, list, Any]:
    """Recursively resolve references in an object."""
    if isinstance(obj, dict):
        return _resolve_dict_references(obj, root)
    if isinstance(obj, list):
        return _resolve_list_references(obj, root)
    return obj

def resolve_json_refs(data: Dict[str, Any], base_path: str = "#") -> Dict[str, Any]:
    """
    Resolve JSON references ($ref) in a configuration dictionary.
    
    Args:
        data: The configuration data containing potential $ref references
        base_path: Base path for resolving relative references (currently unused)
        
    Returns:
        Configuration with all references resolved
    """
    return _resolve_object_recursive(data, data)

def load_config_with_refs(config_path: str) -> Dict[str, Any]:
    """Load configuration and resolve all JSON references"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    return resolve_json_refs(config)

def get_portal_config(portal: Dict[str, Any]) -> Dict[str, Any]:
    """Extract resolved configuration for a specific portal"""
    return portal.get("config", {})
