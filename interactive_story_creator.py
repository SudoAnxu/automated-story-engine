"""
Interactive Story Creator - Easy way to create custom stories with main.py
"""

import asyncio
import os
from pathlib import Path
from story_engine.core.models import StoryConcept

# Create logs directory before importing main
Path('logs').mkdir(exist_ok=True)

from main import StoryEngineApp

def get_user_input(prompt, default=None):
    """Get user input with optional default value."""
    if default:
        user_input = input(f"{prompt} (default: {default}): ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def create_story_concept():
    """Interactive story concept creation."""
    print("\n🎭 Let's Create Your Story!")
    print("=" * 50)
    
    # Basic story info
    story_title = get_user_input("Story title (for file names)")
    genre = get_user_input("Genre", "fantasy")
    target_age = get_user_input("Target age (children/teens/adults)", "children")
    
    print(f"\n📝 Now let's create your characters...")
    print("(You can add multiple characters, press Enter with empty name to finish)")
    
    characters = {}
    character_count = 0
    
    while True:
        character_count += 1
        role = get_user_input(f"Character {character_count} role (e.g., 'hero', 'villain', 'mentor')")
        if not role:
            break
            
        description = get_user_input(f"Describe {role}")
        if description:
            characters[role] = description
    
    if not characters:
        # Default characters if none provided
        characters = {
            "hero": "A brave young adventurer",
            "villain": "A mysterious antagonist"
        }
        print("Using default characters...")
    
    # Plot
    print(f"\n📖 Now let's create the plot...")
    plot = get_user_input("What happens in your story? (Beginning, middle, end)")
    
    # Moral
    moral = get_user_input("What lesson should readers learn?", "Friendship and courage are important")
    
    # Create the concept
    concept = StoryConcept(
        characters=characters,
        plot=plot,
        moral=moral,
        genre=genre,
        target_age=target_age
    )
    
    return concept, story_title

def choose_output_formats():
    """Let user choose which output formats to generate."""
    print(f"\n🎬 Choose output formats:")
    print("1. JSON only (fastest)")
    print("2. JSON + HTML (interactive viewer)")
    print("3. JSON + HTML + Images (if available)")
    print("4. JSON + HTML + Images + Audio (if available)")
    print("5. Everything including video (if moviepy available)")
    
    choice = get_user_input("Choose (1-5)", "2")
    
    format_map = {
        "1": ['json'],
        "2": ['json', 'html'],
        "3": ['json', 'html', 'images'],
        "4": ['json', 'html', 'images', 'audio'],
        "5": ['json', 'html', 'images', 'audio', 'mp4']
    }
    
    return format_map.get(choice, ['json', 'html'])

async def main():
    """Main interactive story creation flow."""
    
    print("🎭 Interactive Story Creator")
    print("Create custom stories with the Automated Story Engine!")
    print("=" * 60)
    
    # Check if we have API keys
    required_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    missing = [k for k in required_keys if not os.getenv(k)]
    
    if missing:
        print(f"❌ Missing API keys: {', '.join(missing)}")
        print("Run: python setup_env.py")
        return
    
    print("✅ API keys found!")
    
    try:
        # Create story concept
        concept, story_title = create_story_concept()
        
        # Choose output formats
        output_formats = choose_output_formats()
        
        # Show summary
        print(f"\n📋 Story Summary:")
        print(f"Title: {story_title}")
        print(f"Genre: {concept.genre}")
        print(f"Age: {concept.target_age}")
        print(f"Characters: {len(concept.characters)}")
        print(f"Output formats: {', '.join(output_formats)}")
        
        confirm = get_user_input("\nCreate this story? (y/n)", "y")
        if confirm.lower() not in ['y', 'yes']:
            print("Story creation cancelled.")
            return
        
        # Initialize the app
        print(f"\n🚀 Initializing Story Engine...")
        app = StoryEngineApp()
        
        # Generate the story
        print(f"\n✨ Generating your story...")
        result = await app.generate_complete_story(
            concept=concept,
            story_title=story_title,
            output_formats=output_formats
        )
        
        if result['success']:
            print(f"\n🎉 SUCCESS! Your story has been created!")
            print(f"📁 Story directory: {result['compilation_result']['story_directory']}")
            
            # Show what was created
            outputs = result['compilation_result']['outputs']
            print(f"\n📄 Generated files:")
            for format_type, output_info in outputs.items():
                if output_info.get('success'):
                    print(f"  ✅ {format_type.upper()}: {output_info['output_path']}")
                else:
                    print(f"  ❌ {format_type.upper()}: {output_info.get('error', 'Failed')}")
            
            # Show story preview
            story = result['story']
            print(f"\n📖 Story Preview:")
            print(f"Summary: {story.story_summary}")
            print(f"Scenes: {len(story.scenes)}")
            
            # Ask if they want to create another
            another = get_user_input("\nCreate another story? (y/n)", "n")
            if another.lower() in ['y', 'yes']:
                await main()  # Recursive call for another story
                
        else:
            print(f"\n❌ Story generation failed: {result.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Story creation interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("This might be a dependency or API issue.")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
