from functools import partial
from loguru import logger


class MockAffiliatePromoterSensor:
	"""
	MockAffiliatePromoterSensor simulates Twitter metrics for affiliate promotion.
	"""
	def __init__(self):
		pass

	def get_count_of_followers(self) -> int:
		logger.debug("MockAffiliatePromoterSensor.get_count_of_followers called")
		return 1000

	def get_count_of_likes(self) -> int:
		logger.debug("MockAffiliatePromoterSensor.get_count_of_likes called")
		return 4000

	def get_metric_fn(self, metric_name: str = "followers"):
		metrics = {
			"followers": partial(self.get_count_of_followers),
			"likes": partial(self.get_count_of_likes),
		}

		if metric_name not in metrics:
			raise ValueError(f"Unsupported metric: {metric_name}")

		return metrics[metric_name]
