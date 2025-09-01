#!/usr/bin/env python3
"""
Test script for story generation with images and audio.
This script helps debug the compilation_result error.
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


async def test_basic_story_generation():
    """Test basic story generation without images/audio."""
    print("🧪 Testing basic story generation...")
    
    # Create a simple story concept
    concept = StoryConcept(
        characters={
            "hero": "A brave young rabbit named Luna",
            "friend": "A wise old owl named Professor Hoot",
            "villain": "A grumpy fox named Shadow"
        },
        plot="Luna discovers a magical garden and must protect it from Shadow with help from Professor Hoot",
        moral="Friendship and courage can overcome any challenge",
        genre="fantasy",
        target_age="children"
    )
    
    try:
        app = StoryEngineApp()
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Magical Garden",
            output_formats=['json', 'html']
        )
        
        if result['success']:
            print("✅ Basic story generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            print(f"📄 Generated formats: {list(result['compilation_result']['outputs'].keys())}")
        else:
            print(f"❌ Basic story generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error in basic generation: {e}")
        import traceback
        traceback.print_exc()


async def test_story_with_images():
    """Test story generation with images."""
    print("\n🖼️ Testing story generation with images...")
    
    # Check if image generation is available
    try:
        from story_engine.generators.image_generator import ImageGenerator
        print("✅ ImageGenerator is available")
    except ImportError as e:
        print(f"❌ ImageGenerator not available: {e}")
        return
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found - skipping image generation test")
        return
    
    concept = StoryConcept(
        characters={
            "hero": "A brave young rabbit named Luna",
            "friend": "A wise old owl named Professor Hoot"
        },
        plot="Luna discovers a magical garden and learns about friendship",
        moral="Friendship makes everything better",
        genre="fantasy",
        target_age="children"
    )
    
    try:
        app = StoryEngineApp()
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Garden Adventure",
            output_formats=['json', 'html', 'images']
        )
        
        if result['success']:
            print("✅ Story with images generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            print(f"📄 Generated formats: {list(result['compilation_result']['outputs'].keys())}")
        else:
            print(f"❌ Story with images generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error in image generation: {e}")
        import traceback
        traceback.print_exc()


async def test_story_with_audio():
    """Test story generation with audio."""
    print("\n🎵 Testing story generation with audio...")
    
    # Check if audio generation is available
    try:
        from story_engine.generators.audio_generator import AudioGenerator
        print("✅ AudioGenerator is available")
    except ImportError as e:
        print(f"❌ AudioGenerator not available: {e}")
        return
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found - skipping audio generation test")
        return
    
    concept = StoryConcept(
        characters={
            "hero": "A brave young rabbit named Luna",
            "friend": "A wise old owl named Professor Hoot"
        },
        plot="Luna discovers a magical garden and learns about friendship",
        moral="Friendship makes everything better",
        genre="fantasy",
        target_age="children"
    )
    
    try:
        app = StoryEngineApp()
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Garden Adventure",
            output_formats=['json', 'html', 'audio']
        )
        
        if result['success']:
            print("✅ Story with audio generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            print(f"📄 Generated formats: {list(result['compilation_result']['outputs'].keys())}")
        else:
            print(f"❌ Story with audio generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error in audio generation: {e}")
        import traceback
        traceback.print_exc()


async def test_full_story_generation():
    """Test complete story generation with images and audio."""
    print("\n🎬 Testing complete story generation with images and audio...")
    
    # Check if all components are available
    try:
        from story_engine.generators.image_generator import ImageGenerator
        from story_engine.generators.audio_generator import AudioGenerator
        from story_engine.assemblers.story_compiler import StoryCompiler
        print("✅ All components are available")
    except ImportError as e:
        print(f"❌ Some components not available: {e}")
        return
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found - skipping full generation test")
        return
    
    concept = StoryConcept(
        characters={
            "hero": "A brave young rabbit named Luna",
            "friend": "A wise old owl named Professor Hoot"
        },
        plot="Luna discovers a magical garden and learns about friendship",
        moral="Friendship makes everything better",
        genre="fantasy",
        target_age="children"
    )
    
    try:
        app = StoryEngineApp()
        result = await app.generate_complete_story(
            concept=concept,
            story_title="Luna's Complete Adventure",
            output_formats=['json', 'html', 'images', 'audio', 'mp4']
        )
        
        if result['success']:
            print("✅ Complete story generation successful!")
            print(f"📁 Output directory: {result['compilation_result']['story_directory']}")
            print(f"📄 Generated formats: {list(result['compilation_result']['outputs'].keys())}")
            
            # Show detailed results
            outputs = result['compilation_result']['outputs']
            for format_type, output_info in outputs.items():
                if output_info.get('success'):
                    print(f"  ✅ {format_type.upper()}: {output_info.get('output_path', 'Generated')}")
                else:
                    print(f"  ❌ {format_type.upper()}: {output_info.get('error', 'Failed')}")
        else:
            print(f"❌ Complete story generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Unexpected error in complete generation: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("🚀 Starting Story Engine Tests")
    print("=" * 50)
    
    # Test basic generation first
    await test_basic_story_generation()
    
    # Test with images
    await test_story_with_images()
    
    # Test with audio
    await test_story_with_audio()
    
    # Test complete generation
    await test_full_story_generation()
    
    print("\n🏁 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
