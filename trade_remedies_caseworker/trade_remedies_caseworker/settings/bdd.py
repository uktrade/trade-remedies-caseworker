from .base import *
# API_TEST_BASE_URL=http://api:8007
# API_BASE_URL = os.environ.get("API_TEST_BASE_URL")
API_BASE_URL="http://test_api:8007"
DEBUG = False

INSTALLED_APPS += ("behave_django",)
