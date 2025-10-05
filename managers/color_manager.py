import json
from logger import logger
from assistant.ask_user_assistant import AskUserAssistant
from assistant.app_color_assistant import MaterialColorSchemeGenerator
from assistant.generation_assistant import CodeGenerationAssistant
from managers.file_manager import FileManager


class ColorManager:
    """
    Orchestrates the complete workflow for generating a Flutter color scheme.
    """

    def __init__(
            self,
            ask_assistant: AskUserAssistant,
            scheme_generator: MaterialColorSchemeGenerator,
            code_generator: CodeGenerationAssistant,
            file_manager: FileManager,
    ):
        """Initializes the manager with all the necessary assistant tools."""
        self.ask_assistant = ask_assistant
        self.scheme_generator = scheme_generator
        self.code_generator = code_generator
        self.file_manager = file_manager
        logger.info("ColorManager initialized with all required assistants.")

    async def run_flow(self):
        """Executes the step-by-step color generation pipeline."""
        logger.info("Starting 'Color Scheme Generation' flow...")
        context = {}

        # --- Step 1: Ask user for the seed color ---
        logger.info("Step 1: Asking user for the seed color.")
        params_to_get = [
            {"name": "seed_color", "type": "color hex code", "prompt": "What is the seed color for the color scheme?"}
        ]
        user_inputs = await self.ask_assistant.gather_info(params_to_get)
        seed_color = user_inputs.get("seed_color")
        if not seed_color:
            logger.error("Failed to get seed color from user. Aborting flow.")
            return
        context['seed_color'] = seed_color

        # --- Step 2: Generate Material color schemes ---
        logger.info(f"Step 2: Generating Material schemes from seed color '{seed_color}'.")
        schemes = self.scheme_generator.generate_material_schemes(seed_color)
        context.update(schemes)

        # --- Step 3: Create and write the app_colors.json file ---
        logger.info("Step 3: Creating and writing to 'assets/app_colors.json'.")
        json_content = json.dumps(context, indent=2)
        await self.file_manager.write_file("assets/app_colors.json", json_content)

        # --- Step 4: Generate the AppColors.dart code ---
        logger.info("Step 4: Generating Dart code for AppColors using the knowledge base.")
        generation_prompt = (
            "Generate a complete AppColors.dart file. This file should contain a class named AppColors "
            "that loads and parses the 'assets/app_colors.json' file. It must provide a method to get a "
            "ThemeData object based on the schemes defined in the JSON."
        )
        generated_code = await self.code_generator.generate(generation_prompt)
        if not generated_code:
            logger.error("Code generation failed. Aborting flow.")
            return
        context['generated_code'] = generated_code

        # --- Step 5: Create and write the app_colors.dart file ---
        logger.info("Step 5: Creating and writing to 'lib/theme/colors/app_colors.dart'.")
        await self.file_manager.write_file("lib/theme/colors/app_colors.dart", context['generated_code'])

        logger.info("✅ 'Color Scheme Generation' flow completed successfully!")
