from datetime import datetime
import re
from textwrap import dedent
from typing import Dict, List, Optional, Set, Tuple
import os
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time
import base64
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import hmac
import hashlib

from result import Err, Ok, Result

from src.client.rag import RAGClient
from src.container import ContainerManager
from src.db import APIDB
from src.genner.Base import Genner
from src.sensor.affiliate_promoter import AffiliatePromoterSensor
from src.my_types import ChatHistory, Message
from src.datatypes.affiliate_promoter import ProductData


class AffiliatePromoterPromptGenerator:
	def __init__(self, prompts: Optional[Dict[str, str]] = None):
		"""
		Initialize with custom prompts for each function.

		Args:
		        prompts: Dictionary containing custom prompts for each function
		"""
		if prompts is None:
			prompts = self.get_default_prompts()
		self._validate_prompts(prompts)
		self.prompts = prompts

	def _extract_default_placeholders(self) -> Dict[str, Set[str]]:
		"""Extract placeholders from default prompts to use as required placeholders."""
		placeholder_pattern = re.compile(r"{([^}]+)}")
		return {
			prompt_name: {
				f"{{{p}}}" for p in placeholder_pattern.findall(prompt_content)
			}
			for prompt_name, prompt_content in self.get_default_prompts().items()
		}

	def _validate_prompts(self, prompts: Dict[str, str]) -> None:
		"""
		Validate prompts for required and unexpected placeholders.

		Args:
		        prompts: Dictionary of prompt name to prompt content

		Raises:
		        ValueError: If prompts are missing required placeholders or contain unexpected ones
		"""
		required_placeholders = self._extract_default_placeholders()

		# Check all required prompts exist
		missing_prompts = set(required_placeholders.keys()) - set(prompts.keys())
		if missing_prompts:
			raise ValueError(f"Missing required prompts: {missing_prompts}")

		# Extract placeholders using regex
		placeholder_pattern = re.compile(r"{([^}]+)}")

		# Check each prompt for missing and unexpected placeholders
		for prompt_name, prompt_content in prompts.items():
			if prompt_name not in required_placeholders:
				continue

			actual_placeholders = {
				f"{{{p}}}" for p in placeholder_pattern.findall(prompt_content)
			}
			required_set = required_placeholders[prompt_name]

			# Check for missing placeholders
			missing = required_set - actual_placeholders
			if missing:
				raise ValueError(
					f"Missing required placeholders in {prompt_name}: {missing}"
				)

			# Check for unexpected placeholders
			unexpected = actual_placeholders - required_set
			if unexpected:
				raise ValueError(
					f"Unexpected placeholders in {prompt_name}: {unexpected}"
				)

	def generate_system_prompt(
		self, role: str, time: str, metric_name: str, metric_state: str
	) -> str:
		"""
		Generate a system prompt for the affiliate promoter agent.

		This method creates a system prompt that sets the context for the agent,
		including its role, current date, goal, and current metric state.

		Args:
		        role (str): The role of the agent (e.g., "influencer")
		        time (str): Time frame for the affiliate promotion goal
		        metric_name (str): Name of the metric to maximize
		        metric_state (str): Current state of the metric

		Returns:
		        str: Formatted system prompt
		"""
		now = datetime.now()
		today_date = now.strftime("%Y-%m-%d")

		return self.prompts["system_prompt"].format(
			role=role,
			today_date=today_date,
			metric_name=metric_name,
			time=time,
			metric_state=metric_state,
		)

	def generate_research_code_prompt_first(self, apis: List[str]) -> str:
		"""
		Generate a prompt for the first-time research code generation.

		This method creates a prompt for generating research code when the agent
		has no prior context or history to work with.

		Args:
		        apis (List[str]): List of APIs available to the agent

		Returns:
		        str: Formatted prompt for first-time research code generation
		"""
		apis_str = ",\n".join(apis) if apis else self._get_default_apis_str()

		return self.prompts["research_code_prompt_first"].format(apis_str=apis_str)

	def generate_research_code_prompt(
		self,
		notifications_str: str,
		prev_strategy: str,
		rag_summary: str,
		before_metric_state: str,
		after_metric_state: str,
	) -> str:
		"""
		Generate a prompt for research code generation with context.

		This method creates a prompt for generating research code when the agent
		has prior context, including notifications, previous strategies, and RAG results.

		Args:
		        notifications_str (str): String containing recent notifications
		        prev_strategy (str): Description of the previous strategy
		        rag_summary (str): Summary from retrieval-augmented generation
		        before_metric_state (str): State of the metric before strategy execution
		        after_metric_state (str): State of the metric after strategy execution

		Returns:
		        str: Formatted prompt for research code generation
		"""
		return self.prompts["research_code_prompt"].format(
			notifications_str=notifications_str,
			prev_strategy=prev_strategy,
			rag_summary=rag_summary,
			before_metric_state=before_metric_state,
			after_metric_state=after_metric_state,
		)

	def generate_strategy_prompt(
		self,
		notifications_str: str,
		research_output_str: str,
		metric_name: str,
		time: str,
	) -> str:
		"""
		Generate a prompt for strategy formulation.

		This method creates a prompt for generating an affiliate promotion strategy based on
		notifications and research output.

		Args:
		        notifications_str (str): String containing recent notifications
		        research_output_str (str): Output from the research code
		        metric_name (str): Name of the metric to maximize
		        time (str): Time frame for the affiliate promotion goal

		Returns:
		        str: Formatted prompt for strategy formulation
		"""
		return self.prompts["strategy_prompt"].format(
			notifications_str=notifications_str,
			research_output_str=research_output_str,
			metric_name=metric_name,
			time=time,
		)

	def generate_affiliate_promoter_code_prompt(
		self, strategy_output: str, apis: List[str]
	) -> str:
		"""Generate prompt for implementing the strategy"""
		apis_str = ",\n".join(apis) if apis else self._get_default_apis_str()
		return self.prompts["affiliate_promoter_code_prompt"].format(
			strategy_output=strategy_output, apis_str=apis_str
		)

	def regen_code(self, previous_code: str, errors: str) -> str:
		"""Generate prompt for fixing code errors"""
		return self.prompts["regen_code_prompt"].format(
			errors=errors, previous_code=previous_code
		)

	@staticmethod
	def _get_default_apis_str() -> str:
		"""Get default list of available APIs"""
		default_apis = [
			dedent("""
            Twitter API v1.1:
            Required env vars:
            - TWITTER_API_KEY
            - TWITTER_API_KEY_SECRET
            - TWITTER_ACCESS_TOKEN
            - TWITTER_ACCESS_TOKEN_SECRET
            
            Example Usage:
            import tweepy
            import os
            from dotenv import load_dotenv

            def main():
                load_dotenv()
                
                # Initialize Twitter API v1.1 (not v2)
                auth = tweepy.OAuth1UserHandler(
                    os.getenv("TWITTER_API_KEY"),
                    os.getenv("TWITTER_API_KEY_SECRET"),
                    os.getenv("TWITTER_ACCESS_TOKEN"),
                    os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
                )
                api = tweepy.API(auth)
                
                try:
                    # Post tweet using v1.1 endpoint
                    tweet_text = "Learn how to use the user Tweet timeline and user mention timeline endpoints in the X API v2 to explore Tweet https://t.co/56a0vZUx7i"
                    tweet = api.update_status(tweet_text)
                    print(f"Posted to Twitter: {tweet.text}")
                except Exception as e:
                    print(f"Error posting to Twitter: {str(e)}")
                    raise

            if __name__ == "__main__":
                main()
            """).strip()
		]
		return ",\n".join(default_apis)

	@staticmethod
	def get_default_prompts() -> Dict[str, str]:
		"""Get the complete set of default prompts that can be customized."""
		return {
			"system_prompt": dedent("""
                You are a {role} social media influencer.
                Today's date is {today_date}.
                Your goal is to maximize {metric_name} within {time}
                You are currently at {metric_state}
            """).strip(),
			#
			#
			#
			"research_code_prompt_first": dedent("""
                You know nothing about your environment.
                What do you do now?
                You can use the following APIs to do research:
                <APIs>
                {apis_str}
                </APIs>
                You are to print for everything, and raise every error or unexpected behavior of the program.
                Please write code using the format below to research the state of the market.
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....
                
                main()
                ```
        """).strip(),
			#
			#
			#
			"research_code_prompt": dedent("""
                Here is what is going on in your environment right now : 
                <LatestNotification>
                {notifications_str}
                </LatestNotification>
                Here is what you just tried : 
                <PrevStrategy>
                {prev_strategy} 
                </PrevStrategy>
                For reference, in the past when you encountered a similar situation you reasoned as follows:
                <RAG>
                {rag_summary}
                </RAG>
                The result of this RAG was
                <BeforeStrategyExecution>
                {before_metric_state}
                </BeforeStrategyExecution>
                <AfterStrategyExecution>
                {after_metric_state}
                </AfterStrategyExecution>
                You are to print for everything, and raise every error or unexpected behavior of the program.
                Please write code using format below to research what is going on in the world and how best to react to it.
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....
                
                main()
                ```
            """).strip(),
			#
			#
			#
			"strategy_prompt": dedent("""
                You just learnt the following information: 
                <LatestNotification>
                {notifications_str}
                </LatestNotifications>
                <ResearchOutput>
                {research_output_str}
                </ResearchOutput>
                Decide what what you should do to help you maximize {metric_name} within {time}. 
                Choose one action and write a short paragraph explaining how you will do it.
        """).strip(),
			#
			#
			#
			"affiliate_promoter_code_prompt": dedent("""
                Please write code to implement this strategy:
                <Strategy>
                {strategy_output}
                </Strategy>
                You have the following APIs:
                <APIs>
                {apis_str}
                </APIs>
                Format the code as follows:
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....

                main()
                ```
            """).strip(),
			#
			#
			#
			"regen_code_prompt": dedent("""
                Given these errors:
                <Errors>
                {errors}
                </Errors>
                And the code it's from:
                <Code>
                {previous_code}
                </Code>
                You are to generate code that fixes the error but doesn't stray too much from the original code, in this format:
                ```python
                from dotenv import load_dotenv
                import ...

                load_dotenv()

                def main():
                    ....

                main()
                ```
                Please generate the code.
            """).strip(),
		}


class AffiliatePromoterAgent:
	"""
	Agent responsible for executing affiliate promotion strategies based on social media data and notifications.

	This class orchestrates the entire affiliate promotion workflow, including system preparation,
	research code generation, strategy formulation, and affiliate promotion code execution.
	It integrates with various components like RAG, database, sensors, and code execution
	to create a complete affiliate promoter agent.
	"""

	def __init__(
		self,
		agent_id: str,
		rag: RAGClient,
		db: APIDB,
		sensor: AffiliatePromoterSensor,
		genner: Genner,
		container_manager: ContainerManager,
		prompt_generator: AffiliatePromoterPromptGenerator,
	):
		"""
		Initialize the affiliate promoter agent with all required components.

		Args:
		        agent_id (str): Unique identifier for this agent
		        rag (RAGClient): Client for retrieval-augmented generation
		        db (APIDB): Database client for storing and retrieving data
		        sensor (AffiliatePromoterSensor): Sensor for monitoring affiliate promotion-related metrics
		        genner (Genner): Generator for creating code and strategies
		        container_manager (ContainerManager): Manager for code execution in containers
		        prompt_generator (AffiliatePromoterPromptGenerator): Generator for creating prompts
		"""
		self.agent_id = agent_id
		self.db = db
		self.rag = rag
		self.sensor = sensor
		self.genner = genner
		self.container_manager = container_manager
		self.prompt_generator = prompt_generator

		self.chat_history = ChatHistory()

	def reset(self) -> None:
		"""
		Reset the agent's chat history.

		This method clears any existing conversation history to start fresh.
		"""
		self.chat_history = ChatHistory()

	def prepare_system(self, role: str, time: str, metric_name: str, metric_state: str):
		"""
		Prepare the system prompt for the agent.

		This method generates the initial system prompt that sets the context
		for the agent's operation, including its role, time context, and metrics.

		Args:
		        role (str): The role of the agent (e.g., "influencer")
		        time (str): Current time information
		        metric_name (str): Name of the metric to track
		        metric_state (str): Current state of the metric

		Returns:
		        ChatHistory: Chat history with the system prompt
		"""
		ctx_ch = ChatHistory(
			Message(
				role="system",
				content=self.prompt_generator.generate_system_prompt(
					role=role,
					time=time,
					metric_name=metric_name,
					metric_state=metric_state,
				),
			)
		)

		return ctx_ch

	def gen_research_code_on_first(
		self, apis: List[str]
	) -> Result[Tuple[str, ChatHistory], str]:
		"""
		Generate research code for the first time.

		This method creates research code when the agent has no prior context,
		using only the available APIs.

		Args:
		        apis (List[str]): List of APIs available to the agent

		Returns:
		        Result[Tuple[str, ChatHistory], str]: Success with code and chat history,
		                or error message
		"""
		ctx_ch = ChatHistory(
			Message(
				role="user",
				content=self.prompt_generator.generate_research_code_prompt_first(
					apis=apis
				),
			)
		)

		gen_result = self.genner.ch_completion(self.chat_history + ctx_ch)

		if err := gen_result.err():
			return Err(f"AffiliatePromoterAgent.gen_research_code_on_first, err: \n{err}")

		response = gen_result.unwrap()
		ctx_ch = ctx_ch.append(Message(role="assistant", content=response))

		return Ok((response, ctx_ch))

	def gen_research_code(
		self,
		notifications_str: str,
		prev_strategy: str,
		rag_summary: str,
		before_metric_state: str,
		after_metric_state: str,
	) -> Result[Tuple[str, ChatHistory], str]:
		"""
		Generate research code with context.

		This method creates research code when the agent has prior context,
		including notifications, previous strategies, and RAG results.

		Args:
		        notifications_str (str): String containing recent notifications
		        prev_strategy (str): Description of the previous strategy
		        rag_summary (str): Summary from retrieval-augmented generation
		        before_metric_state (str): State of the metric before strategy execution
		        after_metric_state (str): State of the metric after strategy execution

		Returns:
		        Result[Tuple[str, ChatHistory], str]: Success with code and chat history,
		                or error message
		"""
		ctx_ch = ChatHistory(
			Message(
				role="user",
				content=self.prompt_generator.generate_research_code_prompt(
					notifications_str=notifications_str,
					prev_strategy=prev_strategy,
					rag_summary=rag_summary,
					before_metric_state=before_metric_state,
					after_metric_state=after_metric_state,
				),
			)
		)

		gen_result = self.genner.ch_completion(self.chat_history + ctx_ch)

		if err := gen_result.err():
			return Err(f"AffiliatePromoterAgent.gen_research_code, err: \n{err}")

		response = gen_result.unwrap()
		ctx_ch = ctx_ch.append(Message(role="assistant", content=response))

		return Ok((response, ctx_ch))

	def gen_strategy(
		self,
		notifications_str: str,
		research_output_str: str,
		metric_name: str,
		time: str,
	) -> Result[Tuple[str, ChatHistory], str]:
		"""
		Generate an affiliate promotion strategy.

		This method formulates an affiliate promotion strategy based on notifications
		and research output.

		Args:
		        notifications_str (str): String containing recent notifications
		        research_output_str (str): Output from the research code
		        metric_name (str): Name of the metric to maximize
		        time (str): Time frame for the affiliate promotion goal

		Returns:
		        Result[Tuple[str, ChatHistory], str]: Success with strategy and chat history,
		                or error message
		"""
		ctx_ch = ChatHistory(
			Message(
				role="user",
				content=self.prompt_generator.generate_strategy_prompt(
					notifications_str=notifications_str,
					research_output_str=research_output_str,
					metric_name=metric_name,
					time=time,
				),
			)
		)

		gen_result = self.genner.ch_completion(self.chat_history + ctx_ch)

		if err := gen_result.err():
			return Err(f"AffiliatePromoterAgent.gen_strategy, err: \n{err}")

		response = gen_result.unwrap()
		ctx_ch = ctx_ch.append(Message(role="assistant", content=response))

		return Ok((response, ctx_ch))

	def gen_affiliate_promoter_code(
		self,
		strategy_output: str,
		apis: List[str],
	) -> Result[Tuple[str, ChatHistory], str]:
		"""
		Generate code for implementing an affiliate promotion strategy.

		This method creates code that will implement an affiliate promotion strategy
		using the available APIs.

		Args:
		        strategy_output (str): Output from the strategy formulation
		        apis (List[str]): List of APIs available to the agent

		Returns:
		        Result[Tuple[str, ChatHistory], str]: Success with code and chat history,
		                or error message
		"""
		ctx_ch = ChatHistory(
			Message(
				role="user",
				content=self.prompt_generator.generate_affiliate_promoter_code_prompt(
					strategy_output=strategy_output,
					apis=apis,
				),
			)
		)

		gen_result = self.genner.generate_code(self.chat_history + ctx_ch)

		if err := gen_result.err():
			return Err(f"AffiliatePromoterAgent.gen_affiliate_promoter_code, err: \n{err}")

		processed_codes, raw_response = gen_result.unwrap()
		ctx_ch = ctx_ch.append(Message(role="assistant", content=raw_response))

		return Ok((processed_codes[0], ctx_ch))

	def gen_better_code(
		self, prev_code: str, errors: str
	) -> Result[Tuple[str, ChatHistory], str]:
		"""
		Generate improved code after errors.

		This method regenerates code that encountered errors during execution,
		using the original code and error messages to create a fixed version.

		Args:
		        prev_code (str): The code that encountered errors
		        errors (str): Error messages from code execution

		Returns:
		        Result[Tuple[str, ChatHistory], str]: Success with improved code and chat history,
		                or error message
		"""
		ctx_ch = ChatHistory(
			Message(
				role="user",
				content=self.prompt_generator.regen_code(prev_code, errors),
			)
		)

		gen_result = self.genner.generate_code(self.chat_history + ctx_ch)

		if err := gen_result.err():
			return Err(f"AffiliatePromoterAgent.gen_better_code, err: \n{err}")

		processed_codes, raw_response = gen_result.unwrap()
		ctx_ch = ctx_ch.append(Message(role="assistant", content=raw_response))

		return Ok((processed_codes[0], ctx_ch))


class AliExpressAPIClient:
	def __init__(self):
		self.api_key = os.getenv("ALIEXPRESS_API_KEY")
		self.api_secret = os.getenv("ALIEXPRESS_API_SECRET")
		self.pid = os.getenv("ALIEXPRESS_PID")
		self.request_count = 0
		self.request_limit = 5000  # Example limit

	def can_request(self):
		return self.request_count < self.request_limit

	def make_signature(self, params):
		sorted_items = sorted(params.items())
		concat = ''.join(f"{k}{v}" for k, v in sorted_items)
		signature = hmac.new(self.api_secret.encode('utf-8'), concat.encode('utf-8'), hashlib.sha256).hexdigest().upper()
		return signature

	def search_products(self, query="smartwatch", limit=5):
		if not self.can_request():
			print("[AliExpress] Request limit reached for this month!")
			return []
		url = "https://api-sg.aliexpress.com/sync"
		timestamp = str(int(time.time() * 1000))
		params = {
			"app_key": self.api_key,
			"timestamp": timestamp,
			"sign_method": "sha256",
			"method": "aliexpress.affiliate.product.query",
			"keywords": query,
			"page_no": "1",
			"page_size": str(limit),
			"fields": "productId,productTitle,productUrl,productImage,originalPrice,salePrice,promotion_link,product_detail_url",
		}
		if self.pid:
			params["tracking_id"] = self.pid
		sign = self.make_signature(params)
		params["sign"] = sign
		try:
			response = requests.get(url, params=params, timeout=10)
			self.request_count += 1
			if response.status_code == 200:
				data = response.json()
				products = []
				items = data.get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
				for item in items:
					affiliate_link = item.get("promotion_link") or item.get("product_detail_url", "")
					# Ensure tracking_id is in the link
					if affiliate_link and self.pid and "tracking_id" not in affiliate_link:
						if "?" in affiliate_link:
							affiliate_link += f"&tracking_id={self.pid}"
						else:
							affiliate_link += f"?tracking_id={self.pid}"
					if self.pid in affiliate_link:
						print(f"✅ tracking_id FOUND in affiliate link: {affiliate_link}")
					else:
						print(f"❌ tracking_id NOT FOUND in affiliate link: {affiliate_link}")
					products.append(ProductData(
						title=item.get("product_title", ""),
						price=float(item.get("target_sale_price", 0)),
						url=item.get("product_detail_url", ""),
						image=item.get("product_main_image_url", ""),
						affiliate_link=affiliate_link,
						source="aliexpress",
						description="",
						rating=None,
						reviews=None,
						currency=item.get("target_sale_price_currency", "USD"),
						guarantees=None,
						return_policy=None,
						seller_trust=None,
						shipping_info=None,
						certifications=None,
						official_store=None,
					))
				return products
			else:
				print(f"[AliExpress] API error: {response.status_code}")
				print(response.text)
				return []
		except Exception as e:
			print("[AliExpress] API exception:", e)
			return []


load_dotenv()
EBAY_CAMPID = os.getenv("EBAY_CAMPID")

def add_ebay_affiliate_params(url, campid):
	parsed = urlparse(url)
	qs = parse_qs(parsed.query)
	qs["mkcid"] = ["1"]
	qs["mkrid"] = ["711-53200-19255-0"]
	qs["siteid"] = ["0"]
	qs["campid"] = [campid]
	qs["toolid"] = ["10001"]
	qs["mkevt"] = ["1"]
	new_query = urlencode(qs, doseq=True)
	new_url = urlunparse(parsed._replace(query=new_query))
	return new_url

class EbayAPIClient:
	def __init__(self):
		self.user_token = os.getenv("EBAY_USER_TOKEN")
		self.refresh_token = os.getenv("EBAY_REFRESH_TOKEN")
		self.client_id = os.getenv("EBAY_CLIENT_ID")
		self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
		self.base_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
		self.request_count = 0
		self.request_limit = 5000  # Συνήθως 5,000 calls/day για production
		self.token_expiry = 0

	def refresh_access_token(self):
		auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
		url = "https://api.ebay.com/identity/v1/oauth2/token"
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
			"Authorization": f"Basic {auth}"
		}
		data = {
			"grant_type": "refresh_token",
			"refresh_token": self.refresh_token,
			"scope": "https://api.ebay.com/oauth/api_scope"
		}
		response = requests.post(url, headers=headers, data=data)
		if response.status_code == 200:
			token_data = response.json()
			self.user_token = token_data["access_token"]
			self.token_expiry = time.time() + token_data.get("expires_in", 7200) - 60
			# Αυτόματη αποθήκευση στο .env
			self.update_env_token(self.user_token)
			return True
		else:
			print("[eBay] Failed to refresh token:", response.text)
			return False

	def update_env_token(self, new_token):
		env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
		try:
			with open(env_path, "r") as f:
				lines = f.readlines()
			with open(env_path, "w") as f:
				for line in lines:
					if line.startswith("EBAY_USER_TOKEN="):
						f.write(f"EBAY_USER_TOKEN={new_token}\n")
					else:
						f.write(line)
			print("[eBay] Updated EBAY_USER_TOKEN in .env!")
		except Exception as e:
			print("[eBay] Could not update .env:", e)

	def can_request(self):
		return self.request_count < self.request_limit

	def get_valid_token(self):
		if not self.user_token or time.time() > self.token_expiry:
			self.refresh_access_token()
		return self.user_token

	def search_products(self, query="laptop", limit=5):
		if not self.can_request():
			print("[eBay] Request limit reached for today!")
			return []
		headers = {
			"Authorization": f"Bearer {self.get_valid_token()}",
			"Content-Type": "application/json"
		}
		params = {"q": query, "limit": limit}
		try:
			response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
			self.request_count += 1
			if response.status_code == 401:
				print("[eBay] Token expired or invalid, refreshing...")
				if self.refresh_access_token():
					headers["Authorization"] = f"Bearer {self.user_token}"
					response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
			if response.status_code == 200:
				data = response.json()
				products = []
				for item in data.get("itemSummaries", []):
					affiliate_url = add_ebay_affiliate_params(item.get("itemWebUrl", ""), EBAY_CAMPID)
					products.append(ProductData(
						title=item.get("title", ""),
						price=float(item.get("price", {}).get("value", 0)),
						url=item.get("itemWebUrl", ""),
						image=item.get("image", {}).get("imageUrl", ""),
						affiliate_link=affiliate_url,
						source="ebay",
						description=item.get("condition", ""),
						rating=None,
						reviews=None,
						currency=item.get("price", {}).get("currency", "USD"),
						guarantees=None,
						return_policy=None,
						seller_trust=f"{item.get('seller', {}).get('username', '')} ({item.get('seller', {}).get('feedbackPercentage', '')}%, {item.get('seller', {}).get('feedbackScore', '')} reviews)",
						shipping_info=f"Shipping: {item.get('shippingOptions', [{}])[0].get('shippingCost', {}).get('value', 'N/A')} {item.get('shippingOptions', [{}])[0].get('shippingCost', {}).get('currency', '')}" if item.get('shippingOptions') else None,
						certifications=None,
						official_store=None,
					))
				return products
			else:
				print(f"[eBay] API error: {response.status_code}")
				return []
		except Exception as e:
			print("[eBay] API exception:", e)
			return []


class DevtoAPIClient:
	def __init__(self):
		self.api_key = os.getenv("DEVTO_API_KEY")
		self.base_url = "https://dev.to/api/articles"

	def publish_article(self, title, body_markdown, tags=None, canonical_url=None, published=True):
		headers = {
			"api-key": self.api_key,
			"Content-Type": "application/json"
		}
		payload = {
			"article": {
				"title": title,
				"body_markdown": body_markdown,
				"published": published,
			}
		}
		if tags:
			payload["article"]["tags"] = tags
		if canonical_url:
			payload["article"]["canonical_url"] = canonical_url
		try:
			response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
			if response.status_code in [200, 201]:
				print(f"[Dev.to] Article published: {title}")
				return response.json()
			else:
				print(f"[Dev.to] API error: {response.status_code}")
				print(response.text)
				return None
		except Exception as e:
			print("[Dev.to] API exception:", e)
			return None


class HashnodeAPIClient:
	def __init__(self):
		self.api_key = os.getenv("HASHNODE_TOKEN")
		self.base_url = "https://api.hashnode.com/"
		self.publication_id = os.getenv("HASHNODE_PUBLICATION_ID")  # Optional, αν έχεις publication

	def publish_article(self, title, content_markdown, tags=None, published=True):
		headers = {
			"Authorization": self.api_key,
			"Content-Type": "application/json"
		}
		# Hashnode uses GraphQL
		query = """
		mutation CreateStory($input: CreateStoryInput!) {
		  createStory(input: $input) {
			code
			success
			message
			post {
			  title
			  slug
			  publication {
				id
			  }
			}
		  }
		}
		"""
		variables = {
			"input": {
				"title": title,
				"contentMarkdown": content_markdown,
				"tags": tags or ["affiliate", "review"],
				"isPublished": published,
			}
		}
		if self.publication_id:
			variables["input"]["publicationId"] = self.publication_id
		payload = {"query": query, "variables": variables}
		try:
			response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
			if response.status_code == 200:
				data = response.json()
				if data.get("data", {}).get("createStory", {}).get("success"):
					print(f"[Hashnode] Article published: {title}")
					return data
				else:
					print(f"[Hashnode] API error: {data}")
					return None
			else:
				print(f"[Hashnode] API error: {response.status_code}")
				print(response.text)
				return None
		except Exception as e:
			print("[Hashnode] API exception:", e)
			return None


class BloggerAPIClient:
	def __init__(self):
		self.blog_id = os.getenv("BLOGGER_BLOG_ID")
		self.client_id = os.getenv("GOOGLE_CLIENT_ID")
		self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
		self.token = os.getenv("GOOGLE_OAUTH_TOKEN")  # Πρέπει να έχεις πάρει access token
		self.refresh_token = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN")
		self.api_service_name = "blogger"
		self.api_version = "v3"
		self.creds = Credentials(
			token=self.token,
			refresh_token=self.refresh_token,
			client_id=self.client_id,
			client_secret=self.client_secret,
			token_uri="https://oauth2.googleapis.com/token"
		)
		self.service = build(self.api_service_name, self.api_version, credentials=self.creds)

	def publish_post(self, title, content, labels=None, published=True):
		body = {
			"title": title,
			"content": content,
		}
		if labels:
			body["labels"] = labels
		try:
			post = self.service.posts().insert(
				blogId=self.blog_id,
				isDraft=not published,
				body=body
			).execute()
			print(f"[Blogger] Post published: {title}")
			return post
		except Exception as e:
			print("[Blogger] API exception:", e)
			return None


class LinkedInAPIClient:
	def __init__(self):
		self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
		self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
		self.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")
		self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")  # Πρέπει να έχεις πάρει access token
		self.base_url = "https://api.linkedin.com/v2/ugcPosts"
		self.author_urn = os.getenv("LINKEDIN_AUTHOR_URN")  # π.χ. "urn:li:person:xxxx"

	def publish_post(self, text, url=None):
		headers = {
			"Authorization": f"Bearer {self.access_token}",
			"Content-Type": "application/json",
			"X-Restli-Protocol-Version": "2.0.0"
		}
		post_data = {
			"author": self.author_urn,
			"lifecycleState": "PUBLISHED",
			"specificContent": {
				"com.linkedin.ugc.ShareContent": {
					"shareCommentary": {"text": text},
					"shareMediaCategory": "NONE"
				}
			},
			"visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
		}
		if url:
			post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
			post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
				{"status": "READY", "originalUrl": url}
			]
		try:
			response = requests.post(self.base_url, headers=headers, json=post_data, timeout=10)
			if response.status_code in [201, 200]:
				print(f"[LinkedIn] Post published: {text[:50]}...")
				return response.json()
			else:
				print(f"[LinkedIn] API error: {response.status_code}")
				print(response.text)
				return None
		except Exception as e:
			print("[LinkedIn] API exception:", e)
			return None


class YouTubeAPIClient:
	def __init__(self):
		self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
		self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
		self.access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
		self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
		self.token_uri = "https://oauth2.googleapis.com/token"
		self.api_service_name = "youtube"
		self.api_version = "v3"
		self.creds = Credentials(
			token=self.access_token,
			refresh_token=self.refresh_token,
			client_id=self.client_id,
			client_secret=self.client_secret,
			token_uri=self.token_uri
		)
		self.service = build(self.api_service_name, self.api_version, credentials=self.creds)

	def upload_video(self, video_file, title, description, tags=None, privacy_status="public"):
		body = {
			"snippet": {
				"title": title,
				"description": description,
				"tags": tags or ["affiliate", "review"],
			},
			"status": {"privacyStatus": privacy_status}
		}
		media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
		try:
			request = self.service.videos().insert(
				part=",".join(body.keys()),
				body=body,
				media_body=media
			)
			response = None
			while response is None:
				status, response = request.next_chunk()
				if status:
					print(f"[YouTube] Upload progress: {int(status.progress() * 100)}%")
			print(f"[YouTube] Video uploaded: {title}")
			return response
		except Exception as e:
			print("[YouTube] API exception:", e)
			return None
