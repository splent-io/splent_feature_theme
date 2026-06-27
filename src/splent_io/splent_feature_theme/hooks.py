"""Template hooks for splent_feature_theme.

The theme provides the PUBLIC shell (`public_base.html`) plus a library of
composable blocks under `templates/blocks/`. Features compose the public page by
injecting into these slots (declared in public_base.html):

    layout.head     — extra <head> tags
    layout.nav      — public navigation items (header)
    layout.hero     — hero section, full-width, above the content
    layout.footer   — footer columns / social links
    layout.scripts  — scripts before </body>

The theme registers nothing by default — products and content features compose
the page. Skins refine the theme by overriding tokens (THEME_TOKENS) and, if
needed, block templates via [tool.splent.refinement].
"""
