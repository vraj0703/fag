import asyncio

from assistant.generation_assistant import CodeGenerationAssistant
from knowledge_base.knowledge_base import KnowledgeBase
from logger import logger


async def kb_bot():
    """
    Main entry point to initialize the RAG system and run the code generation assistant.
    """

    logger.info("Initializing KnowledgeBase for the Code Generation Assistant...")
    # The pre_heat method handles loading from disk or building from source
    kb = await KnowledgeBase.pre_heat()

    # Initialize the assistant with the fully populated knowledge base
    assistant = CodeGenerationAssistant(knowledge_base=kb)

    logger.info("Code Generation Assistant is ready.")
    print("\nHello! I am FAG, your code generation assistant.")
    print(
        "Describe the code you would like me to write (type 'exit' or 'quit' to end)."
    )

    while True:
        try:
            user_request = input("\n> ")
            if user_request.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            # Generate the code based on the user's request
            generated_code = await assistant.generate(user_request)

            if generated_code:
                print("\n🤖 Here is the generated code:\n")
                print("---")
                print(generated_code)
                print("---")
            else:
                print("\n🤖 I'm sorry, I was unable to generate the code.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(
                f"An unexpected error occurred in the main loop: {e}", exc_info=True
            )
            print("🤖 An error occurred. Please try again.")


if __name__ == "__main__":
    asyncio.run(kb_bot())
