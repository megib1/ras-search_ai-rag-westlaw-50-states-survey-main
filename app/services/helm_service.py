import os

from conversation_core.shared.utils.helm import Helm

helm_env = os.getenv("ENVIRONMENT", os.getenv("DD_ENV", "local"))
helm_service = Helm(release_name=f"ai-rag-westlaw-50-states-survey-{helm_env}", namespace=f"207891-ras-search-ai-{helm_env}")