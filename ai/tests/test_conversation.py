"""Tests for conversation flow.

These tests exercise the LLM-driven idea/procedure/business_model stages and LLM-based
category detection by feeding MockLLMClient canned JSON responses (reply_text/ready_to_advance
for narrative stages, category for classification, addressed/gentle_followup for capture
answer-checking) and asserting the conversation reacts to those mocked judgments - not to
keyword matching in the test input. Fallback (keyword-based) behaviour is exercised separately
by leaving MockLLMClient with no/invalid canned responses for a given call.
"""
import pytest
from src.llm_client import MockLLMClient
from src.conversation import ConversationAgent, ConversationState


class TestConversationFlow:
    """Test the full conversation flow through all stages."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = MockLLMClient()
        self.agent = ConversationAgent(self.mock_llm)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _advance_to_business_model(self):
        """Walk idea -> procedure -> business_model via mocked LLM JSON, returning conv_id."""
        conv_id = None

        # idea, turn 1: always just the intro, regardless of ready_to_advance.
        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते! Amazon Kalaa Setu में आपका स्वागत है।", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]
        assert result["stage"] == "idea"

        # idea, turn 2: LLM says ready -> advance to procedure.
        self.mock_llm.set_responses([
            {"reply_text": "बढ़िया! अब मैं बताता हूं कि यह कैसे काम करता है...", "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="हाँ, बताइए", seller_language="hi"
        )
        assert result["stage"] == "procedure"

        # procedure: LLM says ready -> advance to business_model.
        self.mock_llm.set_responses([
            {"reply_text": "समझ गया! अब पैसों के बारे में बताता हूं...", "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="समझ आ गया", seller_language="hi"
        )
        assert result["stage"] == "business_model"

        return conv_id

    def _enter_capture_with_category(self, category: str, description: str):
        """Walk all the way into 'capture' with a given category already detected."""
        conv_id = self._advance_to_business_model()

        self.mock_llm.set_responses([
            {"reply_text": "बहुत अच्छा! अब अपने उत्पाद के बारे में बताइए।", "ready_to_advance": True},
            {"category": category},
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text=description, seller_language="hi"
        )
        assert result["stage"] == "capture"
        assert result["draft_state"]["category"] == category
        return conv_id, result

    # ------------------------------------------------------------------
    # idea / procedure / business_model driven by mocked ready_to_advance
    # ------------------------------------------------------------------

    def test_idea_stage_advances_when_llm_says_ready(self):
        """idea -> procedure should happen only because the mocked LLM said ready_to_advance."""
        conv_id = None

        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते! Amazon Kalaa Setu में आपका स्वागत है।", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]
        assert result["stage"] == "idea"

        reply_text = "बढ़िया! अब मैं बताता हूं कि यह कैसे काम करता है..."
        self.mock_llm.set_responses([
            {"reply_text": reply_text, "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="कुछ भी", seller_language="hi"
        )

        assert result["stage"] == "procedure"
        assert result["ai_reply_text"] == reply_text

    def test_idea_stage_stays_when_llm_says_not_ready(self):
        """idea should NOT advance just because a keyword is present, if the LLM says not ready."""
        conv_id = None

        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते! Amazon Kalaa Setu में आपका स्वागत है।", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]

        reply_text = "कृपया थोड़ा और बताएं, क्या आप समझ पाए?"
        self.mock_llm.set_responses([
            {"reply_text": reply_text, "ready_to_advance": False}
        ])
        # Message contains an interest keyword ("हाँ") - but the mocked LLM still says
        # not ready, so keyword content must NOT override the model's own judgment.
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="हाँ", seller_language="hi"
        )

        assert result["stage"] == "idea"
        assert result["ai_reply_text"] == reply_text

    def test_procedure_stage_advances_when_llm_says_ready(self):
        """procedure -> business_model driven purely by the mocked ready_to_advance flag."""
        conv_id = None
        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते! स्वागत है।", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]

        self.mock_llm.set_responses([
            {"reply_text": "चलिए प्रक्रिया समझते हैं...", "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="ठीक है", seller_language="hi"
        )
        assert result["stage"] == "procedure"

        reply_text = "बहुत बढ़िया! अब पैसों के बारे में बताता हूँ..."
        self.mock_llm.set_responses([
            {"reply_text": reply_text, "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="समझ गया", seller_language="hi"
        )

        assert result["stage"] == "business_model"
        assert result["ai_reply_text"] == reply_text

    def test_business_model_stage_advances_and_detects_category(self):
        """business_model -> capture, with LLM-based category detection on the same message."""
        conv_id = self._advance_to_business_model()

        reply_text = "बहुत अच्छा! अब अपने उत्पाद के बारे में बताइए।"
        self.mock_llm.set_responses([
            {"reply_text": reply_text, "ready_to_advance": True},
            {"category": "toy"},
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="मैं लकड़ी के खिलौने बनाता हूं", seller_language="hi"
        )

        assert result["stage"] == "capture"
        assert result["draft_state"]["category"] == "toy"

    def test_business_model_stage_stays_when_llm_says_not_ready(self):
        """business_model should not advance when the mocked LLM says the seller isn't ready."""
        conv_id = None
        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते!", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]

        self.mock_llm.set_responses([
            {"reply_text": "चलिए प्रक्रिया समझते हैं...", "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="ठीक है", seller_language="hi"
        )
        assert result["stage"] == "procedure"

        self.mock_llm.set_responses([
            {"reply_text": "अब पैसों के बारे में बताता हूं...", "ready_to_advance": True}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="ठीक है", seller_language="hi"
        )
        assert result["stage"] == "business_model"

        reply_text = "कोई बात नहीं, फिर से बताता हूं..."
        self.mock_llm.set_responses([
            {"reply_text": reply_text, "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="???", seller_language="hi"
        )

        assert result["stage"] == "business_model"
        assert result["ai_reply_text"] == reply_text

    # ------------------------------------------------------------------
    # malformed LLM output -> graceful keyword-based fallback
    # ------------------------------------------------------------------

    def test_malformed_llm_json_falls_back_to_keyword_advance(self):
        """A broken (non-JSON) LLM response for a stage transition must not crash the service."""
        conv_id = None
        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते! स्वागत है।", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]

        # Malformed JSON - MockLLMClient.generate_json will return {"error": ..., "raw_text": ...}
        self.mock_llm.set_responses(["This is not JSON at all!"])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="हाँ, ठीक है", seller_language="hi"
        )

        # Falls back to the keyword-based safety net instead of crashing/500-ing.
        assert result["stage"] == "procedure"
        assert len(result["ai_reply_text"]) > 0

    def test_missing_fields_in_llm_json_falls_back(self):
        """A JSON response missing the required fields must also trigger the fallback path."""
        conv_id = None
        self.mock_llm.set_responses([
            {"reply_text": "नमस्ते! स्वागत है।", "ready_to_advance": False}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="नमस्ते", seller_language="hi"
        )
        conv_id = result["conversation_id"]

        # Valid JSON, but wrong shape (e.g. a listing-shaped object instead of reply_text/
        # ready_to_advance) - should be treated as invalid and trigger the fallback.
        self.mock_llm.set_responses([
            {"listing_title": "Not the schema we asked for"}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="हाँ, ठीक है", seller_language="hi"
        )

        assert result["stage"] == "procedure"
        assert len(result["ai_reply_text"]) > 0

    # ------------------------------------------------------------------
    # category detection: LLM-based, with fallback + clarifying question
    # ------------------------------------------------------------------

    def test_category_unclear_asks_exactly_one_clarifying_question(self):
        """If the LLM (and the keyword fallback) can't decide, ask one clarifying question."""
        conv_id = self._advance_to_business_model()

        self.mock_llm.set_responses([
            {"reply_text": "ठीक है, अब अपने उत्पाद के बारे में बताइए।", "ready_to_advance": True},
            {"category": "unclear"},
        ])
        # Deliberately vague - doesn't match any keyword either.
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="मैं कुछ अच्छी चीज़ें बनाता हूं", seller_language="hi"
        )

        assert result["stage"] == "capture"
        assert result["draft_state"]["category"] is None
        assert "किस तरह" in result["ai_reply_text"] or "category" in result["ai_reply_text"].lower()

    def test_category_unclear_llm_falls_back_to_keyword_match(self):
        """Even if the LLM says 'unclear', a matching keyword in the message should still work."""
        conv_id = self._advance_to_business_model()

        self.mock_llm.set_responses([
            {"reply_text": "ठीक है, अब अपने उत्पाद के बारे में बताइए।", "ready_to_advance": True},
            {"category": "unclear"},
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="मैं हाथ से बुनी साड़ी बेचता हूं", seller_language="hi"
        )

        assert result["stage"] == "capture"
        assert result["draft_state"]["category"] == "textile"

    # ------------------------------------------------------------------
    # capture: adaptive answer checking
    # ------------------------------------------------------------------

    def test_capture_stage_gentle_followup_when_answer_not_addressed(self):
        """An answer that didn't address the question should get a gentle follow-up, not advance."""
        conv_id, _ = self._enter_capture_with_category("food", "मैं घर का बना अचार बेचना चाहता हूं")

        follow_up = "कृपया बताइए - इसमें कौन-कौन सी सामग्री है?"
        self.mock_llm.set_responses([
            {"addressed": False, "gentle_followup": follow_up}
        ])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="पता नहीं", seller_language="hi"
        )

        assert result["stage"] == "capture"
        assert result["ai_reply_text"] == follow_up
        assert len(result["draft_state"]["seller_responses"]) == 0

    def test_capture_stage_advances_question_when_answer_addressed(self):
        """An answer the LLM judges as addressing the question should be stored and move on."""
        conv_id, first = self._enter_capture_with_category("food", "मैं घर का बना अचार बेचना चाहता हूं")
        assert len(first["draft_state"]["questions_asked"]) == 1

        self.mock_llm.set_responses([{"addressed": True, "gentle_followup": ""}])
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="आम, नमक, मिर्च, तेल", seller_language="hi"
        )

        assert result["stage"] == "capture"
        assert len(result["draft_state"]["seller_responses"]) == 1
        assert len(result["draft_state"]["questions_asked"]) == 2

    # ------------------------------------------------------------------
    # full happy-path conversations, LLM-driven, for two categories
    # ------------------------------------------------------------------

    def test_food_category_full_flow_llm_driven(self):
        """idea -> done for the food category, driven entirely by mocked LLM JSON."""
        conv_id, _ = self._enter_capture_with_category("food", "मैं घर का बना अचार बेचना चाहता हूं")

        result = None
        for i in range(3):
            self.mock_llm.set_responses([{"addressed": True, "gentle_followup": ""}])
            result = self.agent.process_message(
                seller_id="test-seller", conversation_id=conv_id,
                message_text=f"जवाब {i + 1}", seller_language="hi"
            )

        assert result["stage"] == "done"
        assert result["draft_state"]["category"] == "food"
        assert len(result["draft_state"]["seller_responses"]) == 3

    def test_textile_category_full_flow_llm_driven(self):
        """idea -> done for the textile category, driven entirely by mocked LLM JSON."""
        conv_id, first = self._enter_capture_with_category("textile", "मैं हाथ से बुनी साड़ी बेचता हूं")
        assert "कपड़" in first["ai_reply_text"] or "सामग्री" in first["ai_reply_text"]

        result = None
        for i in range(3):
            self.mock_llm.set_responses([{"addressed": True, "gentle_followup": ""}])
            result = self.agent.process_message(
                seller_id="test-seller", conversation_id=conv_id,
                message_text=f"जवाब {i + 1}", seller_language="hi"
            )

        assert result["stage"] == "done"
        assert result["draft_state"]["category"] == "textile"
        assert len(result["draft_state"]["seller_responses"]) == 3

    # ------------------------------------------------------------------
    # remaining edge cases (KARTIKAY_TASK.md Section 5.1)
    # ------------------------------------------------------------------

    def test_off_topic_response_handling(self):
        """Very short/off-topic first replies should be re-asked gently, never crash."""
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=None,
            message_text="hi", seller_language="hi"
        )
        conv_id = result["conversation_id"]

        # No canned LLM response set -> exercises the fallback path.
        result = self.agent.process_message(
            seller_id="test-seller", conversation_id=conv_id,
            message_text="k", seller_language="hi"
        )

        assert result["stage"] == "idea"
        assert len(result["ai_reply_text"]) > 0

    def test_mixed_hindi_english_input_does_not_crash(self):
        """Mixed Hindi/English seller input must be handled gracefully."""
        conv_id, result = self._enter_capture_with_category(
            "handicraft", "I make handicraft, हाथ से बना है"
        )
        assert result["stage"] == "capture"
        assert result["draft_state"]["category"] == "handicraft"
