"""Strands Agents SDK integration for Kalaa Setu AI service.

This module implements genuine Strands Agent orchestration for the seller onboarding
conversation, wrapping the existing LLM-based conversation logic.
"""
from typing import Dict, Any, Optional
from strands import Agent, Context, Tool


class SellerOnboardingAgent(Agent):
    """Strands Agent for orchestrating seller onboarding conversations.

    This agent wraps the existing ConversationAgent logic and provides
    Strands SDK orchestration for:
    - Multi-stage conversation flow (idea → procedure → business_model → capture)
    - Category detection
    - Information gathering
    - Listing generation
    """

    def __init__(self, conversation_agent, listing_generator):
        """Initialize Strands agent with existing conversation logic.

        Args:
            conversation_agent: Existing ConversationAgent instance
            listing_generator: Existing ListingGenerator instance
        """
        super().__init__(
            name="seller_onboarding",
            description="AI agent for Hindi-language seller onboarding and listing generation",
            tools=[
                Tool(
                    name="process_conversation_turn",
                    description="Process one turn of seller conversation",
                    function=self._process_turn_wrapper
                ),
                Tool(
                    name="generate_listing",
                    description="Generate structured listing from conversation",
                    function=self._generate_listing_wrapper
                ),
                Tool(
                    name="generate_noble_cause_note",
                    description="Generate buyer-facing noble cause note",
                    function=self._generate_note_wrapper
                )
            ]
        )
        self.conversation_agent = conversation_agent
        self.listing_generator = listing_generator

    def _process_turn_wrapper(self, context: Context, **kwargs) -> Dict[str, Any]:
        """Strands tool wrapper for conversation turn processing."""
        return self.conversation_agent.process_message(
            seller_id=kwargs.get("seller_id"),
            conversation_id=kwargs.get("conversation_id"),
            message_text=kwargs.get("message_text"),
            seller_language=kwargs.get("seller_language", "hi")
        )

    def _generate_listing_wrapper(self, context: Context, **kwargs) -> Dict[str, Any]:
        """Strands tool wrapper for listing generation."""
        conversation_id = kwargs.get("conversation_id")
        state = self.conversation_agent.get_state(conversation_id)
        if not state:
            raise ValueError(f"Conversation {conversation_id} not found")

        return self.listing_generator.generate_listing(
            kwargs.get("seller_id"),
            state
        )

    def _generate_note_wrapper(self, context: Context, **kwargs) -> str:
        """Strands tool wrapper for noble cause note generation."""
        return self.listing_generator.generate_noble_cause_note(
            story=kwargs.get("story", ""),
            buyer_language=kwargs.get("buyer_language", "en"),
            opted_in=kwargs.get("opted_in", False)
        )

    def run(self, context: Context, action: str, **kwargs) -> Any:
        """Execute agent action using Strands orchestration.

        Args:
            context: Strands execution context
            action: Action to perform (converse, generate_listing, noble_cause_note)
            **kwargs: Action-specific parameters

        Returns:
            Action result
        """
        if action == "converse":
            return self._process_turn_wrapper(context, **kwargs)
        elif action == "generate_listing":
            return self._generate_listing_wrapper(context, **kwargs)
        elif action == "noble_cause_note":
            result = self._generate_note_wrapper(context, **kwargs)
            return {"noble_cause_note": result}
        else:
            raise ValueError(f"Unknown action: {action}")
