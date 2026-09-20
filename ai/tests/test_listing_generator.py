"""Tests for listing generation."""
import pytest
from src.llm_client import MockLLMClient
from src.listing_generator import ListingGenerator
from src.conversation import ConversationState


class TestListingGenerator:
    """Test listing generation from conversation state."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = MockLLMClient()
        self.generator = ListingGenerator(self.mock_llm)

    def test_generate_listing_with_valid_state(self):
        """Test generating a listing with valid conversation state."""
        # Create a complete conversation state
        state = ConversationState()
        state.stage = "done"
        state.draft_state = {
            "category": "food",
            "raw_description": "मैं घर का बना आम का अचार बेचती हूं",
            "seller_responses": [
                "आम, नमक, मिर्च, सरसों का तेल",
                "दो महीने तक ताज़ा रहता है",
                "ठंडी जगह पर रखें"
            ],
            "questions_asked": ["सामग्री?", "shelf life?", "storage?"]
        }

        # Set mock LLM response
        self.mock_llm.set_responses([
            {
                "listing_title": "Homemade Mango Pickle - Traditional Recipe",
                "description_en": "Authentic homemade mango pickle made with traditional spices. Fresh and flavorful.",
                "description_local": "घर का बना आम का अचार, पारंपरिक मसालों के साथ",
                "price_suggestion": 250,
                "story": "This pickle is lovingly prepared by a rural artisan using age-old family recipes."
            }
        ])

        listing = self.generator.generate_listing("seller-123", state)

        # Verify structure
        assert "listing_id" in listing
        assert "product_id" in listing
        assert listing["category"] == "food"
        assert listing["listing_title"] == "Homemade Mango Pickle - Traditional Recipe"
        assert listing["description_en"] != ""
        assert listing["price_suggestion"] == 250
        assert listing["review_status"] == "pending"
        assert isinstance(listing["photo_guidance"], list)
        assert len(listing["photo_guidance"]) > 0

    def test_generate_listing_with_llm_failure(self):
        """Test fallback when LLM returns malformed JSON."""
        state = ConversationState()
        state.stage = "done"
        state.draft_state = {
            "category": "handicraft",
            "raw_description": "मैं लकड़ी के खिलौने बनाता हूं",
            "seller_responses": ["लकड़ी", "15 cm लंबा"],
            "questions_asked": []
        }

        # Mock LLM to return invalid JSON
        self.mock_llm.set_responses(["This is not JSON at all!"])

        listing = self.generator.generate_listing("seller-123", state)

        # Should still return a valid listing with fallback
        assert listing["category"] == "handicraft"
        assert "listing_title" in listing
        assert "Handcrafted" in listing["listing_title"]
        assert "llm_generation_failed" in listing["compliance_flags"]

    def test_compliance_flags_for_insufficient_details(self):
        """Test that compliance flags are raised for missing information."""
        state = ConversationState()
        state.stage = "capture"
        state.draft_state = {
            "category": "toy",
            "raw_description": "खिलौना",
            "seller_responses": [],  # Insufficient
            "questions_asked": []
        }

        self.mock_llm.set_responses([
            {
                "listing_title": "Toy",
                "description_en": "A toy",
                "description_local": "खिलौना",
                "price_suggestion": 100,
                "story": "A toy story"
            }
        ])

        listing = self.generator.generate_listing("seller-123", state)

        assert "insufficient_details" in listing["compliance_flags"]

    def test_noble_cause_note_without_opt_in(self):
        """Test noble cause note when seller has NOT opted in."""
        story = "This handicraft is made by a village artisan."

        note = self.generator.generate_noble_cause_note(
            story=story,
            buyer_language="en",
            opted_in=False
        )

        # Should only show story, no community impact mention
        assert story in note
        assert "community" not in note.lower()
        assert "development" not in note.lower()

    def test_noble_cause_note_with_opt_in(self):
        """Test noble cause note when seller HAS opted in."""
        story = "This handicraft is made by a village artisan."

        note = self.generator.generate_noble_cause_note(
            story=story,
            buyer_language="en",
            opted_in=True
        )

        # Should include community impact
        assert story in note
        assert "community" in note.lower() or "development" in note.lower()

    def test_noble_cause_note_hindi_with_opt_in(self):
        """Test noble cause note in Hindi with opt-in."""
        story = "यह हस्तशिल्प एक गांव के कारीगर द्वारा बनाया गया है।"

        note = self.generator.generate_noble_cause_note(
            story=story,
            buyer_language="hi",
            opted_in=True
        )

        assert story in note
        assert "समुदाय" in note or "विकास" in note

    def test_all_categories_have_photo_guidance(self):
        """Test that all categories produce photo guidance."""
        categories = ["food", "textile", "toy", "handicraft"]

        for category in categories:
            state = ConversationState()
            state.stage = "done"
            state.draft_state = {
                "category": category,
                "raw_description": f"A {category} item",
                "seller_responses": ["detail 1", "detail 2", "detail 3"],
                "questions_asked": []
            }

            self.mock_llm.set_responses([
                {
                    "listing_title": f"Test {category}",
                    "description_en": f"A {category}",
                    "description_local": f"एक {category}",
                    "price_suggestion": 500,
                    "story": f"A {category} story"
                }
            ])

            listing = self.generator.generate_listing("seller-123", state)

            assert len(listing["photo_guidance"]) > 0
            assert isinstance(listing["photo_guidance"], list)
