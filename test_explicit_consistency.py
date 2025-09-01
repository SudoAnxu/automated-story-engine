#!/usr/bin/env python3
"""
Test for explicit character consistency with very detailed character descriptions.
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


async def test_explicit_character_consistency():
    """Test character consistency with very explicit character descriptions."""
    print("🎭 Testing Explicit Character Consistency")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found")
        return
    
    # Create a story concept with VERY explicit character descriptions
    concept = StoryConcept(
        characters={
            "hero": "Luna is a young white rabbit with soft white fur, wearing a bright blue dress with yellow flower patterns, has emerald green eyes and a pink nose, always carries a small red backpack",
            "friend": "Professor Hoot is a wise old brown owl with dark brown feathers, wearing round golden spectacles, has a gentle white face, wears a green vest with brown buttons, has kind amber eyes",
            "villain": "Shadow is a sly orange fox with dark orange fur, wearing a flowing black cape with silver trim, has sharp yellow eyes, has a mischievous grin, wears a red scarf"
        },
        plot="Luna the white rabbit discovers a magical garden and must protect it from Shadow the orange fox with help from Professor Hoot the brown owl",
        moral="Friendship and courage can overcome any challenge",
        genre="fantasy",
        target_age="children"
    )
    
    print(f"📖 Story Concept with Explicit Characters:")
    print(f"   Hero: {concept.characters['hero']}")
    print(f"   Friend: {concept.characters['friend']}")
    print(f"   Villain: {concept.characters['villain']}")
    print(f"   Plot: {concept.plot}")
    print()
    
    try:
        app = StoryEngineApp()
        
        # Generate story with images only
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Explicit Character Adventure",
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
            
            # Show story data and analyze character consistency
            if result.get('story'):
                story = result['story']
                print(f"\n📖 Story Summary: {story.get('story_summary', '')}")
                print(f"📖 Number of Scenes: {len(story.get('scenes', []))}")
                
                # Analyze character consistency in visual descriptions
                print(f"\n🔍 Character Consistency Analysis:")
                for i, scene in enumerate(story.get('scenes', [])):
                    visual_desc = scene.get('visual_description', '')
                    print(f"\n🎨 Scene {i+1}:")
                    print(f"   Visual Description: {visual_desc}")
                    
                    # Check for character mentions
                    characters_found = []
                    for char_name in ['Luna', 'Professor Hoot', 'Shadow']:
                        if char_name.lower() in visual_desc.lower():
                            characters_found.append(char_name)
                    
                    if characters_found:
                        print(f"   ✅ Characters found: {', '.join(characters_found)}")
                    else:
                        print(f"   ❌ No specific characters mentioned!")
            
        else:
            print(f"❌ Story generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_explicit_character_consistency())
