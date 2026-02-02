"""
LLM Service - Mistral API and Ollama integration with structured outputs
"""
import logging
import asyncio
from typing import Type, TypeVar, Optional, List
from pydantic import BaseModel
import tiktoken
import httpx
from mistralai import Mistral

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMService:
    """Service for LLM interactions with structured outputs"""

    def __init__(self):
        self.use_ollama = settings.use_ollama
        self.mistral_client = None if self.use_ollama else Mistral(api_key=settings.mistral_api_key)
        self.ollama_url = settings.ollama_url
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4/Mistral compatible

    async def call_with_structured_output(
        self,
        prompt: str,
        response_model: Type[T],
        model_name: str = "mistral-large-latest",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        images: Optional[List[bytes]] = None
    ) -> T:
        """
        Call LLM with structured output using Pydantic model.

        Args:
            prompt: The prompt text
            response_model: Pydantic model class for response validation
            model_name: Model to use
            temperature: Temperature setting
            max_tokens: Max tokens for completion
            images: Optional list of image bytes for vision models

        Returns:
            Validated instance of response_model
        """
        try:
            if self.use_ollama:
                return await self._call_ollama_structured(
                    prompt, response_model, model_name, temperature, max_tokens, images
                )
            else:
                return await self._call_mistral_structured(
                    prompt, response_model, model_name, temperature, max_tokens, images
                )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def _call_mistral_structured(
        self,
        prompt: str,
        response_model: Type[T],
        model_name: str,
        temperature: float,
        max_tokens: int,
        images: Optional[List[bytes]]
    ) -> T:
        """Call Mistral API with structured output and retry on validation errors"""
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Build messages
                if images:
                    # Vision model call
                    import base64
                    content = [{"type": "text", "text": prompt}]
                    for img_bytes in images:
                        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                        content.append({
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{img_b64}"
                        })
                    messages = [{"role": "user", "content": content}]
                else:
                    messages = [{"role": "user", "content": prompt}]

                # Call API with JSON mode (guarantees valid JSON)
                response = await asyncio.to_thread(
                    self.mistral_client.chat.complete,
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )

                # Parse and validate response against Pydantic schema
                response_text = response.choices[0].message.content
                validated_response = response_model.model_validate_json(response_text)

                # Success!
                logger.info(f"Mistral call successful on attempt {attempt + 1}: {response.usage.total_tokens} tokens")
                return validated_response

            except Exception as e:
                last_error = e
                response_preview = response_text[:500] if 'response_text' in locals() else 'N/A'
                logger.warning(
                    f"Mistral validation error on attempt {attempt + 1}/{max_retries}: {e}\n"
                    f"Response preview: {response_preview}\n"
                    f"Expected schema: {response_model.__name__}"
                )

                # If this was the last attempt, raise the error
                if attempt == max_retries - 1:
                    logger.error(f"Mistral API failed after {max_retries} attempts")
                    raise last_error

                # Wait before retry (exponential backoff)
                await asyncio.sleep(2 ** attempt)

        # Should never reach here, but just in case
        raise last_error or Exception("Mistral API call failed")

    async def _call_ollama_structured(
        self,
        prompt: str,
        response_model: Type[T],
        model_name: str,
        temperature: float,
        max_tokens: int,
        images: Optional[List[bytes]]
    ) -> T:
        """Call Ollama with structured output"""
        try:
            # Build request
            json_schema = response_model.model_json_schema()
            system_prompt = f"You must respond with valid JSON matching this schema: {json_schema}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            # Add images if provided
            if images:
                import base64
                images_b64 = [base64.b64encode(img).decode('utf-8') for img in images]
                messages[-1]["images"] = images_b64

            async with httpx.AsyncClient(timeout=settings.vision_api_timeout_seconds) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        },
                        "format": "json"
                    }
                )
                response.raise_for_status()
                data = response.json()

            # Parse and validate
            response_text = data["message"]["content"]
            validated_response = response_model.model_validate_json(response_text)

            logger.info(f"Ollama call successful")
            return validated_response

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            # Rough fallback estimate
            return len(text) // 4

    async def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated text
        """
        try:
            tokens = self.tokenizer.encode(text)
            if len(tokens) <= max_tokens:
                return text

            # Truncate and decode
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.tokenizer.decode(truncated_tokens)

            logger.warning(f"Truncated text from {len(tokens)} to {max_tokens} tokens")
            return truncated_text

        except Exception as e:
            logger.error(f"Truncation error: {e}")
            # Rough fallback
            approx_chars = max_tokens * 4
            return text[:approx_chars]

    async def chunk_text_by_tokens(self, text: str, max_tokens: int) -> List[str]:
        """
        Split text into chunks that fit within token limit.

        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk

        Returns:
            List of text chunks
        """
        try:
            tokens = self.tokenizer.encode(text)
            chunks = []

            for i in range(0, len(tokens), max_tokens):
                chunk_tokens = tokens[i:i + max_tokens]
                chunk_text = self.tokenizer.decode(chunk_tokens)
                chunks.append(chunk_text)

            logger.info(f"Split text into {len(chunks)} chunks of max {max_tokens} tokens")
            return chunks

        except Exception as e:
            logger.error(f"Chunking error: {e}")
            # Rough fallback
            approx_chars = max_tokens * 4
            chunks = []
            for i in range(0, len(text), approx_chars):
                chunks.append(text[i:i + approx_chars])
            return chunks

    async def call_vision_api(
        self,
        image_bytes: bytes,
        prompt: str,
        model_name: str = "mistral-large-latest"
    ) -> str:
        """
        Call vision API for image analysis.

        Args:
            image_bytes: Image as bytes
            prompt: Analysis prompt
            model_name: Model to use

        Returns:
            Analysis text
        """
        try:
            if self.use_ollama:
                return await self._call_ollama_vision(image_bytes, prompt, model_name)
            else:
                return await self._call_mistral_vision(image_bytes, prompt, model_name)
        except Exception as e:
            logger.error(f"Vision API call failed: {e}")
            raise

    async def _call_mistral_vision(self, image_bytes: bytes, prompt: str, model_name: str) -> str:
        """Call Mistral vision API"""
        try:
            import base64
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
                    ]
                }
            ]

            response = await asyncio.to_thread(
                self.mistral_client.chat.complete,
                model=model_name,
                messages=messages
            )

            result = response.choices[0].message.content
            logger.info(f"Mistral vision call successful: {response.usage.total_tokens} tokens")
            return result

        except Exception as e:
            logger.error(f"Mistral vision API error: {e}")
            raise

    async def _call_ollama_vision(self, image_bytes: bytes, prompt: str, model_name: str) -> str:
        """Call Ollama vision API"""
        try:
            import base64
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')

            async with httpx.AsyncClient(timeout=settings.vision_api_timeout_seconds) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                                "images": [img_b64]
                            }
                        ],
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()

            result = data["message"]["content"]
            logger.info(f"Ollama vision call successful")
            return result

        except Exception as e:
            logger.error(f"Ollama vision API error: {e}")
            raise


# Global instance
llm_service = LLMService()
