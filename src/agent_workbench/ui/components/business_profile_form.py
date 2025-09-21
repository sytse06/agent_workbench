"""
Business Profile Form Component - UI-002 SEO Coach Interface.

Provides business profile creation form for SEO coaching.
"""

from typing import Any, Dict, Tuple

import gradio as gr


def get_business_profile_form_components() -> (
    Tuple[gr.Textbox, gr.Dropdown, gr.Textbox, gr.Textbox]
):
    """
    Get individual form components for external use.

    Returns:
        Tuple of (business_name, business_type, website_url, location)
        components
    """
    business_name = gr.Textbox(
        label="Bedrijfsnaam", placeholder="Bijv. Restaurant De Gouden Lepel"
    )

    business_type = gr.Dropdown(
        choices=[
            "Restaurant",
            "Webshop",
            "Dienstverlening",
            "B2B Bedrijf",
            "Freelancer",
            "Advocatenkantoor",
            "Zorgverlening",
            "Anders",
        ],
        label="Type bedrijf",
        value="Restaurant",
    )

    website_url = gr.Textbox(label="Website URL", placeholder="https://jouw-website.nl")

    location = gr.Textbox(label="Locatie", placeholder="Amsterdam, Rotterdam, etc.")

    return business_name, business_type, website_url, location


def validate_business_profile(
    business_name: str, business_type: str, website_url: str, location: str
) -> Tuple[bool, str]:
    """
    Validate business profile data.

    Args:
        business_name: Business name input
        business_type: Business type selection
        website_url: Website URL input
        location: Location input

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not business_name.strip():
        return False, "Bedrijfsnaam is verplicht"

    if not website_url.strip():
        return False, "Website URL is verplicht"

    if not website_url.startswith(("http://", "https://")):
        return False, "Website URL moet beginnen met http:// of https://"

    valid_types = [
        "Restaurant",
        "Webshop",
        "Dienstverlening",
        "B2B Bedrijf",
        "Freelancer",
        "Advocatenkantoor",
        "Zorgverlening",
        "Anders",
    ]
    if business_type not in valid_types:
        return False, "Selecteer een geldig bedrijfstype"

    return True, ""


def create_business_profile_dict(
    business_name: str, business_type: str, website_url: str, location: str
) -> Dict[str, Any]:
    """
    Create business profile dictionary from form data.

    Args:
        business_name: Business name
        business_type: Business type
        website_url: Website URL
        location: Location

    Returns:
        Business profile dictionary
    """
    return {
        "business_name": business_name.strip(),
        "business_type": business_type,
        "website_url": website_url.strip(),
        "location": location.strip() or "Nederland",
        "language": "dutch",
        "seo_experience": "beginner",
    }
