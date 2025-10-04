"""
Generate a Material color scheme from a seed color using material-color-utilities.
Requires: pip install material-color-utilities
Reference: https://github.com/RuurdBijlsma/material-color-utilities/blob/main/docs/api.md
"""

from material_color_utilities import theme_from_color


def generate_material_scheme(seed_hex: str, variant: str = "VIBRANT", contrast_level: float = 0.25):
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

    result = {}
    for mode in ['light', 'dark']:
        scheme = getattr(theme.schemes, mode)
        result[mode] = {
            "primary": scheme.primary,
            "onPrimary": scheme.on_primary,
            "primaryContainer": scheme.primary_container,
            "onPrimaryContainer": scheme.on_primary_container,
            "secondary": scheme.secondary,
            "onSecondary": scheme.on_secondary,
            "secondaryContainer": scheme.secondary_container,
            "onSecondaryContainer": scheme.on_secondary_container,
            "tertiary": scheme.tertiary,
            "onTertiary": scheme.on_tertiary,
            "tertiaryContainer": scheme.tertiary_container,
            "onTertiaryContainer": scheme.on_tertiary_container,
            "error": scheme.error,
            "onError": scheme.on_error,
            "errorContainer": scheme.error_container,
            "onErrorContainer": scheme.on_error_container,
            "background": scheme.background,
            "onBackground": scheme.on_background,
            "surface": scheme.surface,
            "onSurface": scheme.on_surface,
            "surfaceVariant": scheme.surface_variant,
            "onSurfaceVariant": scheme.on_surface_variant,
            "outline": scheme.outline,
            "outlineVariant": scheme.outline_variant,
            "inverseSurface": scheme.inverse_surface,
            "inverseOnSurface": scheme.inverse_on_surface,
            "inversePrimary": scheme.inverse_primary,
            "shadow": scheme.shadow,
            "scrim": scheme.scrim,
            "surfaceTint": scheme.surface_tint,
        }
    return result


if __name__ == "__main__":
    seed_color = "#6200EE"  # Example seed color
    schemes = generate_material_scheme(seed_color)
    print("Material Color Schemes from Seed Color:")
    print("Light Scheme:")
    for k, v in schemes['light'].items():
        print(f"  {k}: {v}")
    print("\nDark Scheme:")
    for k, v in schemes['dark'].items():
        print(f"  {k}: {v}")
