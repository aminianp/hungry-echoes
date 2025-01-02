import yaml
from pathlib import Path
from pulumi import Config

class Settings:
    """
    Shared settings manager for hungry-echoes infrastructure.
    Uses Pulumi Config for project-level settings and YAML for component-specific settings.
    """
    def __init__(self):
        # Get GCP provider config
        self._gcp_config = Config('gcp')
        
        # Load component settings from YAML
        settings_path = Path(__file__).parent / "settings.yaml"
        with open(settings_path, 'r') as f:
            self._settings = yaml.safe_load(f)

    @property
    def project_id(self) -> str:
        # Use GCP project from Pulumi config
        return self._gcp_config.require('project')
    
    @property
    def app_cluster_name(self) -> str:
        return self._settings["app_cluster"]["name"]
    
    @property
    def app_cluster_zone(self) -> str:
        return self._settings["app_cluster"]["zone"]
    
    @property
    def monitoring_cluster_zone(self) -> str:
        return self._settings["monitoring_cluster"]["zone"]
    
    @property
    def network_name(self) -> str:
        return self._settings["network"]["name"]

    def get_region_from_zone(self, zone: str) -> str:
        """Extract region from zone name (e.g., 'us-west3-a' -> 'us-west3')"""
        return zone.rsplit('-', 1)[0]

# Create a singleton instance
settings = Settings()