#!/usr/bin/env python3
"""
Test for asset generation reporting and compilation status.
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


async def test_asset_reporting():
    """Test asset generation reporting and compilation status."""
    print("🎭 Testing Asset Generation Reporting")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found")
        return
    
    # Create a story concept
    concept = StoryConcept(
        characters={
            "hero": "Luna is a young white rabbit with soft white fur, wearing a bright blue dress with yellow flower patterns, has emerald green eyes and a pink nose",
            "friend": "Professor Hoot is a wise old brown owl with dark brown feathers, wearing round golden spectacles, has a gentle white face, wears a green vest with brown buttons",
            "villain": "Shadow is a sly orange fox with dark orange fur, wearing a flowing black cape with silver trim, has sharp yellow eyes, has a mischievous grin"
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
        
        # Test 1: Generate story with images only
        print("🖼️ Test 1: Generating story with images only...")
        result1 = await app.generate_complete_story(
            concept=concept,
            story_title="Asset Reporting Test - Images Only",
            output_formats=['json', 'html', 'images']
        )
        
        if result1['success']:
            print("✅ Images-only generation successful!")
            print(f"📁 Output directory: {result1['compilation_result']['story_directory']}")
            
            # Check asset status
            if 'asset_status' in result1:
                asset_status = result1['asset_status']
                print(f"📊 Asset Status:")
                print(f"   Images: {asset_status['images']['generated']}/{asset_status['images']['total']} generated")
                print(f"   Audio: {asset_status['audio']['generated']}/{asset_status['audio']['total']} generated")
            
            # Check compilation outputs
            outputs = result1['compilation_result']['outputs']
            print(f"📄 Compilation Outputs:")
            for format_type, output in outputs.items():
                status = "✅" if output.get('success') else "❌"
                print(f"   {status} {format_type.upper()}: {output.get('success', False)}")
                if not output.get('success'):
                    print(f"      Error: {output.get('error', 'Unknown error')}")
        else:
            print(f"❌ Images-only generation failed: {result1.get('error')}")
        
        print("\n" + "="*60 + "\n")
        
        # Test 2: Generate story with JSON and HTML only (no assets)
        print("📄 Test 2: Generating story with JSON and HTML only...")
        result2 = await app.generate_complete_story(
            concept=concept,
            story_title="Asset Reporting Test - JSON HTML Only",
            output_formats=['json', 'html']
        )
        
        if result2['success']:
            print("✅ JSON/HTML generation successful!")
            print(f"📁 Output directory: {result2['compilation_result']['story_directory']}")
            
            # Check compilation outputs
            outputs = result2['compilation_result']['outputs']
            print(f"📄 Compilation Outputs:")
            for format_type, output in outputs.items():
                status = "✅" if output.get('success') else "❌"
                print(f"   {status} {format_type.upper()}: {output.get('success', False)}")
                if not output.get('success'):
                    print(f"      Error: {output.get('error', 'Unknown error')}")
        else:
            print(f"❌ JSON/HTML generation failed: {result2.get('error')}")
        
        print("\n" + "="*60 + "\n")
        
        # Test 3: Check generated files
        print("📁 Test 3: Checking generated files...")
        
        # Check images-only test files
        test1_dir = Path("generated_stories/Asset Reporting Test - Images Only")
        if test1_dir.exists():
            print(f"📁 Test 1 Directory: {test1_dir}")
            files = list(test1_dir.glob("*"))
            for file in files:
                if file.is_file():
                    size = file.stat().st_size
                    print(f"   📄 {file.name} ({size:,} bytes)")
        
        # Check JSON/HTML test files
        test2_dir = Path("generated_stories/Asset Reporting Test - JSON HTML Only")
        if test2_dir.exists():
            print(f"📁 Test 2 Directory: {test2_dir}")
            files = list(test2_dir.glob("*"))
            for file in files:
                if file.is_file():
                    size = file.stat().st_size
                    print(f"   📄 {file.name} ({size:,} bytes)")
        
        print("\n✅ Asset reporting test completed!")
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_asset_reporting())
