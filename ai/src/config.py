"""Configuration for AI Service."""
import os
from typing import Dict, Any, Optional

# LLM Configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b-instruct")
AI_SERVICE_PORT = int(os.getenv("AI_SERVICE_PORT", "8001"))

# ISO 639-1 code -> language name as it should appear inside an LLM prompt. Adding a language
# the underlying model can already speak only requires a new entry here (plus the matching
# option in frontend SellerSetupForm.jsx) - no other code changes.
LANGUAGE_NAMES: Dict[str, str] = {
    "hi": "Hindi (Devanagari script)",
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "pa": "Punjabi (Gurmukhi script)",
}
DEFAULT_LANGUAGE = "hi"


def get_language_name(lang: Optional[str]) -> str:
    """Return the prompt-ready language name for `lang`, defaulting to Hindi if unknown.

    Tolerates region-tagged codes such as "en-IN" / "hi_IN" and mixed case.
    """
    if isinstance(lang, str) and lang.strip():
        code = lang.strip().lower().replace("_", "-").split("-")[0]
        if code in LANGUAGE_NAMES:
            return LANGUAGE_NAMES[code]
    return LANGUAGE_NAMES[DEFAULT_LANGUAGE]


# Category-specific guidance configuration
CATEGORY_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "food": {
        "questions": {
            "hi": [
                "क्या आप बता सकते हैं कि इसमें कौन-कौन सी सामग्री है?",
                "यह कितने दिनों तक ताज़ा रहता है?",
                "क्या इसमें कोई एलर्जी वाली चीज़ है?",
                "इसे कैसे संग्रहित करना चाहिए?"
            ],
            "en": [
                "Can you tell me what ingredients it contains?",
                "How many days does it stay fresh?",
                "Does it contain anything that could cause an allergy?",
                "How should it be stored?"
            ],
        },
        "compliance_checks": ["ingredients", "shelf_life", "allergens", "storage"],
        "photo_guidance": [
            "shoot in good daylight",
            "show ingredients if packaged",
            "show product from multiple angles",
            "include size reference (coin or hand)"
        ]
    },
    "textile": {
        "questions": {
            "hi": [
                "यह किस कपड़े/सामग्री से बना है?",
                "इसका आकार क्या है?",
                "इसकी देखभाल कैसे करनी चाहिए?",
                "क्या इसमें कोई विशेष डिज़ाइन या काम है?"
            ],
            "en": [
                "What fabric or material is it made from?",
                "What is its size?",
                "How should it be cared for?",
                "Does it have any special design or work on it?"
            ],
        },
        "compliance_checks": ["material", "dimensions", "care_instructions"],
        "photo_guidance": [
            "shoot in natural light",
            "show fabric texture and weave",
            "display full item flat or worn",
            "include size reference (ruler or person)"
        ]
    },
    "toy": {
        "questions": {
            "hi": [
                "यह खिलौना किस उम्र के बच्चों के लिए है?",
                "इसमें कौन-कौन से पार्ट्स हैं?",
                "क्या इसमें छोटे हिस्से हैं जो निगले जा सकते हैं?",
                "यह किस चीज़ से बना है?"
            ],
            "en": [
                "What age group of children is this toy for?",
                "What parts does it have?",
                "Does it have small parts that could be swallowed?",
                "What is it made from?"
            ],
        },
        "compliance_checks": ["age_range", "small_parts_warning", "material_safety"],
        "photo_guidance": [
            "shoot toy in use or display",
            "show all components",
            "include size comparison",
            "demonstrate key features"
        ]
    },
    "handicraft": {
        "questions": {
            "hi": [
                "यह किस सामग्री से बना है?",
                "इसका आकार क्या है?",
                "इसे बनाने में कितना समय लगा?",
                "क्या इसमें कोई खास तकनीक या परंपरागत शैली है?"
            ],
            "en": [
                "What material is it made from?",
                "What is its size?",
                "How long did it take to make?",
                "Is there any special technique or traditional style involved?"
            ],
        },
        "compliance_checks": ["material", "dimensions", "crafting_technique"],
        "photo_guidance": [
            "shoot in natural light",
            "show fine details and craftsmanship",
            "include size reference",
            "capture unique features"
        ]
    }
}

# System prompts for the LLM-driven narrative stages (idea / procedure / business_model).
# Each pins down the content that stage MUST cover so the model doesn't drift, while still
# letting it phrase things naturally and react to what the seller actually said.
# The model is asked to return JSON: {"reply_text": "...", "ready_to_advance": bool}.
# Prompts contain a literal "{language}" placeholder that is filled at request time by
# build_stage_system_prompt() (NOT str.format - the JSON example contains literal braces).
STAGE_SYSTEM_PROMPTS: Dict[str, str] = {
    "idea": (
        "You are a warm, patient onboarding guide for Kalaa Setu, a program that helps rural "
        "Indian sellers (artisans, cooks, weavers) reach buyers on Amazon without needing to "
        "know English or computers. This is the 'idea' stage: explain in the simplest possible "
        "words what Amazon is and why Kalaa Setu matters for the seller, in the same warm, "
        "encouraging register a helpful neighbour would use - never technical, never salesy. "
        "Always reply in {language}, even if the seller wrote in a different language or mixed "
        "languages. If the seller's message is very short, off-topic, or unclear, gently "
        "re-ask whether they'd like to hear about selling their product, in a friendly way, and "
        "set ready_to_advance to false. Only set ready_to_advance to true once the seller has "
        "shown some interest or acknowledgement and it's a natural moment to move on to "
        "explaining the step-by-step procedure. If you do set ready_to_advance to true, let your "
        "reply_text flow naturally into beginning that explanation. "
        'Respond with ONLY a JSON object: {"reply_text": "...", "ready_to_advance": true|false}.'
    ),
    "procedure": (
        "You are the same warm onboarding guide, now in the 'procedure' stage. Explain how the "
        "process works using a simple analogy (for example: like their village's weekly market, "
        "but always open and reaching the whole world). You MUST explicitly mention that the "
        "seller's local school or Common Service Centre (CSC) is the single point of contact "
        "that handles BOTH the training/listing help AND the pickup of the finished product - "
        "this is a hard requirement, never omit it. Always reply in {language}, even if the "
        "seller wrote in a different language or mixed languages. "
        "If the seller's message is very short, off-topic, or unclear, gently re-ask for "
        "acknowledgement and set ready_to_advance to false. Only set ready_to_advance to true "
        "once the seller has acknowledged the explanation, and let your reply_text flow naturally "
        "into beginning the honest explanation of fees and the community contribution. "
        'Respond with ONLY a JSON object: {"reply_text": "...", "ready_to_advance": true|false}.'
    ),
    "business_model": (
        "You are the same warm onboarding guide, now in the 'business_model' stage. Honestly "
        "explain that when a sale happens the seller keeps the majority of the money, Amazon "
        "takes a small platform fee to run the service, and separately the seller may choose to "
        "route a percentage of their OWN proceeds to their school/CSC's community development "
        "fund - this contribution is entirely opt-in, the seller decides the percentage, and they "
        "can turn it on or off or change it at any time. Never imply it is mandatory or "
        "platform-imposed. Always reply in {language}, even if the seller wrote in a different "
        "language or mixed languages. If the seller's message is very short, off-topic, or unclear, gently re-ask for acknowledgement and set "
        "ready_to_advance to false. Only set ready_to_advance to true once the seller has "
        "acknowledged this explanation and it's time to start capturing their product details. "
        'Respond with ONLY a JSON object: {"reply_text": "...", "ready_to_advance": true|false}.'
    ),
}

def build_stage_system_prompt(stage: str, lang: Optional[str]) -> str:
    """Return the system prompt for `stage`, with {language} filled in for `lang`.

    Uses str.replace rather than str.format because the prompts embed a literal JSON example
    ({"reply_text": ...}) whose braces would otherwise be parsed as format fields.
    """
    return STAGE_SYSTEM_PROMPTS[stage].replace("{language}", get_language_name(lang))


# System prompt for LLM-based product category classification (with keyword matching as the
# fallback if this call fails or returns something unusable).
CATEGORY_DETECTION_SYSTEM_PROMPT = (
    "Classify a rural Indian seller's product description into exactly one of these categories: "
    "food, textile, toy, handicraft. The message may be in Hindi, English, another Indian language, or a mix. "
    "If you genuinely cannot tell which of the four categories it is, respond with \"unclear\" "
    "rather than guessing. "
    'Respond with ONLY a JSON object: {"category": "food|textile|toy|handicraft|unclear"}.'
)

# System prompt used during the 'capture' stage to check whether the seller's latest answer
# actually addressed the question that was just asked (LLM-based, with a lightweight fallback).
CAPTURE_ANSWER_CHECK_SYSTEM_PROMPT = (
    "You are helping onboard a rural Indian seller onto Amazon. You will be given a question "
    "that was just asked and the seller's answer, which may be in any language or a mix. "
    "Decide whether the answer meaningfully addresses the question, even partially or briefly - "
    "sellers may have low literacy, so be lenient and only mark it as not addressed if the reply "
    "is genuinely off-topic, empty, or a non-answer. If not addressed, write one short, gentle, "
    "encouraging follow-up in {language} asking the same thing a different way. "
    'Respond with ONLY a JSON object: {"addressed": true|false, "gentle_followup": "..."} '
    '(gentle_followup can be an empty string when addressed is true).'
)

def build_capture_check_system_prompt(lang: Optional[str]) -> str:
    """Return CAPTURE_ANSWER_CHECK_SYSTEM_PROMPT with the follow-up language filled in."""
    return CAPTURE_ANSWER_CHECK_SYSTEM_PROMPT.replace("{language}", get_language_name(lang))


# Safety net: if the LLM call/JSON parsing for a narrative stage fails (even after
# LLMClient.generate_json's own retry), fall back to keyword matching against these words to
# judge whether the seller has shown interest/acknowledgement, mirroring the original scripted
# behaviour so the stage machine never crashes just because Ollama is briefly unavailable.
INTEREST_KEYWORDS: Dict[str, list] = {
    # "hi" is EXACTLY the pre-multilingual list - do not change, Hindi behaviour must not regress.
    "hi": ["हाँ", "ठीक", "अच्छा", "जी", "ok", "yes"],
    "en": ["yes", "ok", "okay", "sure", "interested"],
}
# Combined list: used for languages we have no dedicated keywords for (a Tamil-speaking seller
# may still type "ok" or "हाँ").
INTEREST_KEYWORDS_COMBINED = list(dict.fromkeys(INTEREST_KEYWORDS["hi"] + INTEREST_KEYWORDS["en"]))
# Kept for backward compatibility with anything that imported the old flat list.
INTEREST_KEYWORDS_LOWER = [kw.lower() for kw in INTEREST_KEYWORDS["hi"]]


def get_interest_keywords(lang) -> list:
    """Lower-cased interest keywords for `lang` (hi/en); any other language gets the combined list."""
    base = _base_lang(lang)
    words = INTEREST_KEYWORDS.get(base, INTEREST_KEYWORDS_COMBINED)
    return [kw.lower() for kw in words]

# Hard cap on turns spent in the 'capture' stage before we force a move to 'done', even if the
# category-specific question checklist isn't fully answered yet (KARTIKAY_TASK.md Section 5.1).
CAPTURE_MAX_TURNS = 8

# Stage descriptions for conversation flow, keyed stage -> language -> text ('hi' and 'en').
# Any language other than 'hi' falls back to 'en' (see get_stage_description).
# These are now used as the FALLBACK content for idea/procedure/business_model (shown when the
# LLM call/JSON parsing fails, per the validate-then-retry-then-fallback pattern), not as the
# primary path - the primary path calls the LLM with STAGE_SYSTEM_PROMPTS above.
STAGE_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "idea": {
        "hi": """नमस्ते! मैं आपको Amazon Kalaa Setu के बारे में बताऊंगा।

Amazon एक बहुत बड़ा बाज़ार है जहाँ दुनिया भर के लोग चीजें खरीदते हैं। Kalaa Setu आपके जैसे कारीगरों और विक्रेताओं को इस बाज़ार से जोड़ता है - बिना अंग्रेजी जाने, बिना कंप्यूटर के ज्ञान के।

आपको बस अपनी चीज़ बनानी है और अपनी भाषा में बताना है। बाकी हम संभाल लेंगे। आप अपने उत्पाद के बारे में बताना चाहेंगे?""",

        "en": """Hello! I'm going to tell you about Amazon Kalaa Setu.

Amazon is a very large marketplace where people from all over the world buy things. Kalaa Setu connects artisans and sellers like you to this marketplace - without needing to know English, and without any computer knowledge.

You just make your product and describe it in your own language. We'll take care of the rest. Would you like to tell me about your product?""",
    },

    "procedure": {
        "hi": """बहुत अच्छा! अब मैं आपको बताता हूँ कि यह कैसे काम करेगा:

सोचिए यह आपके गांव के साप्ताहिक बाज़ार जैसा है, लेकिन यह हमेशा खुला रहता है और पूरी दुनिया में है।

1. आप अपना उत्पाद अपने स्कूल या CSC में लाते हैं
2. हम आपसे बातचीत करके एक सुंदर listing बनाते हैं
3. खरीदार दुनिया में कहीं भी आपका उत्पाद देखते हैं और खरीदते हैं
4. जब बिक जाए, आपको पैसे मिलते हैं
5. आपका उत्पाद वही स्कूल/CSC से pickup होता है

आपका स्कूल/CSC ही आपकी एकमात्र बिंदु है - यहीं से सब काम होता है। क्या यह समझ में आया?""",

        "en": """Wonderful! Now let me tell you how this will work:

Think of it like your village's weekly market, but one that is always open and reaches the whole world.

1. You bring your product to your school or CSC
2. We talk with you and create a beautiful listing
3. Buyers anywhere in the world see your product and buy it
4. When it sells, you get paid
5. Your product is picked up from the same school/CSC

Your school/CSC is your single point of contact - everything happens from there. Does that make sense?""",
    },

    "business_model": {
        "hi": """अब मैं आपको पैसों के बारे में बताता हूँ - बिल्कुल ईमानदारी से:

जब कोई आपका उत्पाद खरीदता है:
1. आपको उस पैसे का अधिकतर हिस्सा मिलता है
2. Amazon एक छोटी फीस लेता है (platform चलाने के लिए)
3. बाकी पैसा आपका है

अब एक विशेष बात: आप चाहें तो अपनी कमाई का कुछ हिस्सा अपने स्कूल/CSC के विकास फंड में दे सकते हैं - यह पूरी तरह आपकी मर्ज़ी है। आप कभी भी हाँ या ना कर सकते हैं, और कितना प्रतिशत देना है वो भी आप तय करेंगे।

यह decision आप बाद में भी ले सकते हैं। पहले अपने उत्पाद के बारे में बताइए - यह क्या है?""",

        "en": """Now let me tell you about the money - completely honestly:

When someone buys your product:
1. You get the majority of that money
2. Amazon takes a small fee (to run the platform)
3. The rest of the money is yours

Now one special thing: if you wish, you can give a part of your earnings to your school/CSC's community development fund - this is entirely your choice. You can say yes or no at any time, and you decide what percentage to give.

You can make this decision later too. First, tell me about your product - what is it?""",
    },

    "capture": {
        "hi": """अच्छा! अब मैं आपके उत्पाद के बारे में कुछ जानकारी लूंगा ताकि हम एक अच्छी listing बना सकें।""",

        "en": """Great! Now I'll ask a few things about your product so that we can create a good listing.""",
    }
}


# ----------------------------------------------------------------------------------------------
# Multilingual fallback / safety-net text (Tier 2)
#
# The LLM-driven paths already reply in the seller's language. Everything below is the
# deterministic text used when the LLM is unavailable or in fixed branches. We only maintain
# 'hi' (the live-demo language, must never regress) and 'en'; every other language falls back
# to 'en' rather than being hand-translated.
# ----------------------------------------------------------------------------------------------
FALLBACK_LANGUAGE = "en"
FALLBACK_LANGUAGES = ("hi", "en")


def _base_lang(lang) -> str:
    """Normalise a language tag to a lower-case base code: 'en-IN' -> 'en', None/'' -> 'hi'.

    Missing/blank language keeps the historical default (Hindi) so callers that never passed a
    language behave exactly as before.
    """
    if not isinstance(lang, str) or not lang.strip():
        return "hi"
    return lang.strip().lower().replace("_", "-").split("-")[0]


def resolve_fallback_lang(lang) -> str:
    """Map any language tag to one we have fallback text for: 'hi' or 'en' (default: 'en')."""
    base = _base_lang(lang)
    return base if base in FALLBACK_LANGUAGES else FALLBACK_LANGUAGE


def get_stage_description(stage: str, lang) -> str:
    """Fallback description for `stage` in `lang` ('hi'/'en'; anything else -> 'en')."""
    by_lang = STAGE_DESCRIPTIONS[stage]
    return by_lang.get(resolve_fallback_lang(lang)) or by_lang[FALLBACK_LANGUAGE]


def get_category_questions(category: str, lang) -> list:
    """Capture-stage question list for `category` in `lang` ('hi'/'en'; anything else -> 'en').

    Every language list has the same length - the capture logic indexes by
    len(questions_asked), so switching language mid-conversation stays aligned.
    """
    by_lang = CATEGORY_GUIDANCE[category]["questions"]
    return by_lang.get(resolve_fallback_lang(lang)) or by_lang[FALLBACK_LANGUAGE]


# Short fixed replies used by ConversationAgent, keyed message-id -> language -> text.
# The 'hi' strings are the original literals, unchanged.
FALLBACK_MESSAGES: Dict[str, Dict[str, str]] = {
    # 'done' stage reply.
    "done": {
        "hi": "धन्यवाद! आपकी जानकारी पूरी हो गई है।",
        "en": "Thank you! Your information is complete.",
    },
    # idea stage: very short / off-topic answer in the keyword fallback -> gentle re-ask.
    "idea_reask": {
        "hi": "कृपया बताइए - क्या आप अपने उत्पाद को इस बाज़ार में बेचना चाहेंगे?",
        "en": "Please tell me - would you like to sell your product in this marketplace?",
    },
    # Appended (after a space) to STAGE_DESCRIPTIONS['capture'] when category is still unknown.
    "ask_category_suffix": {
        "hi": "पहले बताइए - यह किस तरह का उत्पाद है? (खाना, कपड़ा, खिलौना, या हस्तशिल्प?)",
        "en": "First, tell me - what kind of product is it? (food, cloth, toy, or handicraft?)",
    },
    # Capture stage, category still unknown after a reply.
    "category_not_understood": {
        "hi": "मुझे समझ नहीं आया। कृपया बताइए - यह खाना है, कपड़ा है, खिलौना है, या हस्तशिल्प?",
        "en": "Sorry, I didn't understand. Please tell me - is it food, cloth, a toy, or a handicraft?",
    },
    # CAPTURE_MAX_TURNS reached: wrap up with whatever we have.
    "capture_max_turns": {
        "hi": "बहुत अच्छा! जितनी जानकारी मिली उसके आधार पर हम आपके लिए एक listing तैयार करेंगे।",
        "en": "Very good! Based on the information we have, we will prepare a listing for you.",
    },
    # Prefix for "please be a bit clearer" - the question that was asked is appended after it.
    "clarify_prefix": {
        "hi": "धन्यवाद, लेकिन कृपया थोड़ा और स्पष्ट बताएं - ",
        "en": "Thank you, but please be a little clearer - ",
    },
    # Enough answers collected (>= 3): capture complete.
    "capture_complete": {
        "hi": "बहुत अच्छा! मैंने सारी जानकारी इकट्ठा कर ली है। अब हम आपके लिए एक listing तैयार करेंगे।",
        "en": "Very good! I have collected all the information. Now we will prepare a listing for you.",
    },
    # Category questions exhausted but we still need more.
    "ask_more": {
        "hi": "कुछ और बताइए - कोई खास बात इस उत्पाद के बारे में?",
        "en": "Please tell me more - is there anything special about this product?",
    },
    # Prefix on the first category question.
    "first_question_prefix": {
        "hi": "अच्छा! ",
        "en": "Great! ",
    },
}


def get_fallback_message(key: str, lang) -> str:
    """Fixed reply `key` in `lang` ('hi'/'en'; anything else -> 'en')."""
    by_lang = FALLBACK_MESSAGES[key]
    return by_lang.get(resolve_fallback_lang(lang)) or by_lang[FALLBACK_LANGUAGE]
