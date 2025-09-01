#!/usr/bin/env python3
"""
Automated Story Engine - Public Version

This is a sanitized version of the main application for public use.
It demonstrates the core functionality without proprietary techniques.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/story_engine.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import public versions
from story_engine.core.models import StoryConcept, GeneratedStory, AssetGenerationStatus, StoryScene
from story_engine.core.orchestrator import StoryOrchestrator

# Import optional components
try:
    from story_engine.generators.image_generator import ImageGenerator
    from story_engine.generators.audio_generator import AudioGenerator
    from story_engine.assemblers.story_compiler import StoryCompiler
    FULL_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some features not available: {e}")
    ImageGenerator = AudioGenerator = StoryCompiler = None
    FULL_FEATURES_AVAILABLE = False


class StoryEngineApp:
    """Public version of the story engine application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.orchestrator = StoryOrchestrator(config_path)
        
        # Initialize optional components
        self.image_generator = None
        self.audio_generator = None
        self.story_compiler = None
        
        if FULL_FEATURES_AVAILABLE:
            try:
                config = self._load_config(config_path)
                self.image_generator = ImageGenerator(config)
                self.audio_generator = AudioGenerator(config)
                self.story_compiler = StoryCompiler(config)
                logger.info("Full story engine features initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize full features: {e}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
        
    async def generate_story(self, concept: StoryConcept, 
                           complexity: str = "standard") -> Dict[str, Any]:
        """Generate a story using the public engine."""
        
        logger.info(f"Generating story: {concept.genre or 'Untitled'}")
        
        try:
            result = await self.orchestrator.generate_story(concept, complexity)
            
            if result['success']:
                logger.info("Story generated successfully")
                return result
            else:
                logger.error(f"Story generation failed: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e),
                'story': None
            }
    
    async def generate_complete_story(self, concept: StoryConcept,
                                    story_title: str,
                                    output_formats: List[str] = ['json']) -> Dict[str, Any]:
        """Generate a complete story with specified output formats."""
        
        logger.info(f"Generating complete story: {story_title}")
        
        # Generate story structure
        story_result = await self.generate_story(concept)
        
        if not story_result['success']:
            return story_result
        
        story = story_result['story']
        
        # Initialize asset generation statuses
        image_statuses = []
        audio_statuses = []
        
        # Generate images if requested
        if 'images' in output_formats and self.image_generator:
            logger.info("Generating images...")
            image_statuses = await self._generate_images(story, story_title)
        
        # Generate audio if requested
        if 'audio' in output_formats and self.audio_generator:
            logger.info("Generating audio...")
            audio_statuses = await self._generate_audio(story, story_title)
        
        # Compile final outputs
        if self.story_compiler and ('images' in output_formats or 'audio' in output_formats):
            logger.info("Compiling story with assets...")
            
            # Convert story dictionary to GeneratedStory object
            try:
                # Normalize all scenes first
                normalized_scenes = []
                for scene_data in story.get('scenes', []):
                    normalized_scene_data = self._normalize_emotional_tones(scene_data.copy())
                    normalized_scenes.append(StoryScene(**normalized_scene_data))
                
                generated_story = GeneratedStory(
                    story_summary=story.get('story_summary', ''),
                    scenes=normalized_scenes
                )
                
                # Filter out asset generation formats for compilation
                compilation_formats = [fmt for fmt in output_formats if fmt not in ['images', 'audio']]
                
                compilation_result = await self.story_compiler.compile_story(
                    story=generated_story,
                    image_statuses=image_statuses,
                    audio_statuses=audio_statuses,
                    story_title=story_title,
                    output_formats=compilation_formats
                )
            except Exception as e:
                logger.error(f"Failed to compile story: {e}")
                compilation_result = {
                    'success': False,
                    'error': str(e),
                    'outputs': {}
                }
            
            # Add asset generation info to the result
            result = {
                'success': compilation_result['success'],
                'error': compilation_result.get('error'),
                'story': story,
                'compilation_result': compilation_result
            }
            
            # Add asset generation status if available
            if 'asset_status' in compilation_result:
                result['asset_status'] = compilation_result['asset_status']
            
            return result
        else:
            # Fallback to basic output generation
            return await self._generate_basic_outputs(story, story_title, output_formats)
    
    def _normalize_emotional_tones(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize emotional tones to match the EmotionalTone enum values."""
        if 'narration_tones' not in scene_data:
            return scene_data
        
        # Mapping of common emotional words to enum values
        tone_mapping = {
            'curiosity': 'curious',
            'wonder': 'awe',
            'anticipation': 'excited',
            'serenity': 'calm',
            'warmth': 'tender',
            'gentleness': 'tender',
            'enlightening': 'hopeful',
            'joy': 'joyful',
            'encouragement': 'hopeful',
            'enthusiasm': 'excited',
            'delight': 'joyful',
            'happiness': 'joyful',
            'contentment': 'calm',
            'satisfaction': 'calm',
            'reflection': 'nostalgic',
            'pride': 'determined',
            'amazed': 'awe',
            'enchanted': 'mysterious',
            'welcoming': 'tender',
            'grateful': 'tender',
            'content': 'calm',
            'enlightened': 'hopeful',
            'reflective': 'nostalgic',
            'fulfilled': 'joyful',
            'intrigued': 'curious',
            'trusting': 'tender',
            'enthusiastic': 'excited',
            'reassuring': 'calm',
            'peaceful': 'calm',
            'enchanting': 'mysterious'
        }
        
        normalized_tones = {}
        for text_segment, tone in scene_data['narration_tones'].items():
            # Convert to lowercase and map to valid enum value
            normalized_tone = tone_mapping.get(tone.lower(), 'calm')  # Default to 'calm' if not found
            normalized_tones[text_segment] = normalized_tone
        
        scene_data['narration_tones'] = normalized_tones
        return scene_data
    
    def _extract_story_characters(self, story: Dict[str, Any]) -> Dict[str, str]:
        """Extract character information from story data."""
        characters = {}
        
        # Look for character information in story summary and scenes
        story_text = story.get('story_summary', '')
        
        # Add character info from scenes
        for scene in story.get('scenes', []):
            story_text += f" {scene.get('visual_description', '')} {scene.get('narration_text', '')}"
        
        # Enhanced character patterns for better extraction
        import re
        character_patterns = [
            r'(\w+)\s+(?:the|is a|was a)\s+([^,\.]+)',
            r'(\w+)\s+(?:named|called)\s+([^,\.]+)',
            r'(\w+)\s+(?:with|wearing|having)\s+([^,\.]+)',
            r'(\w+)\s+(?:who|that)\s+([^,\.]+)',
            r'(\w+)\s+(?:has|had)\s+([^,\.]+)',
            r'(\w+)\s+(?:in|with)\s+([^,\.]+)',
            r'(\w+)\s+(?:wears|wearing)\s+([^,\.]+)',
            r'(\w+)\s+(?:with|has)\s+([^,\.]+)',
        ]
        
        for pattern in character_patterns:
            matches = re.findall(pattern, story_text, re.IGNORECASE)
            for match in matches:
                character_name = match[0].strip()
                description = match[1].strip()
                if character_name and description and len(character_name) > 2:
                    # Clean up the description
                    description = re.sub(r'\s+', ' ', description).strip()
                    characters[character_name] = description
        
        return characters
    
    async def _generate_images(self, story: Dict[str, Any], story_title: str) -> List[AssetGenerationStatus]:
        """Generate images for story scenes with character consistency."""
        if not self.image_generator:
            return []
        
        # Extract character information from the story
        story_characters = self._extract_story_characters(story)
        
        # Initialize character descriptions in image generator
        if hasattr(self.image_generator, 'character_descriptions'):
            self.image_generator.character_descriptions.update(story_characters)
        
        image_statuses = []
        for scene_data in story.get('scenes', []):
            try:
                # Normalize emotional tones first
                normalized_scene_data = self._normalize_emotional_tones(scene_data.copy())
                
                # Convert dictionary to StoryScene object
                scene = StoryScene(**normalized_scene_data)
                status = await self.image_generator.generate_scene_image(
                    scene=scene,
                    story_title=story_title
                )
                image_statuses.append(status)
            except Exception as e:
                logger.error(f"Failed to generate image for scene {scene_data.get('scene_number', 'unknown')}: {e}")
                image_statuses.append(AssetGenerationStatus(
                    scene_number=scene_data.get('scene_number', 0),
                    image_generated=False,
                    image_path=None,
                    error_message=str(e)
                ))
        
        return image_statuses
    
    async def _generate_audio(self, story: Dict[str, Any], story_title: str) -> List[AssetGenerationStatus]:
        """Generate audio for story scenes."""
        if not self.audio_generator:
            return []
        
        audio_statuses = []
        for scene_data in story.get('scenes', []):
            try:
                # Normalize emotional tones first
                normalized_scene_data = self._normalize_emotional_tones(scene_data.copy())
                
                # Convert dictionary to StoryScene object
                scene = StoryScene(**normalized_scene_data)
                status = await self.audio_generator.generate_scene_audio(
                    scene=scene,
                    story_title=story_title
                )
                audio_statuses.append(status)
            except Exception as e:
                logger.error(f"Failed to generate audio for scene {scene_data.get('scene_number', 'unknown')}: {e}")
                audio_statuses.append(AssetGenerationStatus(
                    scene_number=scene_data.get('scene_number', 0),
                    audio_generated=False,
                    audio_path=None,
                    error_message=str(e)
                ))
        
        return audio_statuses
    
    async def _generate_basic_outputs(self, story: Dict[str, Any], story_title: str, 
                                    output_formats: List[str]) -> Dict[str, Any]:
        """Generate basic outputs when full compilation is not available."""
        
        # Create output directory
        output_dir = Path('generated_stories') / story_title
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs = {}
        
        # Save JSON output
        if 'json' in output_formats:
            json_path = output_dir / f"{story_title}_package.json"
            with open(json_path, 'w') as f:
                import json
                json.dump(story, f, indent=2)
            outputs['json'] = {
                'success': True,
                'output_path': str(json_path)
            }
            logger.info(f"JSON saved: {json_path}")
        
        # Save HTML output (basic version)
        if 'html' in output_formats:
            html_path = output_dir / f"{story_title}_viewer.html"
            html_content = self._generate_basic_html(story, story_title)
            with open(html_path, 'w') as f:
                f.write(html_content)
            outputs['html'] = {
                'success': True,
                'output_path': str(html_path)
            }
            logger.info(f"HTML saved: {html_path}")
        
        return {
            'success': True,
            'error': None,
            'story': story,
            'compilation_result': {
                'success': True,
                'outputs': outputs,
                'story_directory': str(output_dir)
            }
        }
    
    def _generate_basic_html(self, story_data: Dict[str, Any], title: str) -> str:
        """Generate basic HTML viewer for the story."""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            text-align: center;
            color: #4a5568;
            margin-bottom: 30px;
        }}
        .scene {{
            margin-bottom: 40px;
            padding: 20px;
            border-left: 4px solid #667eea;
            background: #f7fafc;
        }}
        .scene-number {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.2em;
        }}
        .plot-summary {{
            font-style: italic;
            color: #666;
            margin-bottom: 15px;
        }}
        .narration {{
            font-size: 1.1em;
            margin-bottom: 15px;
        }}
        .visual-description {{
            background: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            font-size: 0.9em;
            color: #4a5568;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="story-summary">
            <p><strong>Summary:</strong> {story_summary}</p>
        </div>
        
        {scenes_html}
    </div>
</body>
</html>
        """
        
        # Generate scenes HTML
        scenes_html = ""
        for scene in story_data.get('scenes', []):
            scenes_html += f"""
            <div class="scene">
                <div class="scene-number">Scene {scene.get('scene_number', '?')}</div>
                <div class="plot-summary">{scene.get('plot_summary', '')}</div>
                <div class="narration">{scene.get('narration_text', '')}</div>
                <div class="visual-description">
                    <strong>Visual:</strong> {scene.get('visual_description', '')}
                </div>
            </div>
            """
        
        return html_template.format(
            title=title,
            story_summary=story_data.get('story_summary', ''),
            scenes_html=scenes_html
        )


async def main():
    """Main function for testing the public engine."""
    
    # Create a sample story concept
    concept = StoryConcept(
        characters={
            "hero": "A curious young girl named Luna",
            "mentor": "A wise old gardener with magical powers"
        },
        plot="Luna discovers a hidden garden where plants can talk and help her solve a mystery that has puzzled the village for generations",
        moral="Friendship and curiosity can solve any problem",
        genre="fantasy",
        target_age="children"
    )
    
    # Initialize the engine
    app = StoryEngineApp()
    
    # Generate the story
    result = await app.generate_complete_story(
        concept=concept,
        story_title="magic_garden_demo",
        output_formats=['json', 'html']
    )
    
    if result['success']:
        print("✅ Story generated successfully!")
        print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
        print(f"📄 Formats: {', '.join(result['compilation_result']['outputs'].keys())}")
    else:
        print(f"❌ Story generation failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
