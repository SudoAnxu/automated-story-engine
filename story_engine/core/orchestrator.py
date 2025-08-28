"""Public version of orchestrator - sanitized for open source.

This version contains basic LLM orchestration without
proprietary delegation strategies or advanced techniques.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .models import StoryConcept, GeneratedStory
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class StoryOrchestrator:
    """Basic story orchestrator for public use."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.prompt_builder = PromptBuilder(config_path)
        self.providers = self._initialize_providers()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def _initialize_providers(self) -> Dict[str, Any]:
        """Initialize basic LLM providers."""
        providers = {}
        
        # OpenAI Provider
        try:
            import openai
            providers['openai'] = {
                'client': openai.AsyncOpenAI(),
                'model': self.config.get('llm_models', {}).get('primary', {}).get('name', 'gpt-4o')
            }
        except ImportError:
            logger.warning("OpenAI not available")
        
        # Anthropic Provider
        try:
            import anthropic
            providers['anthropic'] = {
                'client': anthropic.AsyncAnthropic(),
                'model': self.config.get('llm_models', {}).get('secondary', {}).get('name', 'claude-3-5-sonnet-20241022')
            }
        except ImportError:
            logger.warning("Anthropic not available")
        
        return providers
    
    async def generate_story(self, concept: StoryConcept, 
                           complexity: str = "standard") -> Dict[str, Any]:
        """Generate a story using basic orchestration."""
        
        try:
            # Build prompt
            prompt = await self.prompt_builder.build_prompt(concept, complexity)
            
            # Try providers in order
            for provider_name, provider_config in self.providers.items():
                try:
                    response = await self._call_provider(provider_name, provider_config, prompt)
                    if response:
                        return self._process_response(response, concept)
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed: {e}")
                    continue
            
            return {
                'success': False,
                'error': 'All providers failed',
                'story': None
            }
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'story': None
            }
    
    async def _call_provider(self, provider_name: str, provider_config: Dict[str, Any], 
                           prompt: str) -> Optional[str]:
        """Call a specific LLM provider."""
        
        if provider_name == 'openai':
            return await self._call_openai(provider_config, prompt)
        elif provider_name == 'anthropic':
            return await self._call_anthropic(provider_config, prompt)
        
        return None
    
    async def _call_openai(self, config: Dict[str, Any], prompt: str) -> Optional[str]:
        """Call OpenAI API."""
        try:
            response = await config['client'].chat.completions.create(
                model=config['model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None
    
    async def _call_anthropic(self, config: Dict[str, Any], prompt: str) -> Optional[str]:
        """Call Anthropic API."""
        try:
            response = await config['client'].messages.create(
                model=config['model'],
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return None
    
    def _process_response(self, response: str, concept: StoryConcept) -> Dict[str, Any]:
        """Process LLM response and validate."""
        try:
            # Basic JSON extraction
            json_text = self._extract_json(response)
            story_data = json.loads(json_text)
            
            # Basic validation
            if not self._validate_story_data(story_data):
                return {
                    'success': False,
                    'error': 'Invalid story data',
                    'story': None
                }
            
            return {
                'success': True,
                'error': None,
                'story': story_data
            }
            
        except Exception as e:
            logger.error(f"Response processing failed: {e}")
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}',
                'story': None
            }
    
    def _extract_json(self, text: str) -> str:
        """Basic JSON extraction from response."""
        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")
        
        return text[start:end]
    
    def _validate_story_data(self, data: Dict[str, Any]) -> bool:
        """Basic validation of story data."""
        required_fields = ['story_summary', 'scenes']
        
        for field in required_fields:
            if field not in data:
                return False
        
        if not isinstance(data['scenes'], list) or len(data['scenes']) == 0:
            return False
        
        return True
