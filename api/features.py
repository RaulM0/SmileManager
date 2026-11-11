from django.conf import settings
from rest_framework.exceptions import NotFound


class AIFeatureDisabled(NotFound):
    default_detail = 'La función de inteligencia artificial no está disponible.'
    default_code = 'ai_feature_disabled'


def ai_globally_enabled():
    return bool(getattr(settings, 'FEATURE_AI_ENABLED', False))


def ai_enabled_for_clinic(clinic):
    return ai_globally_enabled() and bool(clinic.ai_enabled)


def require_ai_enabled(clinic):
    if not ai_enabled_for_clinic(clinic):
        raise AIFeatureDisabled()


class TenantAIFeatureMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require_ai_enabled(self.membership.clinic)


class GlobalAIFeatureMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not ai_globally_enabled():
            raise AIFeatureDisabled()
