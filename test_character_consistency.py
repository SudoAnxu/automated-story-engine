#!/usr/bin/env python3
"""
Test script for character consistency in story generation with images.
This script focuses on maintaining consistent character appearances across scenes.
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from story_engine.core.models import StoryConcept
from main import StoryEngineApp


async def test_character_consistency():
    """Test story generation with focus on character consistency."""
    print("🎭 Testing Character Consistency in Story Generation")
    print("=" * 60)
    
    # Check if image generation is available
    try:
        from story_engine.generators.image_generator import ImageGenerator
        print("✅ ImageGenerator is available")
    except ImportError as e:
        print(f"❌ ImageGenerator not available: {e}")
        return
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found - skipping character consistency test")
        return
    
    # Create a story concept with clear character descriptions
    concept = StoryConcept(
        characters={
            "hero": "Luna, a young rabbit with soft white fur, wearing a blue dress with yellow flowers, has bright green eyes and a pink nose",
            "friend": "Professor Hoot, a wise old owl with brown feathers, wearing round spectacles, has a gentle expression and wears a green vest",
            "villain": "Shadow, a sly fox with dark orange fur, wearing a black cape, has sharp yellow eyes and a mischievous grin"
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
    print(f"   Plot: {concept.plot}")
    print()
    
    try:
        app = StoryEngineApp()
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Character Consistent Adventure",
            output_formats=['json', 'html', 'images']
        )
        
        if result['success']:
            print("✅ Character consistent story generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            print(f"📄 Generated formats: {list(result['compilation_result']['outputs'].keys())}")
            
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
            
        else:
            print(f"❌ Character consistent story generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error in character consistency test: {e}")
        import traceback
        traceback.print_exc()


async def test_style_consistency():
    """Test style consistency across multiple stories."""
    print("\n🎨 Testing Style Consistency Across Stories")
    print("=" * 50)
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found - skipping style consistency test")
        return
    
    # Create two different story concepts to test style consistency
    concept1 = StoryConcept(
        characters={
            "hero": "Max, a brave young mouse with gray fur, wearing a red cape, has bright black eyes",
            "friend": "Sage, a wise old turtle with green shell, wearing a blue scarf, has kind brown eyes"
        },
        plot="Max the mouse and Sage the turtle go on an adventure to find a lost treasure",
        moral="Wisdom and bravery work best together",
        genre="adventure",
        target_age="children"
    )
    
    concept2 = StoryConcept(
        characters={
            "hero": "Zara, a curious young cat with orange fur, wearing a purple collar, has bright blue eyes",
            "friend": "Buddy, a friendly dog with brown fur, wearing a red bandana, has warm brown eyes"
        },
        plot="Zara the cat and Buddy the dog solve a mystery in their neighborhood",
        moral="Friendship makes every adventure better",
        genre="mystery",
        target_age="children"
    )
    
    try:
        app = StoryEngineApp()
        
        # Generate first story
        print("📖 Generating first story...")
        result1 = await app.generate_complete_story(
            concept=concept1,
            story_title="Max and Sage Adventure",
            output_formats=['json', 'images']
        )
        
        if result1['success']:
            print("✅ First story generated successfully")
            
            # Generate second story
            print("📖 Generating second story...")
            result2 = await app.generate_complete_story(
                concept=concept2,
                story_title="Zara and Buddy Mystery",
                output_formats=['json', 'images']
            )
            
            if result2['success']:
                print("✅ Second story generated successfully")
                print("\n🎨 Style Consistency Analysis:")
                print("   - Both stories should maintain consistent artistic style")
                print("   - Character designs should be cohesive within each story")
                print("   - Visual treatment should be consistent")
                
            else:
                print(f"❌ Second story generation failed: {result2.get('error')}")
        else:
            print(f"❌ First story generation failed: {result1.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error in style consistency test: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run character consistency tests."""
    print("🚀 Starting Character Consistency Tests")
    print("=" * 60)
    
    # Test character consistency
    await test_character_consistency()
    
    # Test style consistency
    await test_style_consistency()
    
    print("\n🏁 Character consistency tests completed!")
    print("\n📋 Summary:")
    print("   - Character descriptions should be extracted and maintained")
    print("   - Visual prompts should include character consistency")
    print("   - Generated images should show consistent character appearances")
    print("   - Artistic style should remain cohesive across scenes")


if __name__ == "__main__":
    asyncio.run(main())
