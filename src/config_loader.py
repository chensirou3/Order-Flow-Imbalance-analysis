"""Configuration loader for OFI factor research project."""

from pathlib import Path
from typing import Any, Dict
import yaml


def get_config(config_path: Path = None) -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default 'config/settings.yaml'
        
    Returns:
        Dictionary containing all configuration settings
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path is None:
        # Default to config/settings.yaml relative to project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "settings.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_project_root() -> Path:
    """Get the project root directory.
    
    Returns:
        Path object pointing to project root
    """
    return Path(__file__).parent.parent


def resolve_path(relative_path: str, config: Dict[str, Any] = None) -> Path:
    """Resolve a relative path to absolute path from project root.
    
    Args:
        relative_path: Path relative to project root
        config: Optional config dict (not used currently, for future extension)
        
    Returns:
        Absolute Path object
    """
    project_root = get_project_root()
    return project_root / relative_path

