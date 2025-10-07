from typing import Dict, Any

from pydantic import BaseModel, Field

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
        logger.info('TypographyStyleGenerator initialized.')

    def _generate_styles(self, primary_font: str) -> Dict[str, Any]:
        """
        Generates the final 'styles' JSON object by applying the primary font
        to the default Material Design typescales.
        """
        # 1. Create the dictionaries for each typescale
        typescale_data = {
            token: {"fontFamily": primary_font, **values, "token": token}
            for token, values in DEFAULT_TYPESCALE.items()
        }
        typescale_emphasized_data = {
            token: {"fontFamily": primary_font, **values, "token": token}
            for token, values in DEFAULT_TYPESCALE_EMPHASIZED.items()
        }

        # 2. Create an instance of the Styles model
        # Pydantic will handle mapping the dictionary to the aliased fields
        styles_object = Styles(
            **{
                'md.sys.typescale': typescale_data,
                'md.sys.typescale.emphasized': typescale_emphasized_data
            }
        )

        # 3. Pass the validated Styles object to the Typography model
        typography_model = Typography(styles=styles_object)

        # 4. Validate and convert to dict, ensuring correct aliases
        return typography_model.model_dump(by_alias=True)

    async def generate(self, base_font) -> Dict[str, Any]:
        """
        Orchestrates the conversational flow to generate the typography JSON.
        """
        logger.info('Starting typography style generation flow...')
        final_json = self._generate_styles(base_font)

        logger.info('Typography style generation flow completed successfully.')
        return final_json
