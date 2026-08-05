from typing import Dict, Any, List
from app.agents.langgraph.orchestrator import orchestrator
from app.core.logging import get_logger

logger = get_logger("agents.langgraph.workflows")


def register_commerce_workflow(llm: Any, tools: Dict[str, Any]) -> None:
    agent_definitions = {
        "commercial": {
            "system_prompt": "Tu es un agent commercial. Tu génères des devis et gères les demandes clients.",
            "tools": tools.get("commercial_tools", []),
        },
        "juridique": {
            "system_prompt": "Tu es un agent juridique. Tu vérifies les contrats et les conditions légales.",
            "tools": tools.get("legal_tools", []),
        },
        "documentaire": {
            "system_prompt": "Tu es un agent documentaire. Tu recherches et compile les informations pertinentes.",
            "tools": tools.get("document_tools", []),
        },
    }
    orchestrator.register_multi_agent(
        workflow_name="commerce_workflow",
        agent_definitions=agent_definitions,
        llm=llm,
        orchestrator_prompt="Tu es l'orchestrateur commercial. Coordonne les agents pour créer un devis complet.",
    )
    logger.info("Commerce workflow registered")


def register_maintenance_workflow(llm: Any, tools: Dict[str, Any]) -> None:
    agent_definitions = {
        "diagnostic": {
            "system_prompt": "Tu es un agent de diagnostic. Tu analyses les problèmes techniques.",
            "tools": tools.get("diagnostic_tools", []),
        },
        "documentaire": {
            "system_prompt": "Tu es un agent documentaire. Tu recherches la documentation technique.",
            "tools": tools.get("document_tools", []),
        },
        "rapporteur": {
            "system_prompt": "Tu es un agent rapporteur. Tu génères des rapports de maintenance.",
            "tools": tools.get("report_tools", []),
        },
    }
    orchestrator.register_multi_agent(
        workflow_name="maintenance_workflow",
        agent_definitions=agent_definitions,
        llm=llm,
        orchestrator_prompt="Tu es l'orchestrateur maintenance. Coordonne les agents pour diagnostiquer et rapporter.",
    )
    logger.info("Maintenance workflow registered")


WORKFLOW_REGISTRY = {
    "commerce_workflow": register_commerce_workflow,
    "maintenance_workflow": register_maintenance_workflow,
}


def register_workflow(workflow_name: str, llm: Any, tools: Dict[str, Any]) -> None:
    if workflow_name not in WORKFLOW_REGISTRY:
        raise ValueError(f"Workflow '{workflow_name}' not found in registry")
    WORKFLOW_REGISTRY[workflow_name](llm, tools)
    logger.info(f"Workflow '{workflow_name}' registered")


def list_workflows() -> List[str]:
    return list(WORKFLOW_REGISTRY.keys())