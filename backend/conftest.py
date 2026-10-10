import warnings

# Silenciar el warning de DRF en el momento más temprano posible
warnings.filterwarnings(
    "ignore",
    message="Converter 'drf_format_suffix' is already registered",
    category=DeprecationWarning,
    module="rest_framework.urlpatterns",
)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="rest_framework")
