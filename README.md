# 🎭 Automated Story Engine

**Concept-to-Multi-Modal Narrative Workflow**

Transform your story ideas into rich, interactive narratives with AI-generated text, images, and audio. Create beautiful stories that flow seamlessly from scene to scene.

![Story Engine Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **🤖 AI-Powered Story Generation**: Create compelling narratives using OpenAI, Anthropic, and Google AI
- **🎨 Multi-Modal Output**: Generate images, audio narration, and interactive HTML viewers
- **🔄 Seamless Transitions**: Stories flow naturally from scene to scene
- **🎵 Emotional Audio**: Rich narration with emotional tone mapping
- **📱 Interactive Viewer**: Beautiful HTML interface for story consumption
- **🎬 Video Compilation**: Optional video creation with images and audio
- **⚡ Fast & Reliable**: Optimized prompts and fallback systems

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/automated-story-engine.git
cd automated-story-engine

# Install dependencies
pip install -r requirements_core.txt

# Set up API keys
python setup_env.py
```

### 2. Generate Your First Story

```bash
# Interactive story creator (recommended)
python interactive_story_creator.py

# Or use the main engine directly
python main.py
```

### 3. View Your Story

Your generated story will be saved in `generated_stories/[story_title]/` with:
- 📄 **JSON**: Complete story data
- 🌐 **HTML**: Interactive web viewer
- 🖼️ **Images**: Scene illustrations (if enabled)
- 🎵 **Audio**: Narration files (if enabled)
- 🎬 **Video**: Complete video story (if enabled)

## 📖 Example Output

See [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md) for a complete example of generated story content.

## 🎯 Usage Examples

### Interactive Story Creator
```bash
python interactive_story_creator.py
```
Guides you through creating custom stories with questions about characters, plot, and themes.

### Programmatic Usage
```python
import asyncio
from story_engine.core.models import StoryConcept
from main import StoryEngineApp

async def create_story():
    app = StoryEngineApp()
    
    concept = StoryConcept(
        characters={
            "hero": "A brave young explorer",
            "mentor": "A wise old wizard"
        },
        plot="The hero must find the lost crystal to save their village",
        moral="Courage and wisdom can overcome any obstacle",
        genre="fantasy",
        target_age="children"
    )
    
    result = await app.generate_complete_story(
        concept=concept,
        story_title="crystal_quest",
        output_formats=['json', 'html', 'images', 'audio']
    )
    
    if result['success']:
        print(f"Story created: {result['compilation_result']['story_directory']}")

asyncio.run(create_story())
```

## 🛠️ Configuration

### API Keys Required
- **OpenAI API Key**: For story generation and text-to-speech
- **Anthropic API Key**: For story generation (fallback)
- **Google AI API Key**: For story generation (fallback)

### Optional Features
- **Image Generation**: Requires OpenAI API for DALL-E
- **Video Compilation**: Requires `moviepy` package
- **Advanced Audio**: Requires additional TTS providers

## 📁 Project Structure

```
automated-story-engine/
├── story_engine/           # Core engine modules
│   ├── core/              # Story generation and orchestration
│   ├── generators/        # Image and audio generation
│   └── assemblers/        # Story compilation
├── generated_stories/     # Output directory
├── config.yaml           # Configuration file
├── main.py              # Main application
├── interactive_story_creator.py  # Interactive interface
└── requirements_core.txt # Dependencies
```

## 🎨 Story Types Supported

- **Fantasy**: Magic, dragons, enchanted worlds
- **Adventure**: Exploration, quests, discovery
- **Romance**: Love stories, relationships, emotions
- **Mystery**: Puzzles, clues, solving problems
- **Sci-Fi**: Technology, space, future
- **Educational**: Learning-focused content

## 🎭 Target Audiences

- **Children** (5-12 years): Simple language, clear morals
- **Teens** (13-17 years): More complex themes
- **Adults** (18+ years): Sophisticated storytelling

## 🔧 Troubleshooting

### Common Issues

**"Missing API keys"**
```bash
python setup_env.py
```

**"Import errors"**
```bash
pip install -r requirements_core.txt
```

**"Audio generation not working"**
- Check your OpenAI API key
- Ensure you have sufficient API credits

**"Video compilation failed"**
```bash
pip install moviepy
```

### Getting Help

1. Check the [Issues](https://github.com/yourusername/automated-story-engine/issues) page
2. Review the example output in [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)
3. Ensure all API keys are properly configured

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Format code
black story_engine/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and DALL-E image generation
- **Anthropic** for Claude models
- **Google** for Gemini models
- **MoviePy** for video processing
- **Rich** for beautiful terminal output

## 📊 Performance

- **Story Generation**: 30-60 seconds
- **Image Generation**: 10-20 seconds per scene
- **Audio Generation**: 5-10 seconds per scene
- **Video Compilation**: 1-2 minutes total

## 🔮 Roadmap

- [ ] Support for more languages
- [ ] Custom voice training
- [ ] Advanced video effects
- [ ] Story collaboration features
- [ ] Mobile app interface

---

**Made with ❤️ for storytellers everywhere**

*Transform your ideas into immersive narratives with the power of AI.*