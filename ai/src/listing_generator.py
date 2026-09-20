"""Listing generation from conversation state."""
import uuid
from typing import Dict, Any, List
from .llm_client import LLMClient
from .conversation import ConversationState
from .config import CATEGORY_GUIDANCE


class ListingGenerator:
    """Generates structured listings from conversation state."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate_listing(
        self,
        seller_id: str,
        conversation_state: ConversationState
    ) -> Dict[str, Any]:
        """Generate a structured Listing object from conversation state."""
        draft = conversation_state.draft_state
        category = draft.get("category", "handicraft")

        # Validate we have minimum required info
        compliance_flags = self._check_compliance(draft, category)

        # Generate listing fields using LLM
        try:
            listing_data = self._generate_with_llm(draft, category)
        except Exception as e:
            # Fallback to partial generation
            listing_data = self._generate_fallback(draft, category)
            compliance_flags.append("llm_generation_failed")

        # Build the Listing object
        listing = {
            "listing_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),  # Backend will replace with actual product_id
            "category": category,
            "listing_title": listing_data.get("listing_title", f"{category.title()} Product"),
            "description_en": listing_data.get("description_en", "Handcrafted product from rural India"),
            "description_local": listing_data.get("description_local", draft.get("raw_description", "")),
            "price_suggestion": listing_data.get("price_suggestion", 500),
            "photo_guidance": CATEGORY_GUIDANCE[category]["photo_guidance"],
            "story": listing_data.get("story", ""),
            "compliance_flags": compliance_flags,
            "review_status": "pending",
            "created_at": None  # Backend will set
        }

        return listing

    def _generate_with_llm(self, draft: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Generate listing fields using LLM."""
        raw_desc = draft.get("raw_description", "")
        responses = " ".join(draft.get("seller_responses", []))

        prompt = f"""You are creating an Amazon product listing for a rural Indian seller.

Category: {category}
Seller's description (Hindi): {raw_desc}
Additional details: {responses}

Generate a JSON object with these fields:
- listing_title: Short, catchy English title (5-8 words)
- description_en: Detailed English description (2-3 sentences) highlighting quality and origin
- description_local: Hindi description (2-3 sentences)
- price_suggestion: Reasonable price in INR (integer)
- story: A warm 2-sentence story about the seller and craftsmanship for buyers

Respond with ONLY valid JSON, no other text."""

        system = "You are an expert at creating compelling product listings for handcrafted items."

        result = self.llm.generate_json(prompt, system)

        # If LLM returned error, raise exception to trigger fallback
        if "error" in result:
            raise ValueError("LLM returned malformed JSON")

        return result

    def _generate_fallback(self, draft: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Generate a basic listing when LLM fails."""
        raw_desc = draft.get("raw_description", "")

        return {
            "listing_title": f"Handcrafted {category.title()} from Rural India",
            "description_en": f"Authentic {category} made by rural artisan. {raw_desc[:100]}",
            "description_local": raw_desc,
            "price_suggestion": 500,
            "story": f"This {category} is carefully crafted by a rural artisan, bringing traditional skills to your home."
        }

    def _check_compliance(self, draft: Dict[str, Any], category: str) -> List[str]:
        """Check for missing required information based on category."""
        flags = []

        # Get category-specific compliance requirements
        required_checks = CATEGORY_GUIDANCE[category]["compliance_checks"]
        responses = draft.get("seller_responses", [])

        # Basic checks
        if not draft.get("raw_description"):
            flags.append("missing_description")

        if len(responses) < 2:
            flags.append("insufficient_details")

        # Category-specific checks (simple keyword detection)
        for check in required_checks:
            # This is a simplified check - in production would be more sophisticated
            if check == "age_range" and category == "toy":
                if not any(word in " ".join(responses).lower() for word in ["age", "उम्र", "साल", "year"]):
                    flags.append("missing_age_range")

            elif check == "shelf_life" and category == "food":
                if not any(word in " ".join(responses).lower() for word in ["दिन", "महीना", "days", "shelf", "ताज़ा"]):
                    flags.append("missing_shelf_life")

        return flags

    def generate_noble_cause_note(
        self,
        story: str,
        buyer_language: str,
        opted_in: bool
    ) -> str:
        """Generate buyer-facing noble cause note."""
        if not opted_in:
            # Only show seller story, no community impact mention
            if buyer_language == "hi":
                return f"{story}"
            return story

        # Include community impact if seller opted in
        impact_line_en = " A portion of proceeds supports local community development."
        impact_line_hi = " इस बिक्री का कुछ हिस्सा स्थानीय समुदाय के विकास में योगदान देता है।"

        if buyer_language == "hi":
            return f"{story}{impact_line_hi}"
        else:
            return f"{story}{impact_line_en}"
