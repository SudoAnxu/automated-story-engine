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
from story_engine.core.models import StoryConcept
from story_engine.core.orchestrator import StoryOrchestrator


class StoryEngineApp:
    """Public version of the story engine application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.orchestrator = StoryOrchestrator(config_path)
        
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
        
        # Create output directory
        output_dir = Path('generated_stories') / story_title
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON output
        if 'json' in output_formats:
            json_path = output_dir / f"{story_title}_package.json"
            with open(json_path, 'w') as f:
                import json
                json.dump(story_result['story'], f, indent=2)
            logger.info(f"JSON saved: {json_path}")
        
        # Save HTML output (basic version)
        if 'html' in output_formats:
            html_path = output_dir / f"{story_title}_viewer.html"
            html_content = self._generate_basic_html(story_result['story'], story_title)
            with open(html_path, 'w') as f:
                f.write(html_content)
            logger.info(f"HTML saved: {html_path}")
        
        return {
            'success': True,
            'error': None,
            'story': story_result['story'],
            'output_directory': str(output_dir),
            'formats_generated': output_formats
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
        print(f"📁 Output directory: {result['output_directory']}")
        print(f"📄 Formats: {', '.join(result['formats_generated'])}")
    else:
        print(f"❌ Story generation failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
