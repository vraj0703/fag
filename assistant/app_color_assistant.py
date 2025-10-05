"""
Generate a Material color scheme from a seed color using material-color-utilities.
Requires: pip install material-color-utilities
Reference: https://github.com/RuurdBijlsma/material-color-utilities/blob/main/docs/api.md
"""

from material_color_utilities import theme_from_color, Variant


class MaterialColorSchemeGenerator:
    """A class to have an intelligent, multi-turn conversation to gather information."""

    def generate_material_schemes(self, seed_hex: str, variant=Variant.VIBRANT, contrast_level: float = 0.25):
        """
        Convert a seed color (hex) to Material Design color schemes (light & dark).

        Args:
            seed_hex (str): Seed color hex string, e.g., "#4285F4".
            variant (str): Color variant, e.g., "VIBRANT", "TONALSPOT", etc.
            contrast_level (float): Contrast level for theme generation.

        Returns:
            dict: Dictionary with 'light' and 'dark' color schemes.
        """
        # Create theme from seed color
        theme = theme_from_color(
            source=seed_hex,
            contrast_level=contrast_level,
            variant=variant
        )

        result = {
            'light': theme.schemes.light.dict(),
            'dark': theme.schemes.dark.dict(),
        }
        return result


def test_material_color_scheme():
    seed_color = "#6200EE"  # Example seed color
    generator = MaterialColorSchemeGenerator()
    schemes = generator.generate_material_schemes(seed_color)
    print("Material Color Schemes from Seed Color:")
    print("Light Scheme:")
    for k, v in schemes['light'].items():
        print(f"  {k}: {v}")
    print("\nDark Scheme:")
    for k, v in schemes['dark'].items():
        print(f"  {k}: {v}")
    return schemes


if __name__ == "__main__":
    test_material_color_scheme()
