"""Audio generation module with TTS and SSML support."""

import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import xml.etree.ElementTree as ET

try:
    from elevenlabs import AsyncElevenLabs
except ImportError:
    AsyncElevenLabs = None

import openai
from dotenv import load_dotenv

from ..core.models import StoryScene, EmotionalTone, AssetGenerationStatus

load_dotenv()
logger = logging.getLogger(__name__)


class SSMLBuilder:
    """Build SSML (Speech Synthesis Markup Language) from narration and tones."""
    
    # Tone to SSML parameter mapping
    TONE_MAPPINGS = {
        EmotionalTone.CALM: {"rate": "medium", "pitch": "medium", "volume": "medium"},
        EmotionalTone.CURIOUS: {"rate": "medium", "pitch": "+2st", "volume": "medium"},
        EmotionalTone.AWE: {"rate": "slow", "pitch": "+1st", "volume": "soft"},
        EmotionalTone.TENSE: {"rate": "fast", "pitch": "+3st", "volume": "loud"},
        EmotionalTone.DETERMINED: {"rate": "medium", "pitch": "medium", "volume": "loud"},
        EmotionalTone.SAD: {"rate": "slow", "pitch": "-2st", "volume": "soft"},
        EmotionalTone.EXCITED: {"rate": "fast", "pitch": "+4st", "volume": "loud"},
        EmotionalTone.ANGRY: {"rate": "fast", "pitch": "+2st", "volume": "loud"},
        EmotionalTone.MYSTERIOUS: {"rate": "slow", "pitch": "-1st", "volume": "soft"},
        EmotionalTone.JOYFUL: {"rate": "medium", "pitch": "+3st", "volume": "medium"},
        EmotionalTone.VULNERABLE: {"rate": "slow", "pitch": "-1st", "volume": "soft"},
        EmotionalTone.TENDER: {"rate": "slow", "pitch": "medium", "volume": "soft"},
        EmotionalTone.NOSTALGIC: {"rate": "slow", "pitch": "-1st", "volume": "medium"},
        EmotionalTone.HOPEFUL: {"rate": "medium", "pitch": "+1st", "volume": "medium"},
        EmotionalTone.MELANCHOLY: {"rate": "slow", "pitch": "-2st", "volume": "soft"},
        EmotionalTone.PASSIONATE: {"rate": "medium", "pitch": "+2st", "volume": "loud"}
    }
    
    @classmethod
    def build_ssml(cls, narration_text: str, narration_tones: Dict[str, EmotionalTone]) -> str:
        """Build SSML document from narration text and emotional tones."""
        
        # Start SSML document
        ssml_parts = ['<speak>']
        
        # Process each mapped text segment
        processed_chars = 0
        
        for text_segment, tone in narration_tones.items():
            # Find the segment in the full narration
            segment_start = narration_text.find(text_segment, processed_chars)
            
            if segment_start == -1:
                # Segment not found, add as-is
                continue
            
            # Add any text before this segment as neutral
            if segment_start > processed_chars:
                before_text = narration_text[processed_chars:segment_start]
                if before_text.strip():
                    ssml_parts.append(cls._escape_ssml_text(before_text))
            
            # Add the segment with emotional styling
            tone_params = cls.TONE_MAPPINGS.get(tone, cls.TONE_MAPPINGS[EmotionalTone.CALM])
            styled_segment = cls._apply_tone_styling(text_segment, tone_params)
            ssml_parts.append(styled_segment)
            
            # Update processed position
            processed_chars = segment_start + len(text_segment)
        
        # Add any remaining text
        if processed_chars < len(narration_text):
            remaining_text = narration_text[processed_chars:]
            if remaining_text.strip():
                ssml_parts.append(cls._escape_ssml_text(remaining_text))
        
        ssml_parts.append('</speak>')
        
        return ''.join(ssml_parts)
    
    @classmethod
    def _apply_tone_styling(cls, text: str, tone_params: Dict[str, str]) -> str:
        """Apply SSML styling based on tone parameters."""
        escaped_text = cls._escape_ssml_text(text)
        
        # Build prosody tag
        prosody_attrs = []
        for param, value in tone_params.items():
            prosody_attrs.append(f'{param}="{value}"')
        
        prosody_tag = ' '.join(prosody_attrs)
        
        # Add emphasis for certain tones
        if any(param in tone_params and 'loud' in str(value) for param, value in tone_params.items()):
            return f'<prosody {prosody_tag}><emphasis level="moderate">{escaped_text}</emphasis></prosody>'
        else:
            return f'<prosody {prosody_tag}>{escaped_text}</prosody>'
    
    @classmethod
    def _escape_ssml_text(cls, text: str) -> str:
        """Escape special characters for SSML."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    @classmethod
    def add_pauses_and_breaks(cls, ssml: str, scene_number: int) -> str:
        """Add natural pauses and breaks to SSML."""
        # Add scene transition pause at the beginning (except first scene)
        if scene_number > 1:
            ssml = ssml.replace('<speak>', '<speak><break time="1s"/>')
        
        # Add pauses after sentences
        ssml = ssml.replace('.', '.<break time="500ms"/>')
        ssml = ssml.replace('!', '!<break time="500ms"/>')
        ssml = ssml.replace('?', '?<break time="500ms"/>')
        
        # Add longer pauses after dialogue
        ssml = ssml.replace('"', '"<break time="750ms"/>')
        
        return ssml


class AudioProvider:
    """Base class for audio generation providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def generate_audio(self, ssml: str, scene_number: int) -> Dict[str, Any]:
        """Generate audio from SSML."""
        raise NotImplementedError


class OpenAITTSProvider(AudioProvider):
    """OpenAI Text-to-Speech provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def generate_audio(self, ssml: str, scene_number: int) -> Dict[str, Any]:
        """Generate audio using OpenAI TTS API."""
        try:
            # Convert SSML to plain text
            plain_text = self._ssml_to_text(ssml)
            
            # Debug logging
            logger.debug(f"Original SSML: {ssml[:200]}...")
            logger.debug(f"Converted text: {plain_text[:200]}...")
            
            # Ensure we have clean text
            if not plain_text or plain_text.strip() == "":
                logger.warning("Empty text after SSML conversion, using original")
                plain_text = ssml
            
            # Generate audio using OpenAI TTS
            response = await self.client.audio.speech.create(
                model=self.config.get('model', 'tts-1'),
                voice=self.config.get('voice', 'alloy'),
                input=plain_text,
                speed=self.config.get('speed', 1.0)
            )
            
            # Get audio data
            audio_data = response.content
            
            return {
                'success': True,
                'audio_data': audio_data,
                'provider': 'openai',
                'model': self.config.get('model', 'tts-1'),
                'voice': self.config.get('voice', 'alloy')
            }
            
        except Exception as e:
            logger.error(f"OpenAI TTS generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'openai'
            }
    
    def _ssml_to_text(self, ssml: str) -> str:
        """Convert SSML to plain text."""
        import re
        
        try:
            # First, try to parse as XML
            root = ET.fromstring(ssml)
            text_content = ''.join(root.itertext())
        except ET.ParseError as e:
            logger.warning(f"SSML parsing failed: {e}, using regex extraction")
            # Fallback: use regex to extract text between tags
            text_content = ssml
        
        # Clean up any remaining SSML artifacts
        # Remove all XML tags completely
        text_content = re.sub(r'<[^>]+>', '', text_content)
        
        # Remove any SSML-specific attributes that might leak through
        text_content = re.sub(r'\b(rate|pitch|volume|prosody|emphasis|break)\s*[=:]\s*["\']?[^"\'\s]+["\']?', '', text_content, flags=re.IGNORECASE)
        
        # Remove any remaining SSML instruction words
        ssml_words = ['rate', 'pitch', 'volume', 'high', 'low', 'medium', 'fast', 'slow', 'soft', 'loud', 'prosody', 'emphasis', 'break']
        for word in ssml_words:
            text_content = re.sub(rf'\b{word}\b', '', text_content, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and punctuation
        text_content = re.sub(r'\s+', ' ', text_content)
        text_content = re.sub(r'\s*,\s*', ', ', text_content)  # Fix comma spacing
        text_content = re.sub(r'\s*\.\s*', '. ', text_content)  # Fix period spacing
        text_content = re.sub(r'\s*!\s*', '! ', text_content)   # Fix exclamation spacing
        text_content = re.sub(r'\s*\?\s*', '? ', text_content)  # Fix question spacing
        
        # Final cleanup
        text_content = text_content.strip()
        
        # If we ended up with empty or very short text, return original
        if len(text_content) < 10:
            logger.warning("Text too short after SSML conversion, using original")
            return ssml
        
        return text_content


class ElevenLabsProvider(AudioProvider):
    """ElevenLabs TTS provider with advanced voice synthesis."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if api_key and AsyncElevenLabs:
            self.client = AsyncElevenLabs(api_key=api_key)
        else:
            self.client = None
            logger.warning("ElevenLabs API key not found or package not installed")
    
    async def generate_audio(self, ssml: str, scene_number: int) -> Dict[str, Any]:
        """Generate audio using ElevenLabs API."""
        if not self.client:
            return {
                'success': False,
                'error': 'ElevenLabs client not initialized',
                'provider': 'elevenlabs'
            }
        
        try:
            # Convert SSML to plain text for ElevenLabs (they don't support SSML directly)
            # We'll use voice settings to simulate emotional tones
            plain_text = self._ssml_to_text(ssml)
            
            # Generate voice settings based on content analysis
            voice_settings = self._analyze_and_adjust_voice_settings(plain_text)
            
            # Generate audio
            audio_generator = await self.client.generate(
                text=plain_text,
                voice=self.config.get('voice_id', '21m00Tcm4TlvDq8ikWAM'),
                model=self.config.get('model_id', 'eleven_multilingual_v2'),
                voice_settings={
                    "stability": voice_settings.get('stability', 0.75),
                    "similarity_boost": voice_settings.get('similarity_boost', 0.85),
                    "style": voice_settings.get('style', 0.5),
                    "use_speaker_boost": True
                }
            )
            
            # Collect audio data
            audio_data = b""
            async for chunk in audio_generator:
                audio_data += chunk
            
            return {
                'success': True,
                'audio_data': audio_data,
                'provider': 'elevenlabs',
                'voice_settings': voice_settings
            }
            
        except Exception as e:
            logger.error(f"ElevenLabs audio generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'elevenlabs'
            }
    
    def _ssml_to_text(self, ssml: str) -> str:
        """Convert SSML to plain text."""
        try:
            # Parse SSML and extract text content
            root = ET.fromstring(ssml)
            text_content = ''.join(root.itertext())
            
            # Clean up any remaining SSML artifacts
            import re
            # Remove any remaining XML tags
            text_content = re.sub(r'<[^>]+>', '', text_content)
            # Clean up extra whitespace
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return text_content
        except ET.ParseError as e:
            logger.warning(f"SSML parsing failed: {e}, using fallback text extraction")
            # Fallback: use regex to extract text between tags
            import re
            # Remove all XML tags
            text_content = re.sub(r'<[^>]+>', '', ssml)
            # Clean up extra whitespace
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            return text_content
        except Exception as e:
            logger.error(f"Unexpected error in SSML to text conversion: {e}")
            # Last resort: return the original SSML
            return ssml
    
    def _analyze_and_adjust_voice_settings(self, text: str) -> Dict[str, float]:
        """Analyze text and adjust voice settings accordingly."""
        text_lower = text.lower()
        
        # Default settings
        settings = {
            'stability': 0.75,
            'similarity_boost': 0.85,
            'style': 0.5
        }
        
        # Adjust based on content analysis
        if any(word in text_lower for word in ['exciting', 'amazing', 'wonderful']):
            settings['style'] = 0.8  # More expressive
            settings['stability'] = 0.6  # Less stable for excitement
        
        elif any(word in text_lower for word in ['sad', 'crying', 'lonely']):
            settings['style'] = 0.3  # Less expressive
            settings['stability'] = 0.9  # More stable for sadness
        
        elif any(word in text_lower for word in ['scary', 'frightening', 'dark']):
            settings['style'] = 0.7  # Moderately expressive
            settings['stability'] = 0.8  # Controlled delivery
        
        return settings


class AzureTTSProvider(AudioProvider):
    """Azure Text-to-Speech provider with native SSML support."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv('AZURE_SPEECH_KEY')
        self.region = os.getenv('AZURE_SPEECH_REGION')
        self.voice_name = config.get('voice_name', 'en-US-AriaNeural')
    
    async def generate_audio(self, ssml: str, scene_number: int) -> Dict[str, Any]:
        """Generate audio using Azure TTS with SSML support."""
        if not self.api_key or not self.region:
            return {
                'success': False,
                'error': 'Azure Speech credentials not configured',
                'provider': 'azure'
            }
        
        try:
            # Prepare SSML with voice selection
            full_ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{self.voice_name}">
                    {ssml.replace('<speak>', '').replace('</speak>', '')}
                </voice>
            </speak>'''
            
            # Azure TTS API endpoint
            endpoint = f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, data=full_ssml.encode('utf-8')) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        return {
                            'success': True,
                            'audio_data': audio_data,
                            'provider': 'azure',
                            'voice_name': self.voice_name
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"Azure TTS error: {response.status} - {error_text}",
                            'provider': 'azure'
                        }
        
        except Exception as e:
            logger.error(f"Azure TTS generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'azure'
            }


class AudioGenerator:
    """Main audio generation orchestrator with SSML and multiple TTS providers."""
    
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
            'total_audio_duration': 0,
            'provider_usage': {}
        }
    
    def _initialize_providers(self) -> Dict[str, AudioProvider]:
        """Initialize audio generation providers."""
        providers = {}
        
        audio_config = self.config.get('audio_generation', {})
        primary_provider = audio_config.get('primary_provider', 'openai')
        
        # Initialize OpenAI TTS provider
        if primary_provider == 'openai' or 'openai' in audio_config.get('fallback_providers', []):
            providers['openai'] = OpenAITTSProvider(audio_config)
        
        # Initialize ElevenLabs provider (if available)
        if primary_provider == 'elevenlabs' or 'elevenlabs' in audio_config.get('fallback_providers', []):
            providers['elevenlabs'] = ElevenLabsProvider(audio_config)
        
        # Initialize Azure TTS provider
        if primary_provider == 'azure' or 'azure' in audio_config.get('fallback_providers', []):
            providers['azure'] = AzureTTSProvider(audio_config)
        
        return providers
    
    async def generate_scene_audio(self, scene: StoryScene, 
                                 story_title: str = "story") -> AssetGenerationStatus:
        """Generate audio for a single scene."""
        self.stats['total_generated'] += 1
        
        try:
            # Build SSML from narration and tones
            ssml = SSMLBuilder.build_ssml(scene.narration_text, scene.narration_tones)
            ssml = SSMLBuilder.add_pauses_and_breaks(ssml, scene.scene_number)
            
            # Determine provider order
            primary_provider = self.config.get('audio_generation', {}).get('primary_provider', 'openai')
            fallback_providers = self.config.get('audio_generation', {}).get('fallback_providers', [])
            
            providers_to_try = [primary_provider] + [p for p in fallback_providers if p != primary_provider]
            
            # Attempt generation with fallback
            for provider_name in providers_to_try:
                if provider_name not in self.providers:
                    continue
                
                logger.info(f"Generating audio for scene {scene.scene_number} using {provider_name}")
                
                provider = self.providers[provider_name]
                result = await provider.generate_audio(ssml, scene.scene_number)
                
                if result['success']:
                    # Save the audio
                    audio_path = await self._save_audio(
                        result, scene.scene_number, story_title
                    )
                    
                    if audio_path:
                        self.stats['successful_generations'] += 1
                        self.stats['provider_usage'][provider_name] = \
                            self.stats['provider_usage'].get(provider_name, 0) + 1
                        
                        return AssetGenerationStatus(
                            scene_number=scene.scene_number,
                            audio_generated=True,
                            audio_path=str(audio_path)
                        )
                
                logger.warning(f"Provider {provider_name} failed: {result.get('error', 'Unknown error')}")
            
            # All providers failed
            self.stats['failed_generations'] += 1
            return AssetGenerationStatus(
                scene_number=scene.scene_number,
                audio_generated=False,
                error_message="All audio generation providers failed"
            )
        
        except Exception as e:
            logger.error(f"Audio generation error for scene {scene.scene_number}: {str(e)}")
            self.stats['failed_generations'] += 1
            return AssetGenerationStatus(
                scene_number=scene.scene_number,
                audio_generated=False,
                error_message=str(e)
            )
    
    async def _save_audio(self, result: Dict[str, Any], scene_number: int, 
                         story_title: str) -> Optional[Path]:
        """Save generated audio to file."""
        try:
            story_dir = self.output_dir / story_title
            story_dir.mkdir(exist_ok=True)
            
            audio_filename = f"scene_{scene_number:02d}.mp3"
            audio_path = story_dir / audio_filename
            
            audio_data = result.get('audio_data')
            if audio_data:
                with open(audio_path, 'wb') as f:
                    f.write(audio_data)
                return audio_path
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            return None
    
    async def generate_story_audio(self, scenes: List[StoryScene], 
                                 story_title: str = "story",
                                 max_concurrent: int = 2) -> List[AssetGenerationStatus]:
        """Generate audio for all scenes in a story."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(scene: StoryScene) -> AssetGenerationStatus:
            async with semaphore:
                return await self.generate_scene_audio(scene, story_title)
        
        tasks = [generate_single(scene) for scene in scenes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AssetGenerationStatus(
                    scene_number=scenes[i].scene_number,
                    audio_generated=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def preview_ssml(self, scene: StoryScene) -> str:
        """Preview the SSML that would be generated for a scene."""
        ssml = SSMLBuilder.build_ssml(scene.narration_text, scene.narration_tones)
        return SSMLBuilder.add_pauses_and_breaks(ssml, scene.scene_number)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get audio generation statistics."""
        stats = self.stats.copy()
        if stats['total_generated'] > 0:
            stats['success_rate'] = stats['successful_generations'] / stats['total_generated']
        else:
            stats['success_rate'] = 0
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of audio generation providers."""
        health_status = {}
        
        test_ssml = "<speak>This is a test audio generation.</speak>"
        
        for provider_name, provider in self.providers.items():
            try:
                result = await provider.generate_audio(test_ssml, 1)
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
