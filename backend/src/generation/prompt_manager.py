import os
import yaml
import logging
from typing import Tuple

from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages loading, validating, and versioning system and human prompts
    dynamically from a centralized YAML prompts file.
    
    Decouples prompt engineering cycles from python code releases
    and enables structured tracing of prompt versions for A/B evaluation.
    """
    
    def __init__(self, yaml_path: str = None):
        if yaml_path is None:
            # Resolve absolute path relative to project structure
            yaml_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "prompts.yaml"
            )
            
        self.yaml_path = yaml_path
        logger.info(f"Loading versioned prompts repository from: {self.yaml_path}...")
        
        if not os.path.exists(self.yaml_path):
            raise FileNotFoundError(f"Prompts definition file not found at: {self.yaml_path}")
            
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Prompts successfully parsed. Schema Version: {self.config.get('version')}")
        except Exception as e:
            logger.error(f"Failed to read prompt configurations: {e}")
            raise

    def get_prompt(self, prompt_key: str = "rag_prompt", version: str = "v1") -> Tuple[ChatPromptTemplate, dict]:
        """
        Loads a specific prompt configuration and returns it as a LangChain ChatPromptTemplate.
        
        Args:
            prompt_key: The identifier of the prompt category (e.g. 'rag_prompt').
            version: The version string selector (e.g. 'v1', 'v2').
            
        Returns:
            Tuple[ChatPromptTemplate, dict]:
                - ChatPromptTemplate: The compiled ChatPromptTemplate ready for LCEL binding.
                - dict: Prompt metadata containing 'version_id', 'description', and 'prompt_key' for A/B tracing.
        """
        prompts = self.config.get("prompts", {})
        prompt_category = prompts.get(prompt_key, {})
        
        if not prompt_category:
            raise ValueError(f"Prompt category '{prompt_key}' not found in prompts.yaml.")
            
        prompt_config = prompt_category.get(version)
        if not prompt_config:
            raise ValueError(
                f"Prompt version '{version}' not found under category '{prompt_key}'. "
                f"Available versions: {list(prompt_category.keys())}"
            )
            
        system_template = prompt_config.get("system")
        human_template = prompt_config.get("human", "{question}")
        
        if not system_template:
            raise ValueError(f"System template is missing for prompt '{prompt_key}' version '{version}'.")
            
        # Compile ChatPromptTemplate
        chat_template = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", human_template)
        ])
        
        # Package prompt metadata for downstream evaluation and tracking
        metadata = {
            "version_id": prompt_config.get("version_id"),
            "description": prompt_config.get("description", ""),
            "prompt_key": prompt_key
        }
        
        logger.info(f"Loaded prompt '{prompt_key}' version '{version}' successfully ({metadata['description']})")
        return chat_template, metadata

if __name__ == "__main__":
    # Quick manual diagnostic block
    logging.basicConfig(level=logging.INFO)
    manager = PromptManager()
    template, meta = manager.get_prompt("rag_prompt", "v1")
    print(f"Loaded Metadata: {meta}")
    print("System Prompt snippet:")
    print(template.messages[0].prompt.template[:100] + "...")
