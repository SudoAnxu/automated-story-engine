"""Image generation module with multiple provider support."""

import os
import asyncio
import aiohttp
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from PIL import Image
import io

import openai
from dotenv import load_dotenv

from ..core.models import StoryScene, AssetGenerationStatus

load_dotenv()
logger = logging.getLogger(__name__)


class ImageProvider:
    """Base class for image generation providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def generate_image(self, prompt: str, scene_number: int) -> Dict[str, Any]:
        """Generate an image from a text prompt."""
        raise NotImplementedError


class OpenAIImageProvider(ImageProvider):
    """OpenAI DALL-E image generation provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def generate_image(self, prompt: str, scene_number: int) -> Dict[str, Any]:
        """Generate image using DALL-E."""
        try:
            # Enhance prompt for consistency
            enhanced_prompt = self._enhance_prompt_for_consistency(prompt, scene_number)
            
            response = await self.client.images.generate(
                model=self.config.get('model', 'dall-e-3'),
                prompt=enhanced_prompt,
                size=self.config.get('size', '1024x1024'),
                quality=self.config.get('quality', 'hd'),
                style=self.config.get('style', 'natural'),
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            return {
                'success': True,
                'image_url': image_url,
                'revised_prompt': revised_prompt,
                'provider': 'openai',
                'model': self.config.get('model', 'dall-e-3')
            }
            
        except Exception as e:
            logger.error(f"OpenAI image generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'openai'
            }
    
    def _enhance_prompt_for_consistency(self, prompt: str, scene_number: int) -> str:
        """Enhance prompt to maintain visual consistency across scenes."""
        # Add style consistency markers
        style_suffix = " --style consistent children's book illustration, same artistic style throughout"
        
        # Add scene context for continuity
        if scene_number > 1:
            continuity_prefix = f"Scene {scene_number} in the same visual style as previous scenes. "
            prompt = continuity_prefix + prompt
        
        return prompt + style_suffix


class StabilityImageProvider(ImageProvider):
    """Stability AI image generation provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv('STABILITY_API_KEY')
        self.base_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    async def generate_image(self, prompt: str, scene_number: int) -> Dict[str, Any]:
        """Generate image using Stability AI."""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Stability AI API key not found',
                'provider': 'stability'
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    }
                ],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
                "style_preset": "digital-art"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract base64 image data
                        image_data = data['artifacts'][0]['base64']
                        
                        return {
                            'success': True,
                            'image_data': image_data,
                            'provider': 'stability',
                            'model': 'stable-diffusion-xl'
                        }
                    else:
                        error_data = await response.text()
                        return {
                            'success': False,
                            'error': f"API error: {response.status} - {error_data}",
                            'provider': 'stability'
                        }
        
        except Exception as e:
            logger.error(f"Stability AI generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'stability'
            }


class ImageGenerator:
    """Main image generation orchestrator with multiple providers."""
    
    def __init__(self, config: Dict[str, Any], output_dir: str = "./generated_stories"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize providers
        self.providers = self._initialize_providers()
        
        # Generation statistics
        self.stats = {
            'total_generated': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'provider_usage': {}
        }
    
    def _initialize_providers(self) -> Dict[str, ImageProvider]:
        """Initialize image generation providers."""
        providers = {}
        
        image_config = self.config.get('image_generation', {})
        primary_provider = image_config.get('primary_provider', 'openai')
        
        # Initialize OpenAI provider
        if primary_provider == 'openai' or 'openai' in image_config.get('fallback_providers', []):
            providers['openai'] = OpenAIImageProvider(image_config)
        
        # Initialize Stability AI provider
        if primary_provider == 'stability' or 'stability' in image_config.get('fallback_providers', []):
            providers['stability'] = StabilityImageProvider(image_config)
        
        return providers
    
    async def generate_scene_image(self, scene: StoryScene, 
                                 story_title: str = "story") -> AssetGenerationStatus:
        """Generate an image for a single scene."""
        self.stats['total_generated'] += 1
        
        try:
            # Determine provider order
            primary_provider = self.config.get('image_generation', {}).get('primary_provider', 'openai')
            fallback_providers = self.config.get('image_generation', {}).get('fallback_providers', [])
            
            providers_to_try = [primary_provider] + [p for p in fallback_providers if p != primary_provider]
            
            # Attempt generation with fallback
            for provider_name in providers_to_try:
                if provider_name not in self.providers:
                    continue
                
                logger.info(f"Generating image for scene {scene.scene_number} using {provider_name}")
                
                provider = self.providers[provider_name]
                result = await provider.generate_image(scene.visual_description, scene.scene_number)
                
                if result['success']:
                    # Save the image
                    image_path = await self._save_image(
                        result, scene.scene_number, story_title
                    )
                    
                    if image_path:
                        self.stats['successful_generations'] += 1
                        self.stats['provider_usage'][provider_name] = \
                            self.stats['provider_usage'].get(provider_name, 0) + 1
                        
                        return AssetGenerationStatus(
                            scene_number=scene.scene_number,
                            image_generated=True,
                            image_path=str(image_path)
                        )
                
                logger.warning(f"Provider {provider_name} failed: {result.get('error', 'Unknown error')}")
            
            # All providers failed
            self.stats['failed_generations'] += 1
            return AssetGenerationStatus(
                scene_number=scene.scene_number,
                image_generated=False,
                error_message="All image generation providers failed"
            )
        
        except Exception as e:
            logger.error(f"Image generation error for scene {scene.scene_number}: {str(e)}")
            self.stats['failed_generations'] += 1
            return AssetGenerationStatus(
                scene_number=scene.scene_number,
                image_generated=False,
                error_message=str(e)
            )
    
    async def _save_image(self, result: Dict[str, Any], scene_number: int, 
                         story_title: str) -> Optional[Path]:
        """Save generated image to file."""
        try:
            story_dir = self.output_dir / story_title
            story_dir.mkdir(exist_ok=True)
            
            image_filename = f"scene_{scene_number:02d}.png"
            image_path = story_dir / image_filename
            
            if 'image_url' in result:
                # Download from URL (OpenAI)
                async with aiohttp.ClientSession() as session:
                    async with session.get(result['image_url']) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                            return image_path
            
            elif 'image_data' in result:
                # Save from base64 data (Stability AI)
                image_data = base64.b64decode(result['image_data'])
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                return image_path
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            return None
    
    async def generate_story_images(self, scenes: List[StoryScene], 
                                  story_title: str = "story",
                                  max_concurrent: int = 3) -> List[AssetGenerationStatus]:
        """Generate images for all scenes in a story."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(scene: StoryScene) -> AssetGenerationStatus:
            async with semaphore:
                return await self.generate_scene_image(scene, story_title)
        
        tasks = [generate_single(scene) for scene in scenes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AssetGenerationStatus(
                    scene_number=scenes[i].scene_number,
                    image_generated=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def optimize_image_consistency(self, scenes: List[StoryScene]) -> List[StoryScene]:
        """Optimize visual descriptions for consistency across scenes."""
        if not scenes:
            return scenes
        
        # Extract common visual elements from first scene
        first_scene = scenes[0]
        base_style = self._extract_style_elements(first_scene.visual_description)
        
        # Apply consistency enhancements to all scenes
        optimized_scenes = []
        for scene in scenes:
            optimized_description = self._apply_style_consistency(
                scene.visual_description, base_style, scene.scene_number
            )
            
            # Create new scene with optimized description
            optimized_scene = scene.copy()
            optimized_scene.visual_description = optimized_description
            optimized_scenes.append(optimized_scene)
        
        return optimized_scenes
    
    def _extract_style_elements(self, description: str) -> Dict[str, str]:
        """Extract style elements from a visual description."""
        # Simple keyword-based style extraction
        style_keywords = {
            'art_style': ['watercolor', 'digital art', 'oil painting', 'illustration'],
            'lighting': ['golden hour', 'soft light', 'dramatic lighting', 'moonlight'],
            'mood': ['whimsical', 'mysterious', 'bright', 'dark', 'cheerful'],
            'color_palette': ['warm colors', 'cool colors', 'pastel', 'vibrant']
        }
        
        extracted_style = {}
        description_lower = description.lower()
        
        for category, keywords in style_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    extracted_style[category] = keyword
                    break
        
        return extracted_style
    
    def _apply_style_consistency(self, description: str, base_style: Dict[str, str], 
                               scene_number: int) -> str:
        """Apply style consistency to a scene description."""
        # Add style consistency elements
        consistency_elements = []
        
        for category, style_element in base_style.items():
            if style_element not in description.lower():
                consistency_elements.append(style_element)
        
        if consistency_elements:
            consistency_suffix = f" Maintain consistent {', '.join(consistency_elements)} throughout."
            description += consistency_suffix
        
        return description
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get image generation statistics."""
        stats = self.stats.copy()
        if stats['total_generated'] > 0:
            stats['success_rate'] = stats['successful_generations'] / stats['total_generated']
        else:
            stats['success_rate'] = 0
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of image generation providers."""
        health_status = {}
        
        test_prompt = "A simple test image of a red apple on a white background"
        
        for provider_name, provider in self.providers.items():
            try:
                result = await provider.generate_image(test_prompt, 1)
                health_status[provider_name] = {
                    'status': 'healthy' if result['success'] else 'unhealthy',
                    'error': result.get('error', None)
                }
            except Exception as e:
                health_status[provider_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return health_status
