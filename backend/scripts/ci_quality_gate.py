import os
import sys
sys.modules["tensorflow"] = None
sys.modules["keras"] = None
sys.modules["tf_keras"] = None
os.environ["TRANSFORMERS_NO_TF"] = "1"
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_quality_gate():
    logger.info("=== Starting CI/CD RAG Quality Gate ===")
    
    root_dir = os.path.dirname(os.path.dirname(__file__))
    eval_results_path = os.path.join(root_dir, "data", "eval_results.json")
    
    if not os.path.exists(eval_results_path):
        logger.error(f"Evaluation results not found at: {eval_results_path}")
        logger.error("Please run the offline evaluation pipeline first using 'python scripts/evaluate_rag.py'.")
        sys.exit(1)
        
    try:
        with open(eval_results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read evaluation results: {e}")
        sys.exit(1)
        
    logger.info("Loaded Ragas evaluation results:")
    for metric, score in results.items():
        logger.info(f"  - {metric}: {score:.4f}")
        
    # Define production baseline thresholds
    thresholds = {
        "faithfulness": 0.85,
        "answer_correctness": 0.80
    }
    
    failures = []
    print("\n" + "="*50)
    print("          CI/CD QUALITY GATE REPORT")
    print("="*50)
    
    for metric, threshold in thresholds.items():
        score = results.get(metric)
        if score is None:
            logger.warning(f"Metric '{metric}' not found in evaluation results. Skipping gate.")
            continue
            
        status = "PASSED" if score >= threshold else "FAILED"
        print(f"  {metric:<20} : Score={score:.4f} (Threshold={threshold:.4f}) -> {status}")
        
        if score < threshold:
            failures.append(f"{metric} scored {score:.4f} (required >= {threshold:.4f})")
            
    print("="*50 + "\n")
    
    if failures:
        logger.error("Quality Gate FAILED due to the following regressions:")
        for failure in failures:
            logger.error(f"  - {failure}")
        logger.error("Blocking CI/CD merge integration.")
        sys.exit(1)
    else:
        logger.info("Quality Gate PASSED. All metrics satisfy baseline production requirements.")
        logger.info("Allowing CI/CD integration and deployment.")
        sys.exit(0)

if __name__ == "__main__":
    check_quality_gate()
