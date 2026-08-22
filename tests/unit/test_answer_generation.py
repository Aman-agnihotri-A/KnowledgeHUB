from types import SimpleNamespace

import pytest

from app.rag.answer_generation import (
    AnswerGenerationError,
    AnswerGenerationRequest,
    ConversationHistoryMessage,
    DeterministicAnswerGenerationProvider,
    GeminiAnswerGenerationProvider,
    OpenAIAnswerGenerationProvider,
    create_answer_generation_provider,
)


class FakeResponses:
    def __init__(
        self,
        *,
        output_text="Generated answer.",
    ):
        self.output_text = output_text
        self.model = None
        self.input = None

    def create(
        self,
        *,
        model,
        input,
    ):
        self.model = model
        self.input = input

        return SimpleNamespace(
            output_text=self.output_text,
        )


class FakeOpenAIClient:
    def __init__(
        self,
        *,
        output_text="Generated answer.",
    ):
        self.responses = FakeResponses(
            output_text=output_text,
        )

class FakeGeminiModels:
    def __init__(
        self,
        *,
        text="Generated Gemini answer.",
    ):
        self.text = text
        self.model = None
        self.contents = None

    def generate_content(
        self,
        *,
        model,
        contents,
    ):
        self.model = model
        self.contents = contents

        return SimpleNamespace(
            text=self.text,
        )


class FakeGeminiClient:
    def __init__(
        self,
        *,
        text="Generated Gemini answer.",
    ):
        self.models = FakeGeminiModels(
            text=text,
        )

def test_gemini_provider_generates_answer():
    client = FakeGeminiClient(
        text="KnowledgeHub uses FastAPI."
    )

    provider = GeminiAnswerGenerationProvider(
        api_key="test-key",
        model="gemini-3.6-flash",
        client=client,
    )

    result = provider.generate(
        AnswerGenerationRequest(
            question="What framework does it use?",
            context=(
                "[Source: handbook.pdf, chunk 0]\n"
                "KnowledgeHub uses FastAPI."
            ),
        )
    )

    assert result.answer == (
        "KnowledgeHub uses FastAPI."
    )

    assert client.models.model == (
        "gemini-3.6-flash"
    )

    assert (
        "What framework does it use?"
        in client.models.contents
    )

    assert (
        "KnowledgeHub uses FastAPI."
        in client.models.contents
    )

def test_gemini_provider_includes_conversation_history():
    client = FakeGeminiClient()

    provider = GeminiAnswerGenerationProvider(
        api_key="test-key",
        model="gemini-3.6-flash",
        client=client,
    )

    provider.generate(
        AnswerGenerationRequest(
            question="What framework does it use?",
            context="KnowledgeHub uses FastAPI.",
            conversation_history=[
                ConversationHistoryMessage(
                    role="user",
                    content="What is KnowledgeHub?",
                ),
                ConversationHistoryMessage(
                    role="assistant",
                    content=(
                        "It is a knowledge platform."
                    ),
                ),
            ],
        )
    )

    prompt = client.models.contents

    assert (
        "user: What is KnowledgeHub?"
        in prompt
    )

    assert (
        "assistant: It is a knowledge platform."
        in prompt
    )

    assert (
        "KnowledgeHub uses FastAPI."
        in prompt
    )

def test_gemini_provider_rejects_missing_api_key():
    with pytest.raises(
        ValueError,
        match="Gemini API key is required",
    ):
        GeminiAnswerGenerationProvider(
            api_key="   ",
            model="gemini-3.6-flash",
            client=FakeGeminiClient(),
        )


def test_gemini_provider_rejects_missing_model():
    with pytest.raises(
        ValueError,
        match="Gemini model is required",
    ):
        GeminiAnswerGenerationProvider(
            api_key="test-key",
            model="   ",
            client=FakeGeminiClient(),
        )

def test_gemini_provider_wraps_client_failure():
    class FailingGeminiModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            raise RuntimeError(
                "simulated Gemini failure"
            )

    class FailingGeminiClient:
        models = FailingGeminiModels()

    provider = GeminiAnswerGenerationProvider(
        api_key="test-key",
        model="gemini-3.6-flash",
        client=FailingGeminiClient(),
    )

    with pytest.raises(
        AnswerGenerationError,
        match="Gemini answer generation failed",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="Question",
                context="Some context",
            )
        )

def test_create_gemini_provider():
    provider = create_answer_generation_provider(
        provider_name="gemini",
        openai_api_key=None,
        openai_model="test-model",
        gemini_api_key="test-key",
        gemini_model="gemini-3.6-flash",
    )

    assert isinstance(
        provider,
        GeminiAnswerGenerationProvider,
    )

    assert provider.model_name == (
        "gemini-3.6-flash"
    )


def test_create_gemini_provider_requires_api_key():
    with pytest.raises(
        ValueError,
        match="Gemini API key is required",
    ):
        create_answer_generation_provider(
            provider_name="gemini",
            openai_api_key=None,
            openai_model="test-model",
            gemini_api_key=None,
            gemini_model="gemini-3.6-flash",
        )

def test_deterministic_provider_generates_grounded_answer():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    result = provider.generate(
        AnswerGenerationRequest(
            question="What is KnowledgeHub?",
            context=(
                "[Source: handbook.pdf, chunk 0]\n"
                "KnowledgeHub is a knowledge platform."
            ),
        )
    )

    assert result.answer == (
        "Based on the available knowledge base:\n\n"
        "[Source: handbook.pdf, chunk 0]\n"
        "KnowledgeHub is a knowledge platform."
    )


def test_deterministic_provider_rejects_empty_question():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="   ",
                context="Some context",
            )
        )


def test_deterministic_provider_rejects_empty_context():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    with pytest.raises(
        ValueError,
        match="Grounding context cannot be empty",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="KnowledgeHub?",
                context="   ",
            )
        )


def test_provider_model_name_is_stable():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    assert provider.model_name == (
        "deterministic-grounded-v1"
    )


def test_generation_request_supports_conversation_history():
    history = [
        ConversationHistoryMessage(
            role="user",
            content="What is KnowledgeHub?",
        ),
        ConversationHistoryMessage(
            role="assistant",
            content=(
                "KnowledgeHub is a knowledge platform."
            ),
        ),
    ]

    request = AnswerGenerationRequest(
        question="What framework does it use?",
        context=(
            "[Source: handbook.pdf, chunk 0]\n"
            "KnowledgeHub uses FastAPI."
        ),
        conversation_history=history,
    )

    assert request.conversation_history == history


def test_deterministic_provider_ignores_history_for_now():
    provider = (
        DeterministicAnswerGenerationProvider()
    )

    result = provider.generate(
        AnswerGenerationRequest(
            question="What framework does it use?",
            context=(
                "[Source: handbook.pdf, chunk 0]\n"
                "KnowledgeHub uses FastAPI."
            ),
            conversation_history=[
                ConversationHistoryMessage(
                    role="user",
                    content="What is KnowledgeHub?",
                ),
            ],
        )
    )

    assert result.answer == (
        "Based on the available knowledge base:\n\n"
        "[Source: handbook.pdf, chunk 0]\n"
        "KnowledgeHub uses FastAPI."
    )


def test_openai_provider_generates_answer():
    client = FakeOpenAIClient(
        output_text="KnowledgeHub uses FastAPI."
    )

    provider = OpenAIAnswerGenerationProvider(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    result = provider.generate(
        AnswerGenerationRequest(
            question="What framework does it use?",
            context=(
                "[Source: handbook.pdf, chunk 0]\n"
                "KnowledgeHub uses FastAPI."
            ),
        )
    )

    assert result.answer == (
        "KnowledgeHub uses FastAPI."
    )

    assert client.responses.model == (
        "test-model"
    )

    assert (
        "What framework does it use?"
        in client.responses.input
    )

    assert (
        "KnowledgeHub uses FastAPI."
        in client.responses.input
    )


def test_openai_provider_includes_conversation_history():
    client = FakeOpenAIClient()

    provider = OpenAIAnswerGenerationProvider(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    provider.generate(
        AnswerGenerationRequest(
            question="What framework does it use?",
            context="KnowledgeHub uses FastAPI.",
            conversation_history=[
                ConversationHistoryMessage(
                    role="user",
                    content="What is KnowledgeHub?",
                ),
                ConversationHistoryMessage(
                    role="assistant",
                    content=(
                        "It is a knowledge platform."
                    ),
                ),
            ],
        )
    )

    prompt = client.responses.input

    assert "user: What is KnowledgeHub?" in prompt
    assert (
        "assistant: It is a knowledge platform."
        in prompt
    )

    assert (
        "KnowledgeHub uses FastAPI."
        in prompt
    )


def test_openai_provider_rejects_missing_api_key():
    with pytest.raises(
        ValueError,
        match="OpenAI API key is required",
    ):
        OpenAIAnswerGenerationProvider(
            api_key="   ",
            model="test-model",
            client=FakeOpenAIClient(),
        )


def test_openai_provider_rejects_missing_model():
    with pytest.raises(
        ValueError,
        match="OpenAI model is required",
    ):
        OpenAIAnswerGenerationProvider(
            api_key="test-key",
            model="   ",
            client=FakeOpenAIClient(),
        )


def test_openai_provider_rejects_empty_question():
    provider = OpenAIAnswerGenerationProvider(
        api_key="test-key",
        model="test-model",
        client=FakeOpenAIClient(),
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="   ",
                context="Some context",
            )
        )


def test_openai_provider_rejects_empty_context():
    provider = OpenAIAnswerGenerationProvider(
        api_key="test-key",
        model="test-model",
        client=FakeOpenAIClient(),
    )

    with pytest.raises(
        ValueError,
        match="Grounding context cannot be empty",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="Question",
                context="   ",
            )
        )


def test_openai_provider_rejects_empty_model_response():
    client = FakeOpenAIClient(
        output_text="   ",
    )

    provider = OpenAIAnswerGenerationProvider(
        api_key="test-key",
        model="test-model",
        client=client,
    )

    with pytest.raises(
        AnswerGenerationError,
        match="empty answer",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="Question",
                context="Some context",
            )
        )


def test_openai_provider_wraps_client_failure():
    class FailingResponses:
        def create(
            self,
            *,
            model,
            input,
        ):
            raise RuntimeError(
                "simulated provider failure"
            )

    class FailingClient:
        responses = FailingResponses()

    provider = OpenAIAnswerGenerationProvider(
        api_key="test-key",
        model="test-model",
        client=FailingClient(),
    )

    with pytest.raises(
        AnswerGenerationError,
        match="OpenAI answer generation failed",
    ):
        provider.generate(
            AnswerGenerationRequest(
                question="Question",
                context="Some context",
            )
        )


def test_create_deterministic_provider():
    provider = create_answer_generation_provider(
        provider_name="deterministic",
        openai_api_key=None,
        openai_model="test-model",
    )

    assert isinstance(
        provider,
        DeterministicAnswerGenerationProvider,
    )


def test_create_openai_provider():
    provider = create_answer_generation_provider(
        provider_name="openai",
        openai_api_key="test-key",
        openai_model="test-model",
    )

    assert isinstance(
        provider,
        OpenAIAnswerGenerationProvider,
    )

    assert provider.model_name == "test-model"


def test_create_openai_provider_requires_api_key():
    with pytest.raises(
        ValueError,
        match="OpenAI API key is required",
    ):
        create_answer_generation_provider(
            provider_name="openai",
            openai_api_key=None,
            openai_model="test-model",
        )


def test_create_provider_rejects_unknown_provider():
    with pytest.raises(
        ValueError,
        match="Unsupported answer generation provider",
    ):
        create_answer_generation_provider(
            provider_name="unknown",
            openai_api_key=None,
            openai_model="test-model",
        )