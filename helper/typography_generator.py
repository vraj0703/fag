import asyncio
import json
from typing import Dict, Any

from pydantic import BaseModel, Field

# Assuming these are imported from your project structure
from assistant.ask_user_assistant import AskUserAssistant
from logger import logger

# --- 1. Pydantic Models to Define the JSON Structure ---

class Style(BaseModel):
    fontFamily: str
    fontWeight: str
    fontSize: int
    lineHeight: int
    letterSpacing: float
    token: str

class Styles(BaseModel):
    md_sys_typescale: Dict[str, Style] = Field(..., alias='md.sys.typescale')
    md_sys_typescale_emphasized: Dict[str, Style] = Field(..., alias='md.sys.typescale.emphasized')

class Typography(BaseModel):
    styles: Styles

# --- 2. Default Material Design 3 Typescale Data ---

DEFAULT_TYPESCALE = {
    "display-large": {"fontWeight": "400", "fontSize": 57, "lineHeight": 64, "letterSpacing": -0.25},
    "display-medium": {"fontWeight": "400", "fontSize": 45, "lineHeight": 52, "letterSpacing": 0},
    "display-small": {"fontWeight": "400", "fontSize": 36, "lineHeight": 44, "letterSpacing": 0},
    "headline-large": {"fontWeight": "400", "fontSize": 32, "lineHeight": 40, "letterSpacing": 0},
    "headline-medium": {"fontWeight": "400", "fontSize": 28, "lineHeight": 36, "letterSpacing": 0},
    "headline-small": {"fontWeight": "400", "fontSize": 24, "lineHeight": 32, "letterSpacing": 0},
    "title-large": {"fontWeight": "400", "fontSize": 22, "lineHeight": 28, "letterSpacing": 0},
    "title-medium": {"fontWeight": "500", "fontSize": 16, "lineHeight": 24, "letterSpacing": 0.15},
    "title-small": {"fontWeight": "500", "fontSize": 14, "lineHeight": 20, "letterSpacing": 0.1},
    "label-large": {"fontWeight": "500", "fontSize": 14, "lineHeight": 20, "letterSpacing": 0.1},
    "label-medium": {"fontWeight": "500", "fontSize": 12, "lineHeight": 16, "letterSpacing": 0.5},
    "label-small": {"fontWeight": "500", "fontSize": 11, "lineHeight": 16, "letterSpacing": 0.5},
    "body-large": {"fontWeight": "400", "fontSize": 16, "lineHeight": 24, "letterSpacing": 0.5},
    "body-medium": {"fontWeight": "400", "fontSize": 14, "lineHeight": 20, "letterSpacing": 0.25},
    "body-small": {"fontWeight": "400", "fontSize": 12, "lineHeight": 16, "letterSpacing": 0.4},
}

# Create the emphasized version by copying the default and changing the font weight
DEFAULT_TYPESCALE_EMPHASIZED = {
    token: {**values, "fontWeight": "700"}
    for token, values in DEFAULT_TYPESCALE.items()
}


# --- 3. The Typography Style Generator Class ---

class TypographyStyleGenerator:
    """
    An assistant that interactively gathers a primary font from the user and
    generates a Material Design 3 typography style configuration.
    """

    def __init__(self):
        """Initializes the conversational collector."""
        self.collector = AskUserAssistant()
        logger.info('TypographyStyleGenerator initialized.')

    def _generate_styles(self, primary_font: str) -> Dict[str, Any]:
        """
        Generates the final 'styles' JSON object by applying the primary font
        to the default Material Design typescales.
        """
        styles_data = {
            'md.sys.typescale': {
                token: {"fontFamily": primary_font, **values, "token": token}
                for token, values in DEFAULT_TYPESCALE.items()
            },
            'md.sys.typescale.emphasized': {
                token: {"fontFamily": primary_font, **values, "token": token}
                for token, values in DEFAULT_TYPESCALE_EMPHASIZED.items()
            }
        }

        # Validate with Pydantic and convert to dict, ensuring correct aliases
        return Typography(styles=styles_data).model_dump(by_alias=True)

    async def generate(self) -> Dict[str, Any]:
        """
        Orchestrates the conversational flow to generate the typography JSON.
        """
        logger.info('Starting typography style generation flow...')

        # --- Step 1: Gather the primary font from the user ---
        params_to_get = [
            {
                'name': 'primary_font',
                'type': 'font name (e.g., Roboto, Inter)',
                'prompt': 'What is the primary font for the typography styles?'
            }
        ]

        user_inputs = await self.collector.gather_info(params_to_get)
        primary_font = user_inputs.get('primary_font')

        if not primary_font:
            logger.error('Could not obtain a primary font from the user. Aborting.')
            return {}

        # --- Step 2: Generate the final JSON structure ---
        logger.info(f"Generating typography styles with primary font: '{primary_font}'")
        final_json = self._generate_styles(primary_font)

        logger.info('Typography style generation flow completed successfully.')
        return final_json


# --- Example Usage ---
async def main():
    """A test function to demonstrate the TypographyStyleGenerator."""

    generator = TypographyStyleGenerator()

    print('--- Starting Typography Style Generator ---')
    final_styles = await generator.generate()
    print('--- Generation Complete ---')

    if final_styles:
        print('\nHere is the generated typography configuration:')
        # Use json.dumps for pretty printing the final dictionary
        print(json.dumps(final_styles, indent=2))

if __name__ == '__main__':
    asyncio.run(main())