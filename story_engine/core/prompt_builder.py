"""Public version of prompt builder - sanitized for open source.

This version contains basic prompt building functionality without
proprietary techniques or advanced delegation strategies.
"""

import json
import yaml
from typing import List, Dict, Optional, Any
from pathlib import Path
from jinja2 import Template
import random

from .models import StoryConcept, EmotionalTone


class PromptBuilder:
    """Basic prompt builder for public use."""
    
    def __init__(self, config_path: str = "config.yaml", examples_dir: str = "examples"):
        self.config = self._load_config(config_path)
        self.examples_dir = Path(examples_dir)
        self.example_stories = self._load_example_stories()
        self.master_template = Template(self._get_basic_template())
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def _load_example_stories(self) -> List[Dict[str, Any]]:
        """Load example stories for few-shot learning."""
        examples = []
        if self.examples_dir.exists():
            for example_file in self.examples_dir.glob("*.json"):
                try:
                    with open(example_file, 'r') as f:
                        example_data = json.load(f)
                        examples.append(example_data)
                except Exception as e:
                    print(f"Warning: Could not load example {example_file}: {e}")
        return examples
    
    def _get_basic_template(self) -> str:
        """Basic prompt template for public use."""
        return """
# Story Generation Request

## Story Concept
Title: {{ concept.title or "Untitled" }}
Genre: {{ concept.genre }}
Target Age: {{ concept.target_age }}

## Characters
{% for role, description in concept.characters.items() %}
- {{ role }}: {{ description }}
{% endfor %}

## Plot
{{ concept.plot }}

## Moral/Lesson
{{ concept.moral }}

## Requirements
Generate a story with {{ min_scenes }}-{{ max_scenes }} scenes.
Each scene should have:
- Rich narration (50-1200 characters)
- Comprehensive emotional tone mapping (must cover at least 70% of narration text)
- Detailed visual description for image generation with consistent character appearances
- Seamless transitions

## Visual Description Guidelines
For each scene's visual_description, include:
- Character appearances (maintain consistent clothing, features, colors)
- Setting details (location, lighting, atmosphere)
- Character positions and actions
- Color palette and mood
- Style: children's book illustration, warm and engaging

## Narration Tone Mapping Guidelines - CRITICAL
For narration_tones, you MUST map emotional tones to cover AT LEAST 70% of the narration text:

### Requirements:
- Break the narration text into 3-5 meaningful segments (sentences or phrases)
- Assign appropriate emotional tones to each segment
- Use these valid tones: {{ valid_tones|join(', ') }}
- Each segment should be 20-30% of the total narration text

### Example Format:
If narration_text is: "Luna approached the garden with wonder. Her heart filled with excitement as she saw the magical flowers. She felt safe knowing her friend was nearby."
Then narration_tones should be:
{
  "Luna approached the garden with wonder": "curious",
  "Her heart filled with excitement as she saw the magical flowers": "awe", 
  "She felt safe knowing her friend was nearby": "calm"
}

### IMPORTANT: Ensure the total length of tone-mapped text covers at least 70% of the narration_text!

## Output Format
Return valid JSON with this structure:
{
  "story_summary": "Brief story summary",
  "scenes": [
    {
      "scene_number": 1,
      "plot_summary": "What happens in this scene",
      "visual_description": "Detailed visual description including character appearances, setting, lighting, and style",
      "narration_text": "Scene narration text",
      "narration_tones": {
        "Luna approached the garden": "curious",
        "her heart filled with wonder": "awe",
        "she felt safe with her friend": "calm",
        "the magic surrounded them": "mysterious"
      }
    }
  ]
}

## Character Consistency - CRITICAL REQUIREMENT
You MUST maintain EXACT character consistency across all scenes:

### Character Details to Maintain:
{% for role, description in concept.characters.items() %}
**{{ role }}**: {{ description }}
- ALWAYS use this exact description in every scene
- NEVER change clothing, appearance, or physical features
- Keep the same name and personality throughout
{% endfor %}

### Visual Description Requirements:
- Every scene's visual_description MUST include the exact character appearances as defined above
- Use the specific character names (Luna, Professor Hoot, Shadow, etc.) in visual descriptions
- Include clothing, colors, and physical features exactly as specified
- Maintain consistent character positioning and interactions

Generate the story:
        """
    
    async def build_prompt(self, concept: StoryConcept, 
                          complexity: str = "standard") -> str:
        """Build a basic prompt with examples."""
        
        # Get random examples (basic approach)
        relevant_examples = self._get_random_examples()
        
        # Get scene parameters
        scene_params = self._get_scene_parameters(complexity)
        
        # Build the prompt
        prompt = self.master_template.render(
            concept=concept,
            examples=relevant_examples,
            min_scenes=scene_params['min_scenes'],
            max_scenes=scene_params['max_scenes'],
            valid_tones=[tone.value for tone in EmotionalTone]
        )
        
        return prompt
    
    def _get_random_examples(self) -> List[Dict[str, Any]]:
        """Get random examples (basic approach)."""
        if not self.example_stories:
            return []
        return random.sample(self.example_stories, 
                           min(2, len(self.example_stories)))
    
    def _get_scene_parameters(self, complexity: str) -> Dict[str, int]:
        """Get scene parameters based on complexity."""
        params = self.config.get('story_parameters', {})
        
        if complexity == "simple":
            return {
                'min_scenes': params.get('min_scenes', 4),
                'max_scenes': params.get('max_scenes', 8)
            }
        elif complexity == "complex":
            return {
                'min_scenes': params.get('min_scenes', 8),
                'max_scenes': params.get('max_scenes', 15)
            }
        else:  # standard
            return {
                'min_scenes': params.get('min_scenes', 6),
                'max_scenes': params.get('max_scenes', 12)
            }
