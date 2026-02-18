
"""
Theme configuration for the application based on the University of Brasília (UnB) brand guidelines.
"""

UNB_THEME = {
    # Official Colors
    'UNB_BLUE': '#003366',      # Pantone 654
    'UNB_GREEN': '#006633',     # Pantone 348
    'UNB_YELLOW_MED': '#FDCA00',
    'UNB_YELLOW_PURE': '#FFED00',
    'UNB_BLUE_MED': '#0068B4',
    'UNB_BLUE_GREEN': '#00A0A7',
    'UNB_GREEN_LIGHT': '#BAD266',

    # Grays (Concreto Scale)
    'UNB_GRAY_DARK': '#7E7E65',     # Concreto 1 (Dark Text)
    'UNB_GRAY_LIGHT': '#EDEDDF',    # Concreto 4 (Light Backgrounds)

    # Semantic Mapping
    'PRIMARY': '#003366',           # UnB Blue
    'WARNING': '#FDCA00',           # UnB Yellow Medium
    'DANGER': '#FF0000',            # Placeholder Red (Standard)
    'SUCCESS': '#006633',           # UnB Green
    'SECONDARY': '#7E7E65',         # UnB Gray Dark
    'BACKGROUND': '#EDEDDF',        # UnB Gray Light
    'TEXT': '#7E7E65',              # UnB Gray Dark
}

# For backward compatibility if needed, though we should migrate fully.
GOV_THEME = UNB_THEME
