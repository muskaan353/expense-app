from django.urls import path

from apps.ai_assistant.views import AssistantQueryView


urlpatterns = [
    path(
        "ai-assistant/query/",
        AssistantQueryView.as_view(),
        name="assistant-query",
    )
]
