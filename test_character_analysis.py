#!/usr/bin/env python3
"""
Test for analyzing character consistency in story data.
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


async def test_character_analysis():
    """Test character consistency analysis in story data."""
    print("🎭 Testing Character Consistency Analysis")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found")
        return
    
    # Create a story concept with explicit character descriptions
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
    
    print(f"📖 Story Concept:")
    print(f"   Hero: {concept.characters['hero']}")
    print(f"   Friend: {concept.characters['friend']}")
    print(f"   Villain: {concept.characters['villain']}")
    print()
    
    try:
        app = StoryEngineApp()
        
        # Generate story with JSON and HTML only (no images/audio to avoid compilation issues)
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Character Analysis",
            output_formats=['json', 'html']
        )
        
        if result['success']:
            print("✅ Story generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            
            # Analyze character consistency in the story data
            if result.get('story'):
                story = result['story']
                print(f"\n📖 Story Summary: {story.get('story_summary', '')}")
                print(f"📖 Number of Scenes: {len(story.get('scenes', []))}")
                
                # Analyze character consistency in visual descriptions
                print(f"\n🔍 Character Consistency Analysis:")
                character_mentions = {'Luna': [], 'Professor Hoot': [], 'Shadow': []}
                
                for i, scene in enumerate(story.get('scenes', [])):
                    visual_desc = scene.get('visual_description', '')
                    narration_text = scene.get('narration_text', '')
                    
                    print(f"\n🎨 Scene {i+1}:")
                    print(f"   Visual Description: {visual_desc}")
                    print(f"   Narration: {narration_text[:100]}...")
                    
                    # Check for character mentions in visual description
                    for char_name in character_mentions.keys():
                        if char_name.lower() in visual_desc.lower():
                            character_mentions[char_name].append(i+1)
                    
                    # Check for character consistency
                    characters_found = []
                    for char_name in character_mentions.keys():
                        if char_name.lower() in visual_desc.lower():
                            characters_found.append(char_name)
                    
                    if characters_found:
                        print(f"   ✅ Characters found: {', '.join(characters_found)}")
                    else:
                        print(f"   ❌ No specific characters mentioned!")
                
                # Summary of character consistency
                print(f"\n📊 Character Consistency Summary:")
                for char_name, scenes in character_mentions.items():
                    if scenes:
                        print(f"   {char_name}: Found in scenes {scenes}")
                    else:
                        print(f"   {char_name}: ❌ Not found in any visual descriptions!")
                
                # Check for character description consistency
                print(f"\n🎯 Character Description Analysis:")
                for char_name in character_mentions.keys():
                    char_lower = char_name.lower()
                    descriptions_found = []
                    
                    for scene in story.get('scenes', []):
                        visual_desc = scene.get('visual_description', '').lower()
                        if char_lower in visual_desc:
                            # Extract description around the character name
                            start = visual_desc.find(char_lower)
                            end = start + len(char_lower) + 100
                            context = visual_desc[start:end]
                            descriptions_found.append(context)
                    
                    if descriptions_found:
                        print(f"   {char_name}: Found in {len(descriptions_found)} scenes")
                        # Show first description as example
                        if descriptions_found:
                            print(f"      Example: {descriptions_found[0][:80]}...")
                    else:
                        print(f"   {char_name}: ❌ No descriptions found!")
            
        else:
            print(f"❌ Story generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_character_analysis())
