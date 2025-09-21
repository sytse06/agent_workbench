"""
Basic Dutch localization for SEO coaching - UI-002 SEO Coach Interface.

Provides Dutch language support for the SEO coach interface.
"""

DUTCH_MESSAGES = {
    "no_business_profile": (
        "Vul eerst je bedrijfsgegevens in en analyseer je website "
        "voordat we kunnen beginnen met coaching."
    ),
    "analysis_complete": "✅ Website analyse klaar! Stel je vragen.",
    "processing": "🔄 Je verzoek wordt verwerkt...",
    "error_general": "Er ging iets mis. Probeer het opnieuw.",
    "website_required": "Vul een website URL in om te beginnen.",
    "business_name_required": "Vul je bedrijfsnaam in.",
    "analyzing_website": "🔍 Website wordt geanalyseerd...",
    "coach_ready": "👋 Hoi! Analyseer eerst je website voor SEO coaching!",
    "quick_audit_title": "🔍 Snelle SEO Check",
    "keyword_help_title": "🔑 Zoekwoord Tips",
    "content_ideas_title": "✍️ Content Ideeën",
    "send_button": "Verstuur",
    "message_placeholder": "Stel je vraag over SEO...",
    "message_label": "Jouw vraag",
    "analyzing": "Bezig met analyseren...",
    "success": "Gelukt!",
    "error": "Fout",
}


def get_dutch_message(key: str, **kwargs) -> str:
    """
    Get Dutch message with optional formatting.

    Args:
        key: Message key
        **kwargs: Formatting arguments

    Returns:
        Formatted Dutch message
    """
    message = DUTCH_MESSAGES.get(key, f"Bericht niet gevonden: {key}")
    return message.format(**kwargs) if kwargs else message
