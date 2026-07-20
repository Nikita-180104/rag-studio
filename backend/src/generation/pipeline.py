import time
import logging
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from config import settings
from retrieval.vector_store import VectorStoreManager
from utils.errors import RAGException, RetrievalError, GenerationError

logger = logging.getLogger(__name__)

CONDENSE_PROMPT_TEMPLATE = """Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question (which can be understood without context).

Guidelines:
1. If the follow-up question references pronouns, abbreviations, or context from the chat history (e.g., "what happens before it?", "explain that step"), rewrite it to be explicit using terms from the history.
2. If the follow-up question introduces a completely new topic, asks about a different document, or does not refer to the history (e.g., "give summary of the git sheat document", "what is git?"), do NOT merge it with the history. Keep the original question's intent intact and only correct minor spelling errors (e.g. "git sheat" -> "git cheat sheet") or make it a clear standalone search query.
3. Do NOT reply to the question, just return the rephrased standalone question.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone Question:"""

class GenerationPipeline:
    """
    Constructs the modular, highly configurable production RAG pipeline.
    Binds Hybrid retrieval, Cross-Encoder re-ranking, versioned YAML prompt loading,
    and two-layer citation grounding guardrails together under a unified execution flow.
    """
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        logger.info("Initializing Generation Pipeline with Gemini Flash...")
        self.vector_store_manager = vector_store_manager
        
        # Configure pluggable re-ranking cascade (Default fallback retriever)
        try:
            if settings.enable_reranking:
                from retrieval.re_ranker import LocalCrossEncoderReranker
                from langchain_classic.retrievers import ContextualCompressionRetriever
                
                logger.info(f"Cascade Retrieval enabled: Retrieving top-20 candidates and re-ranking to top-{settings.top_n_context} using Cross-Encoder.")
                
                base_retriever = self.vector_store_manager.get_retriever(k=20)
                reranker = LocalCrossEncoderReranker(
                    model_name=settings.reranker_model_name,
                    top_n=settings.top_n_context
                )
                
                self.retriever = ContextualCompressionRetriever(
                    base_compressor=reranker,
                    base_retriever=base_retriever
                )
            else:
                logger.info(f"Direct Retrieval enabled: Retrieving top-{settings.top_n_context} candidates from Vector DB.")
                self.retriever = self.vector_store_manager.get_retriever(k=settings.top_n_context)
        except Exception as e:
            raise RetrievalError(f"Failed to compile RAG pipeline retriever: {e}") from e
        
        # Initialize LLM based on configured provider
        provider = settings.llm_provider.lower()
        try:
            if provider == "groq":
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model=settings.groq_model_name,
                    api_key=settings.groq_api_key,
                    temperature=0,
                    max_tokens=1024,
                    max_retries=2,
                )
            else:
                self.llm = ChatGoogleGenerativeAI(
                    model=settings.active_llm_model,
                    google_api_key=settings.google_api_key,
                    temperature=0,
                    max_tokens=1024,
                    max_retries=2,
                )
        except Exception as e:
            raise GenerationError(f"Failed to initialize LLM ({provider}): {e}") from e
        
        # Initialize the prompt manager and load active version dynamically from prompts.yaml
        try:
            from generation.prompt_manager import PromptManager
            self.prompt_manager = PromptManager()
            self.prompt, self.prompt_metadata = self.prompt_manager.get_prompt(
                prompt_key="rag_prompt",
                version=settings.active_prompt_version
            )
        except Exception as e:
            raise GenerationError(f"Failed to load yaml prompt configurations: {e}") from e
        
        # Initialize our two-layer citation grounding guardrail
        try:
            from generation.guardrails import CitationGuardrail
            self.guardrail = CitationGuardrail()
        except Exception as e:
            raise GenerationError(f"Failed to instantiate CitationGuardrail system: {e}") from e

    def _format_docs(self, docs):
        """Helper to format a list of LangChain Documents into a single string with explicit source tags."""
        formatted_chunks = []
        for doc in docs:
            # Extract metadata (default to 'Unknown' if missing)
            source = doc.metadata.get('source', 'Unknown Source')
            # Extract filename from the path for cleaner citations
            filename = source.split('\\')[-1].split('/')[-1]
            page = doc.metadata.get('page', 'N/A')
            if isinstance(page, int):
                page = page + 1
            
            # Format the chunk with its specific citation tag at the top
            chunk_str = f"[Source: {filename}, Page: {page}]\n{doc.page_content}"
            formatted_chunks.append(chunk_str)
            
        return "\n\n---\n\n".join(formatted_chunks)

    def answer_question(
        self, 
        question: str, 
        search_filter: Dict[str, Any] = None, 
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes the Q&A pipeline for a given question with two-layer grounding protection,
        dynamic query-time metadata filtering, and comprehensive telemetry metrics.
        
        Returns:
            Dict[str, Any]: {
                "answer": str,
                "contexts": List[str],
                "citations": List[Dict[str, Any]],
                "telemetry": Dict[str, Any]
            }
        """
        start_time = time.time()
        logger.info(f"Processing query: '{question}'")
        
        # Resolve search query (reformulate if history is present to resolve pronouns/references)
        search_query = question
        if history and len(history) > 0:
            try:
                formatted_history = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
                condense_prompt = CONDENSE_PROMPT_TEMPLATE.format(
                    chat_history=formatted_history,
                    question=question
                )
                condense_res = self.llm.invoke(condense_prompt)
                search_query = condense_res.content.strip()
                logger.info(f"Query reformulated from '{question}' to stand-alone query: '{search_query}'")
            except Exception as e:
                logger.error(f"Failed to condense query, falling back to original: {e}")
                search_query = question
        
        # Default telemetry metrics
        candidates_count = 0
        max_score = 0.0
        layer1_status = "SKIPPED"
        layer2_status = "SKIPPED"
        input_tokens = 0
        output_tokens = 0
        
        try:
            # 1. Resolve Retriever (compiles dynamic metadata filters if passed)
            if search_filter:
                logger.info(f"Re-compiling retriever with dynamic query-time metadata filter: {search_filter}")
                if settings.enable_reranking:
                    from retrieval.re_ranker import LocalCrossEncoderReranker
                    from langchain_classic.retrievers import ContextualCompressionRetriever
                    
                    base_retriever = self.vector_store_manager.get_retriever(k=20, search_filter=search_filter)
                    reranker = LocalCrossEncoderReranker(
                        model_name=settings.reranker_model_name,
                        top_n=settings.top_n_context
                    )
                    active_retriever = ContextualCompressionRetriever(
                        base_compressor=reranker,
                        base_retriever=base_retriever
                    )
                else:
                    active_retriever = self.vector_store_manager.get_retriever(k=settings.top_n_context, search_filter=search_filter)
            else:
                active_retriever = self.retriever
            
            # 2. Retrieve candidates using the standalone search query
            try:
                docs = active_retriever.invoke(search_query)
                candidates_count = len(docs)
                logger.info(f"Raw retrieval returned {candidates_count} candidate chunks:")
                for idx, doc in enumerate(docs):
                    source = doc.metadata.get('source', 'Unknown')
                    filename = source.split('\\')[-1].split('/')[-1]
                    page = doc.metadata.get('page', -1)
                    if isinstance(page, int):
                        page = page + 1
                    logger.info(f"  [Raw Doc {idx+1}] Source: {filename}, Page: {page}, Snippet: {doc.page_content[:100].replace(chr(10), ' ')}...")
            except Exception as e:
                raise RetrievalError(f"Database query failure: {e}") from e
            
            # Extract lists for structured response
            raw_contexts = [doc.page_content for doc in docs]
            citations = []
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown Source')
                filename = source.split('\\')[-1].split('/')[-1]
                page = doc.metadata.get('page', 'N/A')
                if isinstance(page, int):
                    page = page + 1
                citations.append({
                    "source": filename,
                    "page": page,
                    "re_rank_score": doc.metadata.get('re_rank_score', 0.0)
                })
            
            # 3. Layer 1 Check: Pre-generation relevance check
            is_relevant, max_score = self.guardrail.verify_pre_generation(docs)
            if not is_relevant:
                layer1_status = "FAILED"
                logger.warning(
                    f"Layer 1 Gate triggered! Aborting generation. "
                    f"Max document relevance score ({max_score:.4f}) is below threshold ({settings.min_relevance_score:.4f})."
                )
                telemetry = self._get_telemetry_dict(start_time, candidates_count, max_score, layer1_status, layer2_status, 0, 0)
                self._log_telemetry(telemetry)
                return {
                    "answer": "I don't know based on the provided documents.",
                    "contexts": raw_contexts,
                    "citations": citations,
                    "telemetry": telemetry
                }
            
            layer1_status = "PASSED"
            
            # 4. Format context chunks
            formatted_context = self._format_docs(docs)
            logger.info("Re-ranked high-precision chunks selected for LLM Context:")
            for idx, doc in enumerate(docs):
                source = doc.metadata.get('source', 'Unknown')
                filename = source.split('\\')[-1].split('/')[-1]
                page = doc.metadata.get('page', -1)
                if isinstance(page, int):
                    page = page + 1
                score = doc.metadata.get('re_rank_score', 0.0)
                logger.info(f"  [Context Doc {idx+1}] Source: {filename}, Page: {page}, Score: {score:.4f}, Snippet: {doc.page_content[:100].replace(chr(10), ' ')}...")
            
            # 5. Invoke LLM Generation
            logger.info(f"Context is relevant. Invoking {settings.active_llm_model} for answer generation...")
            try:
                prompt_input = self.prompt.format_messages(
                    context=formatted_context,
                    question=search_query
                )
                logger.info("--- LLM PROMPT SENT TO MODEL ---")
                for msg in prompt_input:
                    logger.info(f"Message Role: {msg.type}\nContent:\n{msg.content}\n")
                logger.info("--------------------------------")
                
                response_msg = self.llm.invoke(prompt_input)
                answer = response_msg.content
                logger.info(f"--- LLM RAW RESPONSE RECEIVED ---\n{answer}\n---------------------------------")
                
                # Retrieve token usage metadata dynamically from response
                if hasattr(response_msg, "usage_metadata") and response_msg.usage_metadata:
                    input_tokens = response_msg.usage_metadata.get("input_tokens", 0)
                    output_tokens = response_msg.usage_metadata.get("output_tokens", 0)
                elif hasattr(response_msg, "response_metadata") and "token_usage" in response_msg.response_metadata:
                    token_usage = response_msg.response_metadata["token_usage"]
                    if token_usage:
                        input_tokens = token_usage.get("prompt_tokens", 0)
                        output_tokens = token_usage.get("completion_tokens", 0)
            except Exception as e:
                raise GenerationError(f"LLM generation API call failed: {e}") from e
            
            # 6. Layer 2 Check: Post-generation grounding audit
            is_grounded, reason = self.guardrail.verify_post_generation(formatted_context, answer)
            if not is_grounded:
                layer2_status = "FAILED"
                logger.warning(
                    f"Layer 2 Gate triggered! Aborting response delivery. "
                    f"Generated answer failed grounding audit: {reason}"
                )
                telemetry = self._get_telemetry_dict(start_time, candidates_count, max_score, layer1_status, layer2_status, input_tokens, output_tokens)
                self._log_telemetry(telemetry)
                return {
                    "answer": "I don't know based on the provided documents.",
                    "contexts": raw_contexts,
                    "citations": citations,
                    "telemetry": telemetry
                }
                
            layer2_status = "PASSED"
            
            telemetry = self._get_telemetry_dict(start_time, candidates_count, max_score, layer1_status, layer2_status, input_tokens, output_tokens)
            self._log_telemetry(telemetry)
            return {
                "answer": answer,
                "contexts": raw_contexts,
                "citations": citations,
                "telemetry": telemetry
            }
            
        except RAGException as re:
            logger.error(f"RAG Pipeline Boundary caught custom error: {re}")
            err_msg = str(re)
            if "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower() or "429" in err_msg:
                raise GenerationError(f"Gemini API rate limit or quota exceeded: {err_msg}") from re
            else:
                answer = f"An internal system error occurred: {err_msg}"
            return {
                "answer": answer,
                "contexts": raw_contexts if 'raw_contexts' in locals() else [],
                "citations": citations if 'citations' in locals() else [],
                "telemetry": self._get_telemetry_dict(start_time, candidates_count if 'candidates_count' in locals() else 0, max_score if 'max_score' in locals() else 0.0, layer1_status if 'layer1_status' in locals() else "ERROR", "ERROR", 0, 0)
            }
        except Exception as e:
            logger.error(f"RAG Pipeline Boundary caught unhandled exception: {e}")
            err_msg = str(e)
            if "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower() or "429" in err_msg:
                raise GenerationError(f"Gemini API rate limit or quota exceeded: {err_msg}") from e
            else:
                answer = f"An unexpected error occurred during pipeline execution: {err_msg}"
            return {
                "answer": answer,
                "contexts": raw_contexts if 'raw_contexts' in locals() else [],
                "citations": citations if 'citations' in locals() else [],
                "telemetry": self._get_telemetry_dict(start_time, candidates_count if 'candidates_count' in locals() else 0, max_score if 'max_score' in locals() else 0.0, layer1_status if 'layer1_status' in locals() else "ERROR", "ERROR", 0, 0)
            }

    def _get_telemetry_dict(
        self, 
        start_time: float, 
        docs_count: int, 
        max_score: float, 
        l1: str, 
        l2: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, Any]:
        """Compiles exact elapsed times, token counts, and transaction costs."""
        elapsed = time.time() - start_time
        
        # Pricing metrics based on provider
        if settings.llm_provider.lower() == "groq":
            # Llama-3.1-70b-versatile estimates: $0.59 / 1M input, $0.79 / 1M output
            input_cost = input_tokens * 0.00000059
            output_cost = output_tokens * 0.00000079
        else:
            # gemini-2.5-flash-lite: $0.10 / 1M input, $0.40 / 1M output
            input_cost = input_tokens * 0.00000010
            output_cost = output_tokens * 0.00000040
        total_cost = input_cost + output_cost
        
        return {
            "provider": settings.vector_db_provider,
            "prompt_version": settings.active_prompt_version,
            "reranking_enabled": settings.enable_reranking,
            "chunks_count": docs_count,
            "max_re_rank_score": max_score,
            "l1_relevance_check": l1,
            "l2_grounding_check": l2,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "transaction_cost_usd": total_cost,
            "elapsed_seconds": elapsed
        }

    def _log_telemetry(self, telemetry: Dict[str, Any]):
        """Prints a comprehensive production metrics summary."""
        print("\n" + "="*50)
        print("          RAG EXECUTION TELEMETRY SUMMARY")
        print("="*50)
        print(f"  Vector DB Provider : {telemetry['provider'].upper()}")
        print(f"  Prompt Version     : {telemetry['prompt_version']}")
        print(f"  Re-ranking Status  : {'ENABLED' if telemetry['reranking_enabled'] else 'DISABLED'}")
        print(f"  Chunks Evaluated   : {telemetry['chunks_count']}")
        print(f"  Max Re-rank Score  : {telemetry['max_re_rank_score']:.4f}")
        print(f"  L1 Relevance Check : {telemetry['l1_relevance_check']}")
        print(f"  L2 Grounding Check : {telemetry['l2_grounding_check']}")
        print(f"  Input Tokens       : {telemetry['input_tokens']}")
        print(f"  Output Tokens      : {telemetry['output_tokens']}")
        print(f"  Transaction Cost   : ${telemetry['transaction_cost_usd']:.8f} USD")
        print(f"  Total Elapsed Time : {telemetry['elapsed_seconds']:.3f} seconds")
        print("="*50 + "\n")

if __name__ == "__main__":
    print("Generation Pipeline module ready.")
