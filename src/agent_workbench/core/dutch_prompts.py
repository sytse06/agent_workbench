"""Dutch SEO coaching prompt templates for seo_coach mode."""

from typing import Any, Dict


class DutchSEOPrompts:
    """Dutch SEO coaching prompt templates and system messages."""

    @staticmethod
    def get_coaching_system_prompt(business_type: str = "algemeen") -> str:
        """
        Get Dutch SEO coaching system prompt.

        Args:
            business_type: Type of business for tailored advice

        Returns:
            System prompt in Dutch
        """
        base_prompt = """Je bent een Nederlandse SEO expert en coach die kleine en
middelgrote bedrijven helpt met hun online vindbaarheid. Je spreekt altijd in
het Nederlands en geeft praktische, uitvoerbare adviezen.

Je kernvaardigheden:
- SEO technische analyse en optimalisatie
- Nederlandse zoekwoordenonderzoek en -strategie
- Content marketing voor de Nederlandse markt
- Local SEO voor Nederlandse bedrijven
- Google Mijn Bedrijf optimalisatie
- Linkbuilding strategieën voor Nederland
- SEO voor Nederlandse e-commerce

Je communicatiestijl:
- Vriendelijk en toegankelijk
- Spreekt de taal van ondernemers
- Geeft concrete, praktische tips
- Legt technische concepten uit in begrijpelijke taal
- Vraagt door om de specifieke situatie te begrijpen
- Geeft prioriteiten aan (wat eerst te doen)

Je focus ligt op:
- Resultaten die echt impact hebben op het bedrijf
- Kosteneffectieve SEO strategieën
- Tools die ook kleine bedrijven kunnen gebruiken
- Tijdsinvestering die realistisch is voor drukke ondernemers
"""

        business_specific = {
            "webshop": """
Extra focus voor webshops:
- Productpagina optimalisatie
- Categoriestructuur voor SEO
- Product reviews en ratings
- Technische SEO voor e-commerce
- Conversie optimalisatie
""",
            "restaurant": """
Extra focus voor restaurants:
- Local SEO en Google Mijn Bedrijf
- Online reviews management
- Menukaart SEO
- Locatie-gebaseerde zoekwoorden
- Seizoensgebonden content
""",
            "dienstverlening": """
Extra focus voor dienstverleners:
- Expertise positionering
- Case studies en testimonials
- Lokale zoekopdrachten
- Service pagina optimalisatie
- Vertrouwen opbouwen via content
""",
            "retail": """
Extra focus voor retail:
- Product vindbaarheid
- Voorraad en beschikbaarheid
- Local inventory ads
- Omnichannel SEO strategie
- Seizoensgebonden optimalisatie
""",
        }

        if business_type.lower() in business_specific:
            base_prompt += business_specific[business_type.lower()]

        base_prompt += """

Begin elke coaching sessie met het begrijpen van:
1. Wat voor bedrijf het is
2. Wat hun huidige SEO uitdagingen zijn
3. Hoeveel tijd/budget ze hebben
4. Wat hun prioritaire doelen zijn

Geef altijd concrete volgende stappen aan het einde van je advies."""

        return base_prompt

    @staticmethod
    def get_analysis_prompt(website_url: str, business_context: Dict[str, Any]) -> str:
        """
        Get prompt for website SEO analysis.

        Args:
            website_url: Website to analyze
            business_context: Business information

        Returns:
            Analysis prompt in Dutch
        """
        business_name = business_context.get("business_name", "het bedrijf")
        business_type = business_context.get("business_type", "algemeen")

        return f"""Ik ga de website {website_url} van {business_name} ({business_type})
analyseren op SEO-kansen.

Focus op deze Nederlandse SEO aspecten:
1. **Technische basis**: Snelheid, mobile-first, SSL, structuur
2. **Content kwaliteit**: Nederlandse taal, zoekwoorden, gebruikersintentie
3. **Local SEO**: Voor Nederlandse markt relevantie
4. **Concurrentie positie**: Wat doen andere Nederlandse bedrijven beter
5. **Quick wins**: Wat kan snel verbeterd worden
6. **Prioriteiten**: Wat heeft de grootste impact

Geef concrete, uitvoerbare adviezen die {business_name} zelf kan implementeren
of tegen redelijke kosten kan laten uitvoeren.

Let op Nederlandse specifieke factoren:
- .nl domein voordelen
- Nederlandse zoekgedrag en taal
- Lokale concurrentie
- Google Mijn Bedrijf optimalisatie
- Nederlandse linkbuilding mogelijkheden"""

    @staticmethod
    def get_recommendations_prompt(
        analysis_results: Dict[str, Any], business_profile: Dict[str, Any]
    ) -> str:
        """
        Get prompt for SEO recommendations.

        Args:
            analysis_results: Previous analysis findings
            business_profile: Business information

        Returns:
            Recommendations prompt in Dutch
        """
        business_name = business_profile.get("business_name", "het bedrijf")
        experience_level = business_profile.get("seo_experience_level", "beginner")

        experience_context = {
            "beginner": "Leg alles stap-voor-stap uit en focus op de basis",
            "intermediate": "Geef gedetailleerde strategieën met praktische "
            "implementatie tips",
            "advanced": "Focus op geavanceerde tactieken en technische "
            "optimalisaties",
        }

        context = experience_context.get(
            experience_level, experience_context["beginner"]
        )

        return f"""Gebaseerd op de SEO analyse voor {business_name},
geef nu concrete aanbevelingen.

{context}

Structureer je aanbevelingen als volgt:

**🚀 QUICK WINS (deze week)**
- 3-5 acties die direct impact hebben
- Concrete stappen en tools
- Verwachte resultaten

**📈 KORTE TERMIJN (1-3 maanden)**\n
- Strategische verbeteringen
- Content en technische optimalisaties
- Meetbare doelstellingen

**🎯 LANGE TERMIJN (3-12 maanden)**
- Groei strategieën
- Autoriteit opbouw
- Schalings mogelijkheden

Voor elke aanbeveling:
- Waarom dit belangrijk is
- Hoe het te implementeren\n
- Welke tools/resources nodig zijn
- Verwachte tijdsinvestering
- Prioriteit niveau (hoog/medium/laag)

Eindig met concrete volgende stappen en hoe we de voortgang kunnen meten."""

    @staticmethod
    def get_implementation_guidance_prompt(
        recommendation: str, experience_level: str
    ) -> str:
        """
        Get prompt for implementation guidance.

        Args:
            recommendation: Specific SEO recommendation
            experience_level: User's SEO experience level

        Returns:
            Implementation guidance prompt in Dutch
        """
        if experience_level == "beginner":
            detail_level = (
                "Geef zeer gedetailleerde stap-voor-stap instructies "
                "met screenshots waar mogelijk"
            )
        elif experience_level == "intermediate":
            detail_level = (
                "Geef praktische implementatie tips met belangrijke " "aandachtspunten"
            )
        else:
            detail_level = (
                "Focus op strategische overwegingen en geavanceerde "
                "implementatie tactieken"
            )

        return f"""Help met het implementeren van deze SEO aanbeveling:
{recommendation}

{detail_level}

Behandel deze aspecten:

**📋 VOORBEREIDING**
- Wat moet je vooraf regelen
- Welke tools/toegang je nodig hebt
- Eventuele kosten of resources

**🔧 STAP-VOOR-STAP IMPLEMENTATIE**
- Concrete actiestappen
- Volgorde van uitvoering
- Veelgemaakte fouten vermijden
- Best practices voor Nederlandse markt

**✅ CONTROLE & VALIDATIE**
- Hoe te controleren of het werkt
- Welke metrics te volgen
- Test procedures
- Troubleshooting tips

**📊 RESULTATEN METEN**
- Welke KPI's belangrijk zijn
- Hoe lang het duurt voor resultaten zichtbaar zijn
- Hoe voortgang te monitoren
- Wanneer bij te stellen

Geef ook aan:
- Geschatte tijdsinvestering
- Moeilijkheidsgraad
- Wanneer hulp van een specialist nodig is
- Nederlandse tools en resources die helpen"""

    @staticmethod
    def get_monitoring_prompt(business_profile: Dict[str, Any]) -> str:
        """
        Get prompt for SEO monitoring and maintenance.

        Args:
            business_profile: Business information

        Returns:
            Monitoring guidance prompt in Dutch
        """
        business_name = business_profile.get("business_name", "het bedrijf")

        return f"""SEO monitoring en onderhoud voor {business_name}

**🎯 MAANDELIJKSE SEO CONTROLES**

1. **Rankings volgen**
   - Belangrijkste zoekwoorden monitoren
   - Concurrentie positie bekijken
   - Nederlandse trend analyses

2. **Website prestaties**
   - Snelheid tests (Core Web Vitals)
   - Mobile-first indexing status
   - Technische SEO health check

3. **Content prestaties**
   - Welke pagina's presteren goed
   - Nieuwe content kansen identificeren
   - Gebruikersgedrag analyseren

4. **Link profiel onderhoud**
   - Nieuwe links controleren
   - Schadelijke links opsporen
   - Link building kansen

**📊 BELANGRIJKSTE METRICS VOOR NEDERLANDSE MARKT**
- Organisch verkeer uit Nederland
- Local search prestaties
- Google Mijn Bedrijf statistieken
- Conversies uit organisch verkeer
- Brand awareness zoekopdrachten

**🚨 WAARSCHUWINGSSIGNALEN**
- Plotselinge ranking dalingen
- Technische problemen
- Negatieve reviews impact
- Concurrentie bewegingen

**🔧 GRATIS NEDERLANDSE SEO TOOLS**
- Google Search Console (Nederlandse data)
- Google Analytics 4 (Nederlandse segmentatie)
- Google Mijn Bedrijf insights
- Gratis ranking tools voor .nl

Geef een persoonlijk monitoring schema voor {business_name} met:
- Welke metrics het belangrijkst zijn
- Hoe vaak te controleren
- Welke tools te gebruiken
- Wanneer actie nodig is"""
