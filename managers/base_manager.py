import json
import re
from logger import logger
import os
from pydantic import BaseModel


class BaseManager:
    """
    A generic manager that reads JSON configurations to orchestrate
    a sequence of assistant actions to complete a flow. It persists
    user inputs by merging them into a JSON file.
    """

    def __init__(self, managers_file_path: str, assistants: dict, user_input_file_path: str = 'user_input.json'):
        """
        Initializes the manager, loading manager definitions and persistent user inputs.
        """
        self.assistants = assistants
        self.user_input_file_path = user_input_file_path
        self.context = self._load_user_input()

        logger.info(f"Loading manager flows from {managers_file_path}...")
        try:
            with open(managers_file_path, 'r') as f:
                self.managers = json.load(f).get('managers', [])
            logger.info(f"Successfully loaded {len(self.managers)} manager definitions.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"FATAL: Could not load or parse manager file at '{managers_file_path}'. Error: {e}")
            self.managers = []

    def _load_user_input(self) -> dict:
        """Loads user input from the specified JSON file if it exists."""
        if os.path.exists(self.user_input_file_path):
            logger.info(f"Loading persistent user inputs from {self.user_input_file_path}")
            try:
                with open(self.user_input_file_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
        return {}

    def _save_user_input(self):
        """Saves the current context to the user input JSON file."""
        logger.info(f"Saving context to {self.user_input_file_path}")
        try:
            with open(self.user_input_file_path, 'w') as f:
                json.dump(self.context, f, indent=4)
        except IOError as e:
            logger.error(f"Could not write to user_input file: {e}")

    def _get_nested_value(self, data_dict, path):
        """Safely retrieves a nested value from a dictionary using a dot-separated path."""
        keys = path.split('.')
        value = data_dict
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _format_input(self, value, context):
        """
        Recursively formats input strings, replacing complex placeholders like
        {{context.schemes.light}} with values from the context dictionary,
        ensuring correct JSON formatting.
        """
        if isinstance(value, str):
            # Case 1: The entire string is a placeholder.
            # Return the raw object to preserve its type (dict, list, etc.).
            match = re.fullmatch(r"\{\{context\.(.*?)}}", value)
            if match:
                placeholder = match.group(1)
                return self._get_nested_value(context, placeholder)

            # Case 2: The placeholder is embedded within a larger string.
            # We need to serialize objects to valid JSON before embedding.
            placeholders = re.findall(r"\{\{context\.(.*?)}}", value)
            for placeholder in placeholders:
                retrieved_value = self._get_nested_value(context, placeholder)

                if retrieved_value is not None:
                    # If the retrieved value is a dict or list, serialize it to a
                    # JSON string with double quotes. Otherwise, convert to a plain string.
                    if isinstance(retrieved_value, (dict, list)):
                        replacement = json.dumps(retrieved_value)
                    else:
                        replacement = str(retrieved_value)

                    value = value.replace(f"{{{{context.{placeholder}}}}}", replacement)
            return value

        elif isinstance(value, list):
            # Recursively format each item in the list.
            return [self._format_input(item, context) for item in value]
        elif isinstance(value, dict):
            # Recursively format each value in the dictionary.
            return {k: self._format_input(v, context) for k, v in value.items()}

        # Return the value as-is if it's not a string, list, or dict.
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

            # Pass the main context (self.context) directly for placeholder replacement.
            inputs = self._format_input(step.get('inputs', {}), self.context)

            result = await method(**inputs)

            # Convert Pydantic models to dicts before storing to ensure JSON serializability
            if isinstance(result, BaseModel):
                result_to_store = result.model_dump()
            else:
                result_to_store = result

            # Store the output back into the main context
            if 'outputs' in step:
                for result_key, context_key in step.get('outputs', {}).items():
                    if result_key == "result":
                        # --- THE FIX: MERGE a new user input with existing ---
                        if (context_key in self.context and
                                isinstance(self.context.get(context_key), dict) and
                                isinstance(result_to_store, dict)):
                            self.context[context_key].update(result_to_store)
                            logger.info(f"Updated (merged) context for '{context_key}'")
                        else:
                            # Otherwise, just set the value
                            self.context[context_key] = result_to_store
                            logger.info(f"Stored step output into context as '{context_key}'")

            # After a step that gathers user input, save the updated context
            if assistant_name == 'ask_user':
                self._save_user_input()

        logger.info(f"Flow '{manager_config['name']}' completed successfully!")
