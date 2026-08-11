import logging
from scraper import scrape_all
from cleaner import clean_all
from llm_reasoner import reason_all
from verifier import verify_predictions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

logger.info("=== Running Prediction Verification ===")
current = scrape_all()
current = clean_all(current)
current = reason_all(current)
verify_predictions(current)
logger.info("Verification complete.")