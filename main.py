import asyncio
import os

from assistant.shell_assistant import ShellAssistant
from helper.color_scheme_generator import MaterialColorSchemeGenerator
from helper.folder_architect import FolderArchitect
from helper.yaml_editor import YamlEditor
from knowledge_base.knowledge_base import KnowledgeBase
from assistant.ask_user_assistant import AskUserAssistant
from assistant.generation_assistant import CodeGenerationAssistant
from managers.base_manager import BaseManager
from helper.file_helper import FileHelper


async def main_bot():
    # 1. Initialize the KnowledgeBase (this handles loading/building the RAG index)
    kb = await KnowledgeBase.pre_heat()

    # 2. Create a dictionary of all available assistant tools
    assistants = {
        "ask_user": AskUserAssistant(),
        "scheme_generator": MaterialColorSchemeGenerator(),
        "code_generator": CodeGenerationAssistant(knowledge_base=kb),
        "file_helper": FileHelper(),
        "shell_assistant": ShellAssistant(),
        "folder_architect": FolderArchitect(),
        "yaml_editor": YamlEditor(),
    }

    # 3. Initialize the BaseManager with the JSON config and the assistants
    script_dir = os.path.dirname(os.path.abspath(__file__))
    managers_path = os.path.join(script_dir, "jsons", "managers.json")  # Or construct an absolute path
    base_manager = BaseManager(managers_file_path=managers_path, assistants=assistants)

    manager_to_run = base_manager.find_manager("create app folder structure")
    await base_manager.run_flow(manager_to_run)

    # # The main application loop
    # while True:
    #     user_request = input("\n> ").strip()
    #     if user_request.lower() in ['exit', 'quit']:
    #         break
    #
    #     # --- Command Routing via BaseManager ---
    #     manager_to_run = base_manager.find_manager(user_request)
    #
    #     if manager_to_run:
    #         # If a specific manager is found (e.g., "create color scheme"), run its flow
    #         await base_manager.run_flow(manager_to_run)
    #     else:
    #         # If no manager matches, default to a general chat action
    #         logger.info("No specific manager found. Handling as a general chat query...")
    #         answer = await assistants["code_generator"].generate(user_request)
    #         print(f"\n🤖 {answer}")


if __name__ == "__main__":
    asyncio.run(main_bot())
