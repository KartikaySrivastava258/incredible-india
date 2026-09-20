"""Configuration for AI Service."""
import os
from typing import Dict, Any

# LLM Configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b-instruct")
AI_SERVICE_PORT = int(os.getenv("AI_SERVICE_PORT", "8001"))

# Category-specific guidance configuration
CATEGORY_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "food": {
        "questions": [
            "क्या आप बता सकते हैं कि इसमें कौन-कौन सी सामग्री है?",
            "यह कितने दिनों तक ताज़ा रहता है?",
            "क्या इसमें कोई एलर्जी वाली चीज़ है?",
            "इसे कैसे संग्रहित करना चाहिए?"
        ],
        "compliance_checks": ["ingredients", "shelf_life", "allergens", "storage"],
        "photo_guidance": [
            "shoot in good daylight",
            "show ingredients if packaged",
            "show product from multiple angles",
            "include size reference (coin or hand)"
        ]
    },
    "textile": {
        "questions": [
            "यह किस कपड़े/सामग्री से बना है?",
            "इसका आकार क्या है?",
            "इसकी देखभाल कैसे करनी चाहिए?",
            "क्या इसमें कोई विशेष डिज़ाइन या काम है?"
        ],
        "compliance_checks": ["material", "dimensions", "care_instructions"],
        "photo_guidance": [
            "shoot in natural light",
            "show fabric texture and weave",
            "display full item flat or worn",
            "include size reference (ruler or person)"
        ]
    },
    "toy": {
        "questions": [
            "यह खिलौना किस उम्र के बच्चों के लिए है?",
            "इसमें कौन-कौन से पार्ट्स हैं?",
            "क्या इसमें छोटे हिस्से हैं जो निगले जा सकते हैं?",
            "यह किस चीज़ से बना है?"
        ],
        "compliance_checks": ["age_range", "small_parts_warning", "material_safety"],
        "photo_guidance": [
            "shoot toy in use or display",
            "show all components",
            "include size comparison",
            "demonstrate key features"
        ]
    },
    "handicraft": {
        "questions": [
            "यह किस सामग्री से बना है?",
            "इसका आकार क्या है?",
            "इसे बनाने में कितना समय लगा?",
            "क्या इसमें कोई खास तकनीक या परंपरागत शैली है?"
        ],
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
# The model is asked to return JSON: {"reply_text": "...(Hindi)...", "ready_to_advance": bool}.
STAGE_SYSTEM_PROMPTS: Dict[str, str] = {
    "idea": (
        "You are a warm, patient onboarding guide for Kalaa Setu, a program that helps rural "
        "Indian sellers (artisans, cooks, weavers) reach buyers on Amazon without needing to "
        "know English or computers. This is the 'idea' stage: explain in the simplest possible "
        "words what Amazon is and why Kalaa Setu matters for the seller, in the same warm, "
        "encouraging register a helpful neighbour would use - never technical, never salesy. "
        "Always reply in Hindi (Devanagari script), even if the seller wrote in English or mixed "
        "Hindi/English. If the seller's message is very short, off-topic, or unclear, gently "
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
        "this is a hard requirement, never omit it. Always reply in Hindi (Devanagari script). "
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
        "platform-imposed. Always reply in Hindi (Devanagari script). If the seller's message is "
        "very short, off-topic, or unclear, gently re-ask for acknowledgement and set "
        "ready_to_advance to false. Only set ready_to_advance to true once the seller has "
        "acknowledged this explanation and it's time to start capturing their product details. "
        'Respond with ONLY a JSON object: {"reply_text": "...", "ready_to_advance": true|false}.'
    ),
}

# System prompt for LLM-based product category classification (with keyword matching as the
# fallback if this call fails or returns something unusable).
CATEGORY_DETECTION_SYSTEM_PROMPT = (
    "Classify a rural Indian seller's product description into exactly one of these categories: "
    "food, textile, toy, handicraft. The message may be in Hindi, English, or a mix of both. "
    "If you genuinely cannot tell which of the four categories it is, respond with \"unclear\" "
    "rather than guessing. "
    'Respond with ONLY a JSON object: {"category": "food|textile|toy|handicraft|unclear"}.'
)

# System prompt used during the 'capture' stage to check whether the seller's latest answer
# actually addressed the question that was just asked (LLM-based, with a lightweight fallback).
CAPTURE_ANSWER_CHECK_SYSTEM_PROMPT = (
    "You are helping onboard a rural Indian seller onto Amazon. You will be given a question "
    "that was just asked and the seller's answer, which may be in Hindi, English, or a mix. "
    "Decide whether the answer meaningfully addresses the question, even partially or briefly - "
    "sellers may have low literacy, so be lenient and only mark it as not addressed if the reply "
    "is genuinely off-topic, empty, or a non-answer. If not addressed, write one short, gentle, "
    "encouraging follow-up in Hindi asking the same thing a different way. "
    'Respond with ONLY a JSON object: {"addressed": true|false, "gentle_followup": "..."} '
    '(gentle_followup can be an empty string when addressed is true).'
)

# Safety net: if the LLM call/JSON parsing for a narrative stage fails (even after
# LLMClient.generate_json's own retry), fall back to keyword matching against these words to
# judge whether the seller has shown interest/acknowledgement, mirroring the original scripted
# behaviour so the stage machine never crashes just because Ollama is briefly unavailable.
INTEREST_KEYWORDS = ["हाँ", "ठीक", "अच्छा", "जी", "ok", "yes"]
INTEREST_KEYWORDS_LOWER = [kw.lower() for kw in INTEREST_KEYWORDS]

# Hard cap on turns spent in the 'capture' stage before we force a move to 'done', even if the
# category-specific question checklist isn't fully answered yet (KARTIKAY_TASK.md Section 5.1).
CAPTURE_MAX_TURNS = 8

# Stage descriptions in Hindi for conversation flow.
# These are now used as the FALLBACK content for idea/procedure/business_model (shown when the
# LLM call/JSON parsing fails, per the validate-then-retry-then-fallback pattern), not as the
# primary path - the primary path calls the LLM with STAGE_SYSTEM_PROMPTS above.
STAGE_DESCRIPTIONS = {
    "idea": """नमस्ते! मैं आपको Amazon Kalaa Setu के बारे में बताऊंगा।

Amazon एक बहुत बड़ा बाज़ार है जहाँ दुनिया भर के लोग चीजें खरीदते हैं। Kalaa Setu आपके जैसे कारीगरों और विक्रेताओं को इस बाज़ार से जोड़ता है - बिना अंग्रेजी जाने, बिना कंप्यूटर के ज्ञान के।

आपको बस अपनी चीज़ बनानी है और अपनी भाषा में बताना है। बाकी हम संभाल लेंगे। आप अपने उत्पाद के बारे में बताना चाहेंगे?""",

    "procedure": """बहुत अच्छा! अब मैं आपको बताता हूँ कि यह कैसे काम करेगा:

सोचिए यह आपके गांव के साप्ताहिक बाज़ार जैसा है, लेकिन यह हमेशा खुला रहता है और पूरी दुनिया में है।

1. आप अपना उत्पाद अपने स्कूल या CSC में लाते हैं
2. हम आपसे बातचीत करके एक सुंदर listing बनाते हैं
3. खरीदार दुनिया में कहीं भी आपका उत्पाद देखते हैं और खरीदते हैं
4. जब बिक जाए, आपको पैसे मिलते हैं
5. आपका उत्पाद वही स्कूल/CSC से pickup होता है

आपका स्कूल/CSC ही आपकी एकमात्र बिंदु है - यहीं से सब काम होता है। क्या यह समझ में आया?""",

    "business_model": """अब मैं आपको पैसों के बारे में बताता हूँ - बिल्कुल ईमानदारी से:

जब कोई आपका उत्पाद खरीदता है:
1. आपको उस पैसे का अधिकतर हिस्सा मिलता है
2. Amazon एक छोटी फीस लेता है (platform चलाने के लिए)
3. बाकी पैसा आपका है

अब एक विशेष बात: आप चाहें तो अपनी कमाई का कुछ हिस्सा अपने स्कूल/CSC के विकास फंड में दे सकते हैं - यह पूरी तरह आपकी मर्ज़ी है। आप कभी भी हाँ या ना कर सकते हैं, और कितना प्रतिशत देना है वो भी आप तय करेंगे।

यह decision आप बाद में भी ले सकते हैं। पहले अपने उत्पाद के बारे में बताइए - यह क्या है?""",

    "capture": """अच्छा! अब मैं आपके उत्पाद के बारे में कुछ जानकारी लूंगा ताकि हम एक अच्छी listing बना सकें।"""
}
