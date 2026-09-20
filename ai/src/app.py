"""Flask application for AI Service HTTP API with Strands Agents SDK integration."""
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from .llm_client import LLMClient
from .conversation import ConversationAgent
from .listing_generator import ListingGenerator
from .strands_wrapper import StrandsAgentWrapper
from .config import AI_SERVICE_PORT

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize LLM client and conversation logic
llm_client = LLMClient()
conversation_agent = ConversationAgent(llm_client)
listing_generator = ListingGenerator(llm_client)

# Initialize Strands Agent wrapper (Build It requirement)
strands_agent = StrandsAgentWrapper(conversation_agent, listing_generator)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/agent/converse", methods=["POST"])
def converse():
    """Handle one turn of seller onboarding conversation."""
    try:
        data = request.get_json()

        # Extract parameters
        seller_id = data.get("seller_id")
        conversation_id = data.get("conversation_id")
        message_text = data.get("message_text")
        seller_language = data.get("seller_language", "hi")

        # Validate required fields
        if not seller_id or not message_text:
            return jsonify({
                "error": {
                    "code": "invalid_request",
                    "message": "seller_id and message_text are required"
                }
            }), 400

        # Process message through Strands Agent wrapper
        result = strands_agent.process_conversation_turn(
            seller_id=seller_id,
            conversation_id=conversation_id,
            message_text=message_text,
            seller_language=seller_language
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": str(e)
            }
        }), 500


@app.route("/agent/generate-listing", methods=["POST"])
def generate_listing():
    """Generate structured listing from conversation."""
    try:
        data = request.get_json()

        # Extract parameters
        seller_id = data.get("seller_id")
        conversation_id = data.get("conversation_id")

        # Validate required fields
        if not seller_id or not conversation_id:
            return jsonify({
                "error": {
                    "code": "invalid_request",
                    "message": "seller_id and conversation_id are required"
                }
            }), 400

        # Get conversation state
        state = conversation_agent.get_state(conversation_id)
        if not state:
            return jsonify({
                "error": {
                    "code": "not_found",
                    "message": "Conversation not found"
                }
            }), 404

        # Generate listing through Strands Agent wrapper
        listing = strands_agent.generate_listing(seller_id, conversation_id)

        return jsonify(listing), 200

    except Exception as e:
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": str(e)
            }
        }), 500


@app.route("/agent/noble-cause-note", methods=["POST"])
def noble_cause_note():
    """Generate buyer-facing noble cause note."""
    try:
        data = request.get_json()

        # Extract parameters
        story = data.get("story", "")
        buyer_language = data.get("buyer_language", "en")
        opted_in = data.get("opted_in", False)

        # Generate note through Strands Agent wrapper
        note = strands_agent.generate_noble_cause_note(
            story=story,
            buyer_language=buyer_language,
            opted_in=opted_in
        )

        return jsonify({"noble_cause_note": note}), 200

    except Exception as e:
        return jsonify({
            "error": {
                "code": "internal_error",
                "message": str(e)
            }
        }), 500


def create_app():
    """Application factory."""
    return app


if __name__ == "__main__":
    port = AI_SERVICE_PORT
    print(f"Starting AI Service on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
