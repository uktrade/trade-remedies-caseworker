from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from v2_api_client.mixins import APIClientMixin

from core.base import GroupRequiredMixin
from core.constants import SECURITY_GROUP_TRA_ADMINISTRATOR, SECURITY_GROUP_TRA_INVESTIGATOR


class BaseCaseWorkerView(LoginRequiredMixin, GroupRequiredMixin, APIClientMixin):
    groups_required = [SECURITY_GROUP_TRA_INVESTIGATOR, SECURITY_GROUP_TRA_ADMINISTRATOR]


class BaseCaseWorkerTemplateView(BaseCaseWorkerView, TemplateView):
    pass
