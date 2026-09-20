"""Conversation state management and orchestration using Strands Agents SDK."""
import uuid
from typing import Dict, Any, Optional, List, Tuple
from .llm_client import LLMClient
from .config import (
    CATEGORY_GUIDANCE,
    STAGE_DESCRIPTIONS,
    STAGE_SYSTEM_PROMPTS,
    CATEGORY_DETECTION_SYSTEM_PROMPT,
    CAPTURE_ANSWER_CHECK_SYSTEM_PROMPT,
    CAPTURE_MAX_TURNS,
    INTEREST_KEYWORDS_LOWER,
)


class ConversationState:
    """Manages the state of a seller onboarding conversation."""

    STAGES = ["idea", "procedure", "business_model", "capture", "done"]

    def __init__(self, conversation_id: Optional[str] = None):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.stage = "idea"
        self.draft_state: Dict[str, Any] = {
            "raw_description": "",
            "category": None,
            "detected_info": {},
            "questions_asked": [],
            "seller_responses": []
        }
        self.history: List[Dict[str, str]] = []
        self.stage_entry_turn = 0

    def advance_stage(self) -> bool:
        """Move to the next stage. Returns True if advanced, False if already at end."""
        current_idx = self.STAGES.index(self.stage)
        if current_idx < len(self.STAGES) - 1:
            self.stage = self.STAGES[current_idx + 1]
            self.stage_entry_turn = len(self.history)
            return True
        return False

    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.history.append({"role": role, "content": content})

    def turns_in_current_stage(self) -> int:
        """Count turns since entering current stage."""
        return len(self.history) - self.stage_entry_turn

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dict."""
        return {
            "conversation_id": self.conversation_id,
            "stage": self.stage,
            "draft_state": self.draft_state,
            "history": self.history,
            "stage_entry_turn": self.stage_entry_turn
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Deserialize state from dict."""
        state = cls(data["conversation_id"])
        state.stage = data["stage"]
        state.draft_state = data["draft_state"]
        state.history = data["history"]
        state.stage_entry_turn = data.get("stage_entry_turn", 0)
        return state


class ConversationAgent:
    """Strands-style agent orchestrating the seller onboarding conversation.

    idea/procedure/business_model are driven by real LLM calls (LLMClient.generate_json)
    using a per-stage system prompt (see config.STAGE_SYSTEM_PROMPTS). Category detection is
    also LLM-based. Every LLM call has a keyword-based fallback that only engages if the LLM
    call/JSON parsing fails (after LLMClient.generate_json's own retry) - the stage machine
    never crashes and never silently guesses a category.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.conversations: Dict[str, ConversationState] = {}

    def process_message(
        self,
        seller_id: str,
        conversation_id: Optional[str],
        message_text: str,
        seller_language: str = "hi"
    ) -> Dict[str, Any]:
        """Process a single message turn in the conversation."""
        # Get or create conversation state
        if conversation_id and conversation_id in self.conversations:
            state = self.conversations[conversation_id]
        else:
            state = ConversationState()
            self.conversations[state.conversation_id] = state

        # Add user message to history
        state.add_message("user", message_text)

        # Route to appropriate stage handler
        if state.stage in ("idea", "procedure", "business_model"):
            response = self._handle_narrative_stage(state, message_text, seller_language, state.stage)
        elif state.stage == "capture":
            response = self._handle_capture_stage(state, message_text, seller_language)
        else:
            response = "धन्यवाद! आपकी जानकारी पूरी हो गई है।"

        # Add AI response to history
        state.add_message("assistant", response)

        # Build response
        return {
            "conversation_id": state.conversation_id,
            "ai_reply_text": response,
            "stage": state.stage,
            "draft_state": state.draft_state
        }

    # ------------------------------------------------------------------
    # idea / procedure / business_model: LLM-driven narrative stages
    # ------------------------------------------------------------------

    def _handle_narrative_stage(
        self, state: ConversationState, message: str, lang: str, stage: str
    ) -> str:
        """Handle one of the idea/procedure/business_model stages via the LLM.

        Calls the LLM with a system prompt pinning down the required content for `stage` and
        asks for structured JSON: {"reply_text": ..., "ready_to_advance": bool}. Falls back to
        the original keyword-based safety net (STAGE_DESCRIPTIONS + interest keywords) only if
        the LLM call/JSON parsing fails to produce a usable result.
        """
        turns = state.turns_in_current_stage()

        prompt = self._build_narrative_prompt(state, stage, message)
        result = self.llm.generate_json(prompt, system=STAGE_SYSTEM_PROMPTS[stage])
        reply_text, ready_to_advance, used_fallback = self._parse_narrative_result(result)

        if used_fallback:
            reply_text, ready_to_advance = self._fallback_narrative_response(stage, message, turns)

        # Never advance on the very first turn of a stage - always deliver the stage's own
        # explanation before deciding the seller is ready to move on.
        if turns <= 1:
            ready_to_advance = False

        if ready_to_advance:
            state.advance_stage()
            if state.stage == "capture":
                # business_model -> capture also requires detecting the product category
                # from this same message (see KARTIKAY_TASK.md Section 5.2).
                return self._enter_capture_stage(state, message, lang)

        return reply_text

    def _build_narrative_prompt(self, state: ConversationState, stage: str, message: str) -> str:
        """Build the user-turn prompt for a narrative-stage LLM call."""
        history_text = self._format_history(state)
        turn_number = state.turns_in_current_stage()
        return (
            f"Conversation so far:\n{history_text}\n\n"
            f"This is turn {turn_number} of the '{stage}' stage.\n"
            f"Seller's latest message: {message}\n\n"
            "Respond with a JSON object with exactly these fields:\n"
            "- reply_text: your reply to the seller, in Hindi (Devanagari script)\n"
            "- ready_to_advance: true only if the seller has now engaged enough that it is "
            "time to move on to the next topic, false otherwise\n\n"
            "Respond with ONLY the JSON object, no other text."
        )

    def _format_history(self, state: ConversationState) -> str:
        """Render recent conversation history as plain text context for the LLM."""
        lines = []
        for turn in state.history[-10:]:
            speaker = "Seller" if turn["role"] == "user" else "Assistant"
            lines.append(f"{speaker}: {turn['content']}")
        return "\n".join(lines) if lines else "(no prior messages)"

    def _parse_narrative_result(
        self, result: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[bool], bool]:
        """Validate the LLM's JSON output for a narrative stage.

        Returns (reply_text, ready_to_advance, used_fallback). used_fallback is True whenever
        the result can't be trusted (LLM/JSON error, or missing/mistyped fields).
        """
        if not isinstance(result, dict) or "error" in result:
            return None, None, True

        reply_text = result.get("reply_text")
        ready_to_advance = result.get("ready_to_advance")

        if not isinstance(reply_text, str) or not reply_text.strip():
            return None, None, True
        if not isinstance(ready_to_advance, bool):
            return None, None, True

        return reply_text, ready_to_advance, False

    def _fallback_narrative_response(
        self, stage: str, message: str, turns: int
    ) -> Tuple[str, bool]:
        """Keyword-based safety net, used only when the LLM call/JSON parsing fails twice.

        Mirrors the original scripted behaviour so tests/production never crash or silently
        stall just because Ollama is briefly unavailable.
        """
        if turns <= 1:
            return STAGE_DESCRIPTIONS[stage], False

        if stage == "idea":
            message_lower = message.lower()
            # An explicit interest keyword always counts as ready, even if short.
            if any(kw in message_lower for kw in INTEREST_KEYWORDS_LOWER):
                return STAGE_DESCRIPTIONS["procedure"], True
            # Otherwise, very short/off-topic answers get gently re-asked rather than advancing.
            if len(message.strip()) < 5:
                return (
                    "कृपया बताइए - क्या आप अपने उत्पाद को इस बाज़ार में बेचना चाहेंगे?",
                    False,
                )
            return STAGE_DESCRIPTIONS["procedure"], True

        if stage == "procedure":
            return STAGE_DESCRIPTIONS["business_model"], True

        # business_model: the reply text here is only used if we somehow don't end up
        # entering capture (defensive); the real capture-entry reply is built separately.
        return STAGE_DESCRIPTIONS[stage], True

    # ------------------------------------------------------------------
    # capture: category detection + adaptive per-category questioning
    # ------------------------------------------------------------------

    def _enter_capture_stage(self, state: ConversationState, message: str, lang: str) -> str:
        """First turn inside 'capture': detect category from the message that triggered it."""
        category = self._detect_category(message)
        if category:
            state.draft_state["category"] = category
            state.draft_state["raw_description"] = message
            return self._get_category_question(state, category)
        return (
            STAGE_DESCRIPTIONS["capture"]
            + " पहले बताइए - यह किस तरह का उत्पाद है? (खाना, कपड़ा, खिलौना, या हस्तशिल्प?)"
        )

    def _handle_capture_stage(self, state: ConversationState, message: str, lang: str) -> str:
        """Handle the 'capture' stage - gather product details, adaptively."""
        # Detect category if not already set.
        if not state.draft_state.get("category"):
            category = self._detect_category(message)
            if category:
                state.draft_state["category"] = category
                state.draft_state["raw_description"] = message
                return self._get_category_question(state, category)
            return "मुझे समझ नहीं आया। कृपया बताइए - यह खाना है, कपड़ा है, खिलौना है, या हस्तशिल्प?"

        # Hard cap: if the seller never gives enough info, move on with what we have rather
        # than looping forever (KARTIKAY_TASK.md Section 5.1).
        if state.turns_in_current_stage() > CAPTURE_MAX_TURNS:
            state.draft_state["seller_responses"].append(message)
            state.advance_stage()
            return "बहुत अच्छा! जितनी जानकारी मिली उसके आधार पर हम आपके लिए एक listing तैयार करेंगे।"

        # Check whether the seller's answer actually addressed the last question asked.
        questions_asked = state.draft_state["questions_asked"]
        if questions_asked:
            last_question = questions_asked[-1]
            addressed, follow_up = self._check_answer_addressed(last_question, message)
            if not addressed:
                return follow_up or f"धन्यवाद, लेकिन कृपया थोड़ा और स्पष्ट बताएं - {last_question}"

        # Store response
        state.draft_state["seller_responses"].append(message)

        # Check if we have enough info (at least 3 responses) to complete
        if len(state.draft_state["seller_responses"]) >= 3:
            state.advance_stage()
            return "बहुत अच्छा! मैंने सारी जानकारी इकट्ठा कर ली है। अब हम आपके लिए एक listing तैयार करेंगे।"

        # Get next question for this category. The required-info checklist per category
        # (CATEGORY_GUIDANCE[category]["questions"]) stays the source of truth for *what* must
        # be asked, so listing_generator._check_compliance keeps working unchanged.
        category = state.draft_state["category"]
        guidance = CATEGORY_GUIDANCE[category]
        questions_asked_count = len(questions_asked)

        if questions_asked_count < len(guidance["questions"]):
            question = guidance["questions"][questions_asked_count]
            state.draft_state["questions_asked"].append(question)
            return question

        # Ask for more general details
        return "कुछ और बताइए - कोई खास बात इस उत्पाद के बारे में?"

    def _check_answer_addressed(self, question: str, answer: str) -> Tuple[bool, Optional[str]]:
        """LLM-based check of whether `answer` addresses `question`, with a light fallback."""
        prompt = f"Question asked: {question}\nSeller's answer: {answer}"
        result = self.llm.generate_json(prompt, system=CAPTURE_ANSWER_CHECK_SYSTEM_PROMPT)

        if isinstance(result, dict) and "error" not in result and isinstance(result.get("addressed"), bool):
            addressed = result["addressed"]
            follow_up = result.get("gentle_followup")
            follow_up = follow_up if isinstance(follow_up, str) and follow_up.strip() else None
            return addressed, follow_up

        # Fallback: only reject clearly empty/too-short non-answers; otherwise accept the
        # answer rather than risk stalling the seller forever because the LLM was unavailable.
        if len(answer.strip()) < 2:
            return False, None
        return True, None

    def _detect_category(self, message: str) -> Optional[str]:
        """Detect product category from message: LLM-based, keyword matching as fallback only.

        Never silently guesses - returns None ("unclear") if neither the LLM nor the keyword
        list can decide, so the caller asks a clarifying question instead.
        """
        prompt = f"Seller's message: {message}"
        result = self.llm.generate_json(prompt, system=CATEGORY_DETECTION_SYSTEM_PROMPT)

        if isinstance(result, dict) and "error" not in result:
            candidate = result.get("category")
            if isinstance(candidate, str):
                candidate = candidate.strip().lower()
                if candidate in CATEGORY_GUIDANCE:
                    return candidate

        # LLM said "unclear", failed to parse, or errored -> try the keyword list before
        # giving up. If the keyword list also can't decide, return None (the caller asks the
        # one clarifying question) rather than silently guessing a category.
        return self._detect_category_keywords(message)

    def _detect_category_keywords(self, message: str) -> Optional[str]:
        """Keyword-only category detection - fallback path only."""
        message_lower = message.lower()

        # Food keywords
        if any(kw in message_lower for kw in ["खाना", "खाद्य", "मिठाई", "नमकीन", "अचार", "food", "sweet", "snack"]):
            return "food"

        # Textile keywords
        if any(kw in message_lower for kw in ["कपड़ा", "साड़ी", "दुपट्टा", "कुर्ता", "textile", "fabric", "cloth", "saree"]):
            return "textile"

        # Toy keywords
        if any(kw in message_lower for kw in ["खिलौना", "toy", "खेल", "game"]):
            return "toy"

        # Handicraft keywords
        if any(kw in message_lower for kw in ["हस्तशिल्प", "handicraft", "हाथ से बना", "कला", "craft", "दस्तकारी"]):
            return "handicraft"

        return None

    def _get_category_question(self, state: ConversationState, category: str) -> str:
        """Get the first category-specific question."""
        guidance = CATEGORY_GUIDANCE[category]
        question = guidance["questions"][0]
        state.draft_state["questions_asked"].append(question)
        return f"अच्छा! {question}"

    def get_state(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation state."""
        return self.conversations.get(conversation_id)
