#!/usr/bin/env python3
"""
Simple test for character consistency - generates images and JSON only.
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

from story_engine.core.models import StoryConcept
from main import StoryEngineApp


async def test_simple_character_consistency():
    """Test character consistency with simple output formats."""
    print("🎭 Testing Simple Character Consistency")
    print("=" * 50)
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found")
        return
    
    # Create a story concept with very specific character descriptions
    concept = StoryConcept(
        characters={
            "hero": "Luna, a young rabbit with pure white fur, wearing a bright blue dress with yellow flower patterns, has emerald green eyes and a pink nose, always carries a small red backpack",
            "friend": "Professor Hoot, a wise old owl with dark brown feathers, wearing round golden spectacles, has a gentle white face, wears a green vest with brown buttons, has kind amber eyes",
            "villain": "Shadow, a sly fox with dark orange fur, wearing a flowing black cape with silver trim, has sharp yellow eyes, has a mischievous grin, wears a red scarf"
        },
        plot="Luna the rabbit discovers a magical garden and must protect it from Shadow the fox with help from Professor Hoot the wise owl",
        moral="Friendship and courage can overcome any challenge",
        genre="fantasy",
        target_age="children"
    )
    
    print(f"📖 Story Concept:")
    print(f"   Hero: {concept.characters['hero']}")
    print(f"   Friend: {concept.characters['friend']}")
    print(f"   Villain: {concept.characters['villain']}")
    print()
    
    try:
        app = StoryEngineApp()
        
        # Generate story with images only (no audio to avoid compilation issues)
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Consistent Adventure",
            output_formats=['json', 'html', 'images']
        )
        
        if result['success']:
            print("✅ Character consistent story generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            
            # Show character tracking info
            if hasattr(app.image_generator, 'character_descriptions'):
                print(f"\n🎭 Character Descriptions Tracked:")
                for char_name, desc in app.image_generator.character_descriptions.items():
                    print(f"   {char_name}: {desc}")
            
            # Show generated scenes info
            if hasattr(app.image_generator, 'generated_scenes'):
                print(f"\n🖼️ Generated Scenes:")
                for scene_info in app.image_generator.generated_scenes:
                    print(f"   Scene {scene_info['scene_number']}: {scene_info['image_path']}")
            
            # Show story data
            if result.get('story'):
                story = result['story']
                print(f"\n📖 Story Summary: {story.get('story_summary', '')}")
                print(f"📖 Number of Scenes: {len(story.get('scenes', []))}")
                
                # Show visual descriptions for first few scenes
                for i, scene in enumerate(story.get('scenes', [])[:3]):
                    print(f"\n🎨 Scene {i+1} Visual Description:")
                    print(f"   {scene.get('visual_description', '')}")
            
        else:
            print(f"❌ Story generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple_character_consistency())
