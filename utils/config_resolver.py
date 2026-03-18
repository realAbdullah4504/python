import json
from typing import Dict, Any

def resolve_json_refs(data: Dict[str, Any], base_path: str = "#") -> Dict[str, Any]:
    """
    Resolve JSON references ($ref) in a configuration dictionary.
    
    Args:
        data: The configuration data containing potential $ref references
        base_path: Base path for resolving relative references
        
    Returns:
        Configuration with all references resolved
    """
    def resolve_ref(ref_path: str, root: Dict[str, Any]) -> Any:
        """Resolve a single JSON reference path"""
        if ref_path.startswith("#/"):
            # JSON Pointer format - navigate through the structure
            parts = ref_path[2:].split("/")
            current = root
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    raise ValueError(f"Cannot resolve reference: {ref_path}")
            return current
        return None
    
    def resolve_recursive(obj: Dict[str, Any], root: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve all references in an object"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    # Resolve the reference and merge/replace
                    resolved = resolve_ref(value, root)
                    if isinstance(resolved, dict):
                        # Deep merge resolved reference with current object (excluding $ref)
                        resolved_copy = resolve_recursive(resolved, root)
                        result.update(resolved_copy)
                    else:
                        result[key] = resolved
                elif isinstance(value, (dict, list)):
                    result[key] = resolve_recursive(value, root)
                else:
                    result[key] = value
            return result
        elif isinstance(obj, list):
            return [resolve_recursive(item, root) for item in obj]
        else:
            return obj
    
    return resolve_recursive(data, data)

def load_config_with_refs(config_path: str) -> Dict[str, Any]:
    """Load configuration and resolve all JSON references"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    return resolve_json_refs(config)

def get_portal_config(portal: Dict[str, Any]) -> Dict[str, Any]:
    """Extract resolved configuration for a specific portal"""
    return portal.get("config", {})
