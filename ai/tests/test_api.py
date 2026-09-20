"""Tests for Flask API endpoints."""
import pytest
import json
from src.app import create_app
from src.llm_client import MockLLMClient
from src import app as app_module


@pytest.fixture
def client():
    """Create test client with mocked LLM."""
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as test_client:
        # Create fresh mock for each test
        mock_llm = MockLLMClient()
        mock_llm.set_responses([
            {
                "listing_title": "Homemade Pickle - Traditional Recipe",
                "description_en": "Authentic homemade pickle made with traditional spices.",
                "description_local": "घर का बना अचार, पारंपरिक मसालों के साथ",
                "price_suggestion": 250,
                "story": "This pickle is lovingly prepared by a rural artisan."
            }
        ])
        app_module.llm_client = mock_llm
        app_module.conversation_agent.llm = mock_llm
        app_module.listing_generator.llm = mock_llm
        yield test_client


class TestAPIEndpoints:
    """Test the HTTP API endpoints."""

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

    def test_converse_endpoint_valid_request(self, client):
        """Test /agent/converse with valid request."""
        payload = {
            "seller_id": "test-seller-123",
            "conversation_id": None,
            "message_text": "नमस्ते",
            "seller_language": "hi"
        }

        response = client.post(
            '/agent/converse',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "conversation_id" in data
        assert "ai_reply_text" in data
        assert "stage" in data
        assert "draft_state" in data
        assert data["stage"] == "idea"

    def test_converse_endpoint_missing_fields(self, client):
        """Test /agent/converse with missing required fields."""
        payload = {
            "seller_id": "test-seller-123"
            # Missing message_text
        }

        response = client.post(
            '/agent/converse',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_converse_endpoint_conversation_continuity(self, client):
        """Test that conversation_id maintains state across turns."""
        # First turn
        payload1 = {
            "seller_id": "test-seller",
            "conversation_id": None,
            "message_text": "नमस्ते",
            "seller_language": "hi"
        }

        response1 = client.post(
            '/agent/converse',
            data=json.dumps(payload1),
            content_type='application/json'
        )

        data1 = json.loads(response1.data)
        conv_id = data1["conversation_id"]

        # Second turn with same conversation_id
        payload2 = {
            "seller_id": "test-seller",
            "conversation_id": conv_id,
            "message_text": "हाँ, बताइए",
            "seller_language": "hi"
        }

        response2 = client.post(
            '/agent/converse',
            data=json.dumps(payload2),
            content_type='application/json'
        )

        data2 = json.loads(response2.data)

        # Should have same conversation_id and advanced stage
        assert data2["conversation_id"] == conv_id
        assert data2["stage"] != data1["stage"]

    def test_generate_listing_endpoint_valid_request(self, client):
        """Test /agent/generate-listing with valid request."""
        # First create a conversation and advance to capture stage with product info
        conv_id = None
        messages = ["नमस्ते", "हाँ", "ठीक है", "मैं अचार बेचती हूं", "आम, नमक", "दो महीने", "ठंडी जगह"]

        for msg in messages:
            conv_payload = {
                "seller_id": "test-seller",
                "conversation_id": conv_id,
                "message_text": msg,
                "seller_language": "hi"
            }

            conv_response = client.post(
                '/agent/converse',
                data=json.dumps(conv_payload),
                content_type='application/json'
            )

            conv_data = json.loads(conv_response.data)
            conv_id = conv_data["conversation_id"]

        # Now generate listing
        listing_payload = {
            "seller_id": "test-seller",
            "conversation_id": conv_id
        }

        response = client.post(
            '/agent/generate-listing',
            data=json.dumps(listing_payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "listing_id" in data
        assert "category" in data
        assert "listing_title" in data
        assert "review_status" in data
        assert data["review_status"] == "pending"

    def test_generate_listing_endpoint_missing_conversation(self, client):
        """Test /agent/generate-listing with non-existent conversation."""
        payload = {
            "seller_id": "test-seller",
            "conversation_id": "non-existent-id"
        }

        response = client.post(
            '/agent/generate-listing',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_noble_cause_note_endpoint_without_opt_in(self, client):
        """Test /agent/noble-cause-note when not opted in."""
        payload = {
            "story": "A beautiful handicraft from rural India.",
            "buyer_language": "en",
            "opted_in": False
        }

        response = client.post(
            '/agent/noble-cause-note',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "noble_cause_note" in data
        # Should not mention community contribution
        assert "community" not in data["noble_cause_note"].lower()

    def test_noble_cause_note_endpoint_with_opt_in(self, client):
        """Test /agent/noble-cause-note when opted in."""
        payload = {
            "story": "A beautiful handicraft from rural India.",
            "buyer_language": "en",
            "opted_in": True
        }

        response = client.post(
            '/agent/noble-cause-note',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "noble_cause_note" in data
        # Should mention community contribution
        note = data["noble_cause_note"].lower()
        assert "community" in note or "development" in note
