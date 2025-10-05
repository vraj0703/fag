import json
import re
from logger import logger


class BaseManager:
    """
    A generic manager that reads JSON configurations to orchestrate
    a sequence of assistant actions to complete a flow.
    """

    def __init__(self, managers_file_path: str, assistants: dict):
        """
        Initializes the manager with a path to the JSON config and a dictionary of available assistants.
        """
        self.assistants = assistants
        logger.info(f"Loading manager flows from {managers_file_path}...")
        try:
            with open(managers_file_path, 'r') as f:
                self.managers = json.load(f).get('managers', [])
            logger.info(f"Successfully loaded {len(self.managers)} manager definitions.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"FATAL: Could not load or parse manager file at '{managers_file_path}'. Error: {e}")
            self.managers = []

    def _get_nested_value(self, data_dict, path):
        """Safely retrieves a nested value from a dictionary using a dot-separated path."""
        keys = path.split('.')
        value = data_dict
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None  # Path not found
        return value

    def _format_input(self, value, context):
        """
        Recursively formats input strings, replacing complex placeholders like
        {{context.user_inputs.seed_color}} with values from the context dictionary.
        """
        if isinstance(value, str):
            # Find all placeholders like {{context.some.nested.value}}
            placeholders = re.findall(r"\{\{context\.(.*?)\}\}", value)
            for placeholder in placeholders:
                # Retrieve the nested value from the context
                retrieved_value = self._get_nested_value(context, placeholder)
                if retrieved_value is not None:
                    # If the placeholder is the entire string, replace it directly to preserve type
                    if value == f"{{{{context.{placeholder}}}}}":
                        return retrieved_value
                    # Otherwise, perform a string replacement
                    value = value.replace(f"{{{{context.{placeholder}}}}}", str(retrieved_value))
            return value
        elif isinstance(value, list):
            return [self._format_input(item, context) for item in value]
        elif isinstance(value, dict):
            return {k: self._format_input(v, context) for k, v in value.items()}
        return value

    def find_manager(self, user_input: str):
        """Finds a manager that matches the user's input based on keywords."""
        for manager in self.managers:
            for keyword in manager.get('keywords', []):
                if keyword.lower() in user_input.lower():
                    logger.info(f"Match found! Activating manager: '{manager['name']}'")
                    return manager
        return None

    async def run_flow(self, manager_config: dict):
        """Executes the step-by-step pipeline for a given manager configuration."""
        if not manager_config:
            logger.error("run_flow was called with an invalid manager configuration (None). Aborting flow.")
            return

        logger.info(f"Starting flow for manager: '{manager_config['name']}'...")
        context = {}

        sorted_steps = sorted(manager_config.get('steps', []), key=lambda x: x.get('id', float('inf')))

        for step in sorted_steps:
            assistant_name = step.get('assistant')
            method_name = step.get('method')
            step_desc = step.get('description', 'No description')
            logger.info(f"Executing Step {step.get('id')}: {step_desc}")

            assistant = self.assistants.get(assistant_name)
            if not assistant:
                logger.error(f"Assistant '{assistant_name}' not found. Aborting flow.")
                return

            method = getattr(assistant, method_name, None)
            if not callable(method):
                logger.error(f"Method '{method_name}' not found on assistant '{assistant_name}'. Aborting flow.")
                return

            inputs = self._format_input(step.get('inputs', {}), context)

            result = await method(**inputs)

            for result_key, context_key in step.get('outputs', {}).items():
                if result_key == "result":
                    context[context_key] = result
                    logger.info(f"Stored step output into context as '{context_key}'")

        logger.info(f"✅ Flow '{manager_config['name']}' completed successfully!")

