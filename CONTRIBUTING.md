# 🤝 Contributing to Automated Story Engine

Thank you for your interest in contributing to the Automated Story Engine! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- API keys for OpenAI, Anthropic, and/or Google AI

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/automated-story-engine.git
cd automated-story-engine

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config.example.yaml config.yaml
python setup_env.py
```

## 📋 How to Contribute

### 1. Bug Reports
- Use the GitHub issue tracker
- Include steps to reproduce
- Provide error messages and logs
- Specify your environment (OS, Python version, etc.)

### 2. Feature Requests
- Check existing issues first
- Describe the feature clearly
- Explain the use case and benefits
- Consider implementation complexity

### 3. Code Contributions
- Fork the repository
- Create a feature branch: `git checkout -b feature/amazing-feature`
- Make your changes
- Add tests if applicable
- Ensure all tests pass
- Submit a pull request

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_story_generation.py

# Run with coverage
python -m pytest --cov=story_engine tests/
```

### Test Structure
```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for workflows
├── fixtures/       # Test data and fixtures
└── conftest.py     # Pytest configuration
```

## 📝 Code Style

### Python Style Guide
- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

### Code Formatting
```bash
# Format code with black
black story_engine/

# Check code style
flake8 story_engine/

# Sort imports
isort story_engine/
```

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add support for custom voice synthesis
fix: resolve SSML parsing issues in audio generation
docs: update README with new installation steps
test: add unit tests for story validation
```

## 🏗️ Architecture

### Project Structure
```
story_engine/
├── core/              # Core story generation logic
│   ├── models.py      # Data models and validation
│   ├── orchestrator.py # LLM orchestration
│   └── prompt_builder.py # Prompt engineering
├── generators/        # Asset generation
│   ├── image_generator.py
│   └── audio_generator.py
└── assemblers/        # Story compilation
    └── story_compiler.py
```

### Key Components
- **Models**: Pydantic models for data validation
- **Orchestrator**: Manages LLM providers and fallbacks
- **Prompt Builder**: Constructs optimized prompts
- **Generators**: Create images and audio assets
- **Assembler**: Compiles final story outputs

## 🔒 Security Guidelines

### API Keys
- Never commit API keys to the repository
- Use environment variables for sensitive data
- Test with limited API quotas
- Rotate keys regularly

### Data Privacy
- Don't log sensitive user data
- Anonymize test data
- Follow GDPR/privacy best practices
- Secure file handling

## 📚 Documentation

### Code Documentation
- Write clear docstrings
- Include type hints
- Document complex algorithms
- Add inline comments for tricky logic

### User Documentation
- Update README.md for new features
- Add examples for new functionality
- Keep installation instructions current
- Document configuration options

## 🎯 Areas for Contribution

### High Priority
- [ ] Additional LLM provider support
- [ ] More image generation options
- [ ] Advanced audio features
- [ ] Mobile app interface
- [ ] Multi-language support

### Medium Priority
- [ ] Story collaboration features
- [ ] Advanced video effects
- [ ] Custom voice training
- [ ] Story analytics
- [ ] Export to other formats

### Low Priority
- [ ] Web interface
- [ ] Story templates
- [ ] Community features
- [ ] Advanced customization
- [ ] Performance optimizations

## 🐛 Common Issues

### Import Errors
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check Python version
python --version
```

### API Key Issues
```bash
# Verify environment variables
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# Test API connectivity
python -c "import openai; print('API key valid')"
```

### Memory Issues
- Reduce concurrent generations in config
- Use smaller models for testing
- Clear cache regularly
- Monitor memory usage

## 📞 Getting Help

### Community Support
- GitHub Discussions for questions
- GitHub Issues for bugs
- Discord server for real-time chat
- Stack Overflow with `automated-story-engine` tag

### Maintainer Contact
- Email: maintainer@example.com
- Twitter: @storyengine
- LinkedIn: /in/storyengine

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation
- Annual contributor awards

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to the Automated Story Engine! Together, we're building the future of AI-powered storytelling.** 🎭✨
