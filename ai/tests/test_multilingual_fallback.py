"""Tier-2 multilingual tests: the deterministic fallback / safety-net paths.

These paths only run when the LLM fails/returns junk, or in fixed (non-LLM) branches. They must:
  * keep Hindi output EXACTLY as before (pinned string-for-string below),
  * work in English,
  * fall back to English for every other language (no hand-translation into 7 languages),
  * never surface an Ollama transport error (RuntimeError) as a 500.
"""
import json
import re

import pytest

from src import app as app_module
from src.app import create_app
from src.config import (
    CATEGORY_GUIDANCE,
    FALLBACK_MESSAGES,
    STAGE_DESCRIPTIONS,
    get_category_questions,
    get_fallback_message,
    get_interest_keywords,
    get_stage_description,
    resolve_fallback_lang,
)
from src.conversation import ConversationAgent, ConversationState
from src.llm_client import LLMClient, MockLLMClient

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
CATEGORIES = ["food", "textile", "toy", "handicraft"]
STAGES = ["idea", "procedure", "business_model", "capture"]


def has_devanagari(text: str) -> bool:
    return bool(DEVANAGARI.search(text))


class RaisingLLM(LLMClient):
    """Simulates Ollama being down / model missing (LLMClient.generate raises RuntimeError)."""

    def generate(self, prompt, system=None):
        raise RuntimeError("LLM request failed: 404 Client Error: Not Found for url")


# ----------------------------------------------------------------------
# config helpers
# ----------------------------------------------------------------------

class TestConfigShape:
    def test_every_stage_has_hi_and_en(self):
        for stage in STAGES:
            assert set(STAGE_DESCRIPTIONS[stage]) >= {"hi", "en"}
            assert has_devanagari(STAGE_DESCRIPTIONS[stage]["hi"])
            assert not has_devanagari(STAGE_DESCRIPTIONS[stage]["en"])

    @pytest.mark.parametrize("category", CATEGORIES)
    def test_question_lists_same_length_across_languages(self, category):
        qs = CATEGORY_GUIDANCE[category]["questions"]
        assert set(qs) >= {"hi", "en"}
        # capture logic indexes by len(questions_asked) - lengths MUST match
        assert len({len(v) for v in qs.values()}) == 1
        assert all(not has_devanagari(q) for q in qs["en"])

    @pytest.mark.parametrize("category", CATEGORIES)
    def test_listing_generator_keys_untouched(self, category):
        g = CATEGORY_GUIDANCE[category]
        assert isinstance(g["compliance_checks"], list) and g["compliance_checks"]
        assert isinstance(g["photo_guidance"], list) and g["photo_guidance"]

    def test_every_fallback_message_has_hi_and_en(self):
        for key, by_lang in FALLBACK_MESSAGES.items():
            assert has_devanagari(by_lang["hi"]), key
            assert by_lang["en"] and not has_devanagari(by_lang["en"]), key

    @pytest.mark.parametrize("lang,expected", [
        ("hi", "hi"), ("en", "en"), ("en-IN", "en"), ("EN_in", "en"), ("hi-IN", "hi"),
        ("ta", "en"), ("te", "en"), ("bn", "en"), ("pa", "en"), ("xx", "en"),
        (None, "hi"), ("", "hi"),   # missing language keeps the historical Hindi default
    ])
    def test_resolve_fallback_lang(self, lang, expected):
        assert resolve_fallback_lang(lang) == expected

    def test_unsupported_language_gets_english_text(self):
        for lang in ["ta", "te", "bn", "mr", "gu", "kn", "pa"]:
            assert get_stage_description("idea", lang) == STAGE_DESCRIPTIONS["idea"]["en"]
            assert get_category_questions("food", lang) == CATEGORY_GUIDANCE["food"]["questions"]["en"]
            assert get_fallback_message("done", lang) == FALLBACK_MESSAGES["done"]["en"]

    def test_interest_keywords_per_language(self):
        assert get_interest_keywords("hi") == ["हाँ", "ठीक", "अच्छा", "जी", "ok", "yes"]
        en = get_interest_keywords("en")
        assert {"yes", "ok", "okay", "sure", "interested"} <= set(en)
        combined = get_interest_keywords("ta")   # no dedicated list -> combined
        assert "हाँ" in combined and "sure" in combined


# ----------------------------------------------------------------------
# Hindi must not regress: pin the exact literals that used to be inline
# ----------------------------------------------------------------------

class TestHindiPinned:
    def test_hindi_literals_exact(self):
        assert get_fallback_message("done", "hi") == "धन्यवाद! आपकी जानकारी पूरी हो गई है।"
        assert get_fallback_message("idea_reask", "hi") == (
            "कृपया बताइए - क्या आप अपने उत्पाद को इस बाज़ार में बेचना चाहेंगे?")
        assert get_fallback_message("ask_category_suffix", "hi") == (
            "पहले बताइए - यह किस तरह का उत्पाद है? (खाना, कपड़ा, खिलौना, या हस्तशिल्प?)")
        assert get_fallback_message("category_not_understood", "hi") == (
            "मुझे समझ नहीं आया। कृपया बताइए - यह खाना है, कपड़ा है, खिलौना है, या हस्तशिल्प?")
        assert get_fallback_message("capture_max_turns", "hi") == (
            "बहुत अच्छा! जितनी जानकारी मिली उसके आधार पर हम आपके लिए एक listing तैयार करेंगे।")
        assert get_fallback_message("clarify_prefix", "hi") == "धन्यवाद, लेकिन कृपया थोड़ा और स्पष्ट बताएं - "
        assert get_fallback_message("capture_complete", "hi") == (
            "बहुत अच्छा! मैंने सारी जानकारी इकट्ठा कर ली है। अब हम आपके लिए एक listing तैयार करेंगे।")
        assert get_fallback_message("ask_more", "hi") == "कुछ और बताइए - कोई खास बात इस उत्पाद के बारे में?"
        assert get_fallback_message("first_question_prefix", "hi") == "अच्छा! "

    def test_hindi_questions_exact(self):
        assert get_category_questions("food", "hi")[0] == "क्या आप बता सकते हैं कि इसमें कौन-कौन सी सामग्री है?"
        assert get_category_questions("textile", "hi")[0] == "यह किस कपड़े/सामग्री से बना है?"
        assert get_category_questions("toy", "hi")[2] == "क्या इसमें छोटे हिस्से हैं जो निगले जा सकते हैं?"
        assert get_category_questions("handicraft", "hi")[3] == "क्या इसमें कोई खास तकनीक या परंपरागत शैली है?"

    def test_hindi_first_category_question_reply(self):
        agent = ConversationAgent(MockLLMClient())
        state = ConversationState()
        reply = agent._get_category_question(state, "food")           # default lang == hi
        assert reply == "अच्छा! क्या आप बता सकते हैं कि इसमें कौन-कौन सी सामग्री है?"
        assert state.draft_state["questions_asked"] == [
            "क्या आप बता सकते हैं कि इसमें कौन-कौन सी सामग्री है?"]

    def test_hindi_done_stage_reply(self):
        agent = ConversationAgent(MockLLMClient())
        state = ConversationState()
        state.stage = "done"
        agent.conversations[state.conversation_id] = state
        r = agent.process_message("s", state.conversation_id, "hello", seller_language="hi")
        assert r["ai_reply_text"] == "धन्यवाद! आपकी जानकारी पूरी हो गई है।"

    def test_hindi_narrative_fallback_uses_original_text(self):
        """LLM returns junk on the very first turn -> Hindi stage description, as before."""
        mock = MockLLMClient()
        mock.set_responses(["not json"])
        agent = ConversationAgent(mock)
        r = agent.process_message("s", None, "नमस्ते", seller_language="hi")
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["idea"]["hi"]
        assert r["ai_reply_text"].startswith("नमस्ते! मैं आपको Amazon Kalaa Setu")


# ----------------------------------------------------------------------
# English fallback paths, driven end-to-end through ConversationAgent
# ----------------------------------------------------------------------

class TestEnglishFallbackPaths:
    def setup_method(self):
        self.mock = MockLLMClient()
        self.agent = ConversationAgent(self.mock)

    def _say(self, conv_id, text, lang="en", responses=None):
        self.mock.set_responses(responses or [])
        return self.agent.process_message("s", conv_id, text, seller_language=lang)

    def _to_business_model_via_fallback(self, lang="en"):
        """Walk idea -> procedure -> business_model with the LLM returning nothing usable."""
        r = self._say(None, "hello", lang)
        cid = r["conversation_id"]
        assert r["stage"] == "idea"
        r = self._say(cid, "yes please", lang)
        assert r["stage"] == "procedure"
        r = self._say(cid, "understood", lang)
        assert r["stage"] == "business_model"
        return cid, r

    def test_first_turn_uses_english_stage_description(self):
        r = self._say(None, "hello")
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["idea"]["en"]
        assert not has_devanagari(r["ai_reply_text"])

    def test_idea_to_procedure_and_business_model_fallback_text_is_english(self):
        r = self._say(None, "hello")
        cid = r["conversation_id"]
        r = self._say(cid, "yes please")
        assert r["stage"] == "procedure"
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["procedure"]["en"]
        r = self._say(cid, "understood")
        assert r["stage"] == "business_model"
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["business_model"]["en"]
        # the hard requirement text (single point of contact) survives translation
        assert "CSC" in STAGE_DESCRIPTIONS["procedure"]["en"]

    def test_short_offtopic_reply_gets_english_reask(self):
        cid = self._say(None, "hello")["conversation_id"]
        r = self._say(cid, "?")               # <5 chars, no interest keyword
        assert r["stage"] == "idea"
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["idea_reask"]["en"]

    def test_english_interest_keyword_advances_short_reply(self):
        cid = self._say(None, "hello")["conversation_id"]
        r = self._say(cid, "sure")            # 4 chars: only the keyword list can advance this
        assert r["stage"] == "procedure"

    def test_interest_keywords_are_language_specific(self):
        # "sure" is an English keyword but not in the Hindi list: hi keeps re-asking (unchanged).
        cid = self._say(None, "नमस्ते", "hi")["conversation_id"]
        r = self._say(cid, "sure", "hi")
        assert r["stage"] == "idea"
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["idea_reask"]["hi"]

    def test_hindi_keyword_still_advances_in_hindi(self):
        cid = self._say(None, "नमस्ते", "hi")["conversation_id"]
        r = self._say(cid, "हाँ", "hi")
        assert r["stage"] == "procedure"
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["procedure"]["hi"]

    def test_capture_entry_with_category_is_english(self):
        cid, _ = self._to_business_model_via_fallback()
        r = self._say(cid, "I sell homemade pickle", responses=[
            {"reply_text": "Great, tell me about your product.", "ready_to_advance": True},
            {"category": "food"},
        ])
        assert r["stage"] == "capture"
        assert r["draft_state"]["category"] == "food"
        q0 = CATEGORY_GUIDANCE["food"]["questions"]["en"][0]
        assert r["ai_reply_text"] == "Great! " + q0
        assert r["draft_state"]["questions_asked"] == [q0]

    def test_capture_entry_unknown_category_asks_in_english(self):
        cid, _ = self._to_business_model_via_fallback()
        r = self._say(cid, "I make some nice things", responses=[
            {"reply_text": "ok", "ready_to_advance": True},
            {"category": "unclear"},
        ])
        assert r["stage"] == "capture"
        assert r["draft_state"]["category"] is None
        assert r["ai_reply_text"] == (
            STAGE_DESCRIPTIONS["capture"]["en"] + " " + FALLBACK_MESSAGES["ask_category_suffix"]["en"])
        assert not has_devanagari(r["ai_reply_text"])

    def test_capture_stage_category_still_unclear_english_message(self):
        cid, _ = self._to_business_model_via_fallback()
        self._say(cid, "I make some nice things", responses=[
            {"reply_text": "ok", "ready_to_advance": True}, {"category": "unclear"}])
        r = self._say(cid, "just things", responses=[{"category": "unclear"}])
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["category_not_understood"]["en"]
        assert r["draft_state"]["category"] is None

    def test_full_english_capture_flow_and_completion_message(self):
        cid, _ = self._to_business_model_via_fallback()
        r = self._say(cid, "I weave sarees", responses=[
            {"reply_text": "ok", "ready_to_advance": True}, {"category": "textile"}])
        qs = CATEGORY_GUIDANCE["textile"]["questions"]["en"]
        assert r["ai_reply_text"] == "Great! " + qs[0]

        # answers accepted (mock returns {} -> the light fallback accepts non-trivial answers)
        r = self._say(cid, "cotton and silk")
        assert r["ai_reply_text"] == qs[1]
        r = self._say(cid, "six yards")
        assert r["ai_reply_text"] == qs[2]
        r = self._say(cid, "wash by hand")
        assert r["stage"] == "done"
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["capture_complete"]["en"]

        # 'done' stage reply
        r = self._say(cid, "thanks")
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["done"]["en"]

    def test_unaddressed_answer_without_llm_followup_uses_english_prefix(self):
        cid, _ = self._to_business_model_via_fallback()
        self._say(cid, "I sell toys", responses=[
            {"reply_text": "ok", "ready_to_advance": True}, {"category": "toy"}])
        q0 = CATEGORY_GUIDANCE["toy"]["questions"]["en"][0]
        r = self._say(cid, "idk", responses=[{"addressed": False, "gentle_followup": ""}])
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["clarify_prefix"]["en"] + q0
        assert r["draft_state"]["seller_responses"] == []

    def test_unaddressed_answer_hindi_prefix_unchanged(self):
        agent = ConversationAgent(MockLLMClient())
        state = ConversationState()
        state.stage = "capture"
        state.draft_state["category"] = "food"
        q0 = CATEGORY_GUIDANCE["food"]["questions"]["hi"][0]
        state.draft_state["questions_asked"] = [q0]
        agent.conversations[state.conversation_id] = state
        agent.llm.set_responses([{"addressed": False, "gentle_followup": ""}])
        r = agent.process_message("s", state.conversation_id, "पता नहीं", seller_language="hi")
        assert r["ai_reply_text"] == f"धन्यवाद, लेकिन कृपया थोड़ा और स्पष्ट बताएं - {q0}"

    @pytest.mark.parametrize("lang,key_lang", [("en", "en"), ("hi", "hi")])
    def test_capture_max_turns_wrapup(self, lang, key_lang):
        state = ConversationState()
        state.stage = "capture"
        state.draft_state["category"] = "food"
        state.history = [{"role": "user", "content": "x"}] * 20   # well past CAPTURE_MAX_TURNS
        self.agent.conversations[state.conversation_id] = state
        r = self._say(state.conversation_id, "more", lang)
        assert r["stage"] == "done"
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["capture_max_turns"][key_lang]

    @pytest.mark.parametrize("lang,key_lang", [("en", "en"), ("hi", "hi")])
    def test_ask_more_when_questions_exhausted(self, lang, key_lang):
        state = ConversationState()
        state.stage = "capture"
        state.draft_state["category"] = "food"
        qs = get_category_questions("food", lang)
        state.draft_state["questions_asked"] = list(qs)           # all 4 already asked
        self.agent.conversations[state.conversation_id] = state
        r = self._say(state.conversation_id, "some answer", lang)
        assert r["stage"] == "capture"
        assert r["ai_reply_text"] == FALLBACK_MESSAGES["ask_more"][key_lang]


class TestOtherLanguagesFallBackToEnglish:
    @pytest.mark.parametrize("lang", ["ta", "te", "bn", "mr", "gu", "kn", "pa", "en-IN"])
    def test_full_fallback_flow(self, lang):
        mock = MockLLMClient()
        agent = ConversationAgent(mock)

        def say(cid, text, responses=None):
            mock.set_responses(responses or [])
            return agent.process_message("s", cid, text, seller_language=lang)

        r = say(None, "vanakkam")
        cid = r["conversation_id"]
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["idea"]["en"]
        # Tamil/Telugu/... sellers commonly still type "ok"/"yes"/"हाँ" - combined list applies
        # for languages without dedicated keywords.
        r = say(cid, "ok")
        assert r["stage"] == "procedure" and r["ai_reply_text"] == STAGE_DESCRIPTIONS["procedure"]["en"]
        r = say(cid, "understood")
        assert r["stage"] == "business_model"
        r = say(cid, "I make toys", [
            {"reply_text": "x", "ready_to_advance": True}, {"category": "toy"}])
        assert r["ai_reply_text"] == "Great! " + CATEGORY_GUIDANCE["toy"]["questions"]["en"][0]
        assert not has_devanagari(r["ai_reply_text"])


# ----------------------------------------------------------------------
# keyword category detection (fallback), English variants
# ----------------------------------------------------------------------

class TestEnglishCategoryKeywords:
    def setup_method(self):
        self.agent = ConversationAgent(MockLLMClient())

    @pytest.mark.parametrize("message,expected", [
        # food
        ("I make homemade pickle", "food"),
        ("we sell papad and chutney", "food"),
        ("jaggery and spices", "food"),
        # textile
        ("I weave woven shawls", "textile"),
        ("handloom dupatta", "textile"),
        ("embroidered kurta", "textile"),
        ("I sell a sari", "textile"),
        # toy
        ("wooden toys", "toy"),
        ("I make cloth dolls", "textile"),      # ordering unchanged: textile is checked before toy
        ("clay puppets and puzzles", "toy"),
        # handicraft
        ("handmade pottery", "handicraft"),
        ("bamboo baskets", "handicraft"),
        ("I do wood carving", "handicraft"),
        ("terracotta", "handicraft"),
        # existing Hindi / mixed behaviour unchanged
        ("मैं हाथ से बुनी साड़ी बेचता हूं", "textile"),
        ("यह लकड़ी का खिलौना है", "toy"),
        ("I make handicraft, हाथ से बना है", "handicraft"),
    ])
    def test_detects(self, message, expected):
        assert self.agent._detect_category_keywords(message) == expected

    @pytest.mark.parametrize("message", [
        "I sell things for 50 dollars",       # 'doll' must not match 'dollars'
        "My name is Sarita and I work hard",  # 'sari' must not match 'Sarita'
        "I make some nice things",
        "मैं कुछ अच्छी चीज़ें बनाता हूं",
    ])
    def test_no_false_positive(self, message):
        assert self.agent._detect_category_keywords(message) is None


# ----------------------------------------------------------------------
# Ollama transport errors must not become 500s
# ----------------------------------------------------------------------

class TestLLMTransportErrorFallsBack:
    def test_narrative_stage_falls_back_instead_of_raising(self):
        agent = ConversationAgent(RaisingLLM())
        r = agent.process_message("s", None, "hello", seller_language="en")
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["idea"]["en"]
        r2 = agent.process_message("s", r["conversation_id"], "yes", seller_language="en")
        assert r2["stage"] == "procedure"

    def test_hindi_narrative_stage_falls_back_instead_of_raising(self):
        agent = ConversationAgent(RaisingLLM())
        r = agent.process_message("s", None, "नमस्ते", seller_language="hi")
        assert r["ai_reply_text"] == STAGE_DESCRIPTIONS["idea"]["hi"]

    def test_category_detection_falls_back_to_keywords(self):
        agent = ConversationAgent(RaisingLLM())
        assert agent._detect_category("I make pickle") == "food"
        assert agent._detect_category("मैं अचार बनाता हूँ") == "food"
        assert agent._detect_category("something vague") is None

    def test_answer_check_falls_back_to_lenient_accept(self):
        agent = ConversationAgent(RaisingLLM())
        assert agent._check_answer_addressed("q?", "cotton") == (True, None)
        assert agent._check_answer_addressed("q?", " ") == (False, None)

    def test_full_conversation_completes_with_llm_down(self):
        agent = ConversationAgent(RaisingLLM())
        cid = None
        for text in ["hello", "yes", "ok", "I sell homemade pickle", "salt and oil", "one year", "no"]:
            r = agent.process_message("s", cid, text, seller_language="en")
            cid = r["conversation_id"]
        assert r["stage"] == "done"
        assert r["draft_state"]["category"] == "food"


@pytest.fixture
def client_llm_down():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        original = app_module.conversation_agent.llm
        app_module.conversation_agent.llm = RaisingLLM()
        yield c
        app_module.conversation_agent.llm = original


class TestConverseEndpointWithLLMDown:
    @pytest.mark.parametrize("lang,expected", [
        ("hi", STAGE_DESCRIPTIONS["idea"]["hi"]),
        ("en", STAGE_DESCRIPTIONS["idea"]["en"]),
        ("ta", STAGE_DESCRIPTIONS["idea"]["en"]),
    ])
    def test_converse_returns_200_with_fallback_text(self, client_llm_down, lang, expected):
        resp = client_llm_down.post(
            "/agent/converse",
            data=json.dumps({"seller_id": "s1", "conversation_id": None,
                             "message_text": "hello", "seller_language": lang}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert json.loads(resp.data)["ai_reply_text"] == expected
