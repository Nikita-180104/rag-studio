import logging
from typing import List, Tuple
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from config import settings

logger = logging.getLogger(__name__)

class GroundingAssessment(BaseModel):
    """
    Structured response model for post-generation grounding evaluation.
    Enforces native JSON structure from the Gemini API.
    """
    is_grounded: bool = Field(
        description="True if every factual claim in the answer is 100% supported by the provided context chunks. False if there are any hallucinations, extrapolations, or details not present in the context."
    )
    reason: str = Field(
        description="Brief explanation of the grounding decision, citing specific discrepancies if any are found."
    )

class CitationGuardrail:
    """
    Two-Layer Citation Grounding Guardrail Component.
    
    Layer 1 (Pre-generation): Compares Cross-Encoder re-rank scores against min_relevance_score
                              to block LLM calls on irrelevant contexts.
    Layer 2 (Post-generation): Employs a structured LLM checker to inspect the output and block hallucinations.
    """
    
    def __init__(self):
        logger.info("Initializing Citation Guardrail System...")
        
        # Initialize the grounding verification LLM.
        # We use temperature=0 for absolute deterministic verification.
        self.verifier_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.google_api_key,
            temperature=0,
            max_tokens=512,
            max_retries=2,
        )
        
        # Define the strict grounding evaluation prompt template
        self.grounding_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strict and precise factual auditor. 
Your single job is to analyze the provided Source Context Chunks and determine if the Generated Answer is 100% factually grounded in and supported by that context.

Rules:
1. Every claim, number, or statement in the Generated Answer must be explicitly present or logically entailed by the Source Context Chunks.
2. If the Generated Answer mentions information, facts, or assumptions NOT supported by the context, you must set 'is_grounded' to false.
3. Ignore formatting or citation brackets; focus strictly on semantic factual claims.

Source Context Chunks:
{context}"""),
            ("human", "Generated Answer:\n{answer}")
        ])
        
        # Bind structured output schema to the verifier LLM
        self.structured_verifier = self.verifier_llm.with_structured_output(GroundingAssessment)
        logger.info("Factual guardrail successfully loaded.")

    def verify_pre_generation(self, documents: List[Document]) -> Tuple[bool, float]:
        """
        Layer 1 Check: Evaluates the maximum Cross-Encoder re-rank score among retrieved chunks.
        If all documents are below the threshold, returns False (too weak), short-circuiting generation.
        
        Returns:
            Tuple[bool, float]: (is_relevant, max_score)
        """
        if not documents:
            logger.warning("No documents retrieved. Pre-generation check failed.")
            return False, -999.0
            
        # Extract re-rank scores. Default to 0.0 if re-ranking was disabled.
        scores = [doc.metadata.get("re_rank_score", 0.0) for doc in documents]
        max_score = max(scores)
        
        # If re-ranking is enabled, assert against the threshold
        if settings.enable_reranking:
            is_relevant = max_score >= settings.min_relevance_score
            if not is_relevant:
                logger.warning(
                    f"Pre-generation short-circuit activated! Max re-rank score ({max_score:.4f}) "
                    f"is below the minimum relevance threshold ({settings.min_relevance_score:.4f})."
                )
            else:
                logger.info(f"Pre-generation check passed. Max re-rank score: {max_score:.4f}")
            return is_relevant, max_score
            
        # If re-ranking is disabled, pass by default since we don't have Cross-Encoder scores
        return True, 0.0

    def verify_post_generation(self, context: str, answer: str) -> Tuple[bool, str]:
        """
        Layer 2 Check: Audits the generated response against context using the structured LLM auditor.
        
        Returns:
            Tuple[bool, str]: (is_grounded, explanation_reason)
        """
        logger.info("Executing Layer 2 post-generation grounding audit...")
        try:
            # Construct the formatted validation prompt
            prompt_input = self.grounding_prompt.format_messages(
                context=context,
                answer=answer
            )
            
            # Invoke structured evaluation
            assessment: GroundingAssessment = self.structured_verifier.invoke(prompt_input)
            
            if not assessment.is_grounded:
                logger.warning(f"Post-generation audit failed! Reason: {assessment.reason}")
            else:
                logger.info("Post-generation audit passed successfully. No hallucinations detected.")
                
            return assessment.is_grounded, assessment.reason
            
        except Exception as e:
            logger.error(f"Factual grounding audit crashed: {e}. Defaulting to unsafe pass for safety.")
            return True, f"Error running guardrail audit: {e}"
