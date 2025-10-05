import asyncio

from assistant.app_color_assistant import MaterialColorSchemeGenerator
from assistant.ask_user_assistant import AskUserAssistant
from assistant.generation_assistant import CodeGenerationAssistant
from knowledge_base.knowledge_base import KnowledgeBase
from managers.color_manager import ColorManager
from managers.file_manager import FileManager

async def main_bot():
    # 1. Initialize the KnowledgeBase (this handles loading/building the RAG index)
    kb = await KnowledgeBase.pre_heat()

    # 2. Initialize all the individual assistant tools
    ask_assistant = AskUserAssistant()
    scheme_generator = MaterialColorSchemeGenerator()
    code_generator = CodeGenerationAssistant(knowledge_base=kb)
    file_manager = FileManager()

    # 3. Initialize the ColorManager with its required tools
    color_manager = ColorManager(
        ask_assistant=ask_assistant,
        scheme_generator=scheme_generator,
        code_generator=code_generator,
        file_manager=file_manager
    )

    print("\nHello! I am FAG, your Flutter App Generation assistant.")

    await color_manager.run_flow()

if __name__ == "__main__":
    asyncio.run(main_bot())