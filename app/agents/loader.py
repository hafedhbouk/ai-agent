import yaml
from pathlib import Path
from typing import List, Dict, Optional
from app.agents.schemas import AgentYAMLConfig
from app.core.logging import get_logger
from app.core.exceptions import AgentPlatformException

logger = get_logger("agents.loader")


class AgentLoadError(AgentPlatformException):
    def __init__(self, file_path: str, message: str):
        super().__init__(f"Failed to load agent from {file_path}: {message}", "AGENT_LOAD_ERROR")


class AgentLoader:
    def __init__(self, agents_dir: str = "./agents"):
        self.agents_dir = Path(agents_dir)
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def discover_files(self) -> List[Path]:
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return []
        yaml_files = sorted(self.agents_dir.glob("*.yaml")) + sorted(self.agents_dir.glob("*.yml"))
        logger.info(f"Discovered {len(yaml_files)} agent configuration file(s)")
        return yaml_files

    def load_single(self, file_path: Path) -> AgentYAMLConfig:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            if not isinstance(raw, dict):
                raise AgentLoadError(str(file_path), "YAML root must be a mapping")
            config = AgentYAMLConfig(**raw)
            logger.info(f"Loaded agent config: {config.name} from {file_path.name}")
            return config
        except yaml.YAMLError as e:
            raise AgentLoadError(str(file_path), f"YAML parse error: {e}")
        except Exception as e:
            raise AgentLoadError(str(file_path), str(e))

    def load_all(self) -> List[AgentYAMLConfig]:
        configs: List[AgentYAMLConfig] = []
        for file_path in self.discover_files():
            try:
                configs.append(self.load_single(file_path))
            except AgentLoadError as e:
                logger.error(str(e))
        logger.info(f"Successfully loaded {len(configs)} agent configuration(s)")
        return configs
