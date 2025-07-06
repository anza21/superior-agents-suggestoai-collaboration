import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.agent.affiliate_promoter import AffiliatePromoterAgent, AffiliatePromoterPromptGenerator
from src.container import ContainerManager
from src.genner.Base import Genner
from src.client.rag import RAGClient
from src.db import APIDB
from src.summarizer import get_summarizer
from src.flows.affiliate_promoter import autonomous_affiliate_promoter_loop
from loguru import logger
import logging

# Mock setup (προσαρμόστε αν έχετε πραγματικά components)
class DummyGenner(Genner):
    def __init__(self, identifier="dummy", do_stream=False):
        super().__init__(identifier, do_stream)
    def ch_completion(self, *args, **kwargs):
        return ""
    def generate_code(self, *args, **kwargs):
        return ""
    def extract_code(self, *args, **kwargs):
        return ""
    def extract_list(self, *args, **kwargs):
        return []
    def generate_list(self, *args, **kwargs):
        return []

class DummyRAG(RAGClient):
    def __init__(self, agent_id="demo_affiliate_agent", session_id="demo_session", base_url="http://localhost:8080"):
        super().__init__(agent_id, session_id, base_url)

class DummyDB(APIDB):
    def __init__(self, base_url="http://localhost:9020/api_v1", api_key="demo_api_key"):
        super().__init__(base_url, api_key)
    def insert_chat_history(self, *args, **kwargs):
        pass
    def insert_strategy_and_result(self, *args, **kwargs):
        pass

class DummyContainerManager:
    def run_code_in_con(self, *args, **kwargs):
        return ("", "")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = AffiliatePromoterAgent(
        agent_id="demo_affiliate_agent",
        rag=DummyRAG(),
        db=DummyDB(),
        sensor=None,
        genner=DummyGenner(),
        container_manager=DummyContainerManager(),
        prompt_generator=AffiliatePromoterPromptGenerator(),
    )
    session_id = "demo_session"
    role = "affiliate_promoter"
    time_str = "24h"
    apis = ["ebay", "aliexpress", "amazon"]
    metric_name = "affiliate_sales"
    summarizer = get_summarizer(agent.genner)
    # Demo: τρέχουμε μόνο 2 κύκλους με μικρό interval
    import threading
    import time
    def run_limited_cycles():
        for _ in range(2):
            logger.info("=== Νέος κύκλος affiliate promotion (demo) ===")
            from src.flows.affiliate_promoter import unassisted_flow
            unassisted_flow(
                agent=agent,
                session_id=session_id,
                role=role,
                time=time_str,
                apis=apis,
                metric_name=metric_name,
                prev_strat=None,
                notif_str=None,
                summarizer=summarizer,
            )
            time.sleep(5)
        print("Demo ολοκληρώθηκε!")
    run_limited_cycles() 