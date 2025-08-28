"""Data models for the story engine."""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class EmotionalTone(str, Enum):
    """Predefined emotional tones for audio generation."""
    CALM = "calm"
    CURIOUS = "curious" 
    AWE = "awe"
    TENSE = "tense"
    DETERMINED = "determined"
    SAD = "sad"
    EXCITED = "excited"
    ANGRY = "angry"
    MYSTERIOUS = "mysterious"
    JOYFUL = "joyful"
    VULNERABLE = "vulnerable"
    TENDER = "tender"
    NOSTALGIC = "nostalgic"
    HOPEFUL = "hopeful"
    MELANCHOLY = "melancholy"
    PASSIONATE = "passionate"


class StoryScene(BaseModel):
    """Model for a single story scene."""
    scene_number: int = Field(..., ge=1, description="Scene number in sequence")
    plot_summary: str = Field(..., min_length=10, max_length=300, 
                             description="Brief description of scene purpose")
    visual_description: str = Field(..., min_length=50, max_length=600,
                                   description="Detailed visual prompt for image generation")
    narration_text: str = Field(..., min_length=50, max_length=1200,
                               description="Full narration text for the scene with seamless transitions")
    narration_tones: Dict[str, EmotionalTone] = Field(...,
                                                     description="Mapping of text segments to emotional tones")
    transition_from_previous: Optional[str] = Field(None, max_length=200,
                                                   description="Seamless transition from previous scene")
    transition_to_next: Optional[str] = Field(None, max_length=200,
                                             description="Seamless transition to next scene")
    
    @validator('narration_tones')
    def validate_narration_mapping(cls, v, values):
        """Ensure all narration text is mapped to tones."""
        if 'narration_text' in values:
            narration = values['narration_text']
            mapped_text = ' '.join(v.keys())
            # Basic validation that most text is covered
            coverage = len(mapped_text) / len(narration)
            if coverage < 0.7:
                raise ValueError("Narration tones must cover at least 70% of the text")
        return v


class StoryMetadata(BaseModel):
    """Metadata about the generated story."""
    title: Optional[str] = None
    genre: Optional[str] = None
    target_age: Optional[str] = None
    moral_theme: Optional[str] = None
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")


class GeneratedStory(BaseModel):
    """Complete generated story structure."""
    story_summary: str = Field(..., min_length=50, max_length=1000,
                              description="Brief summary of the entire story")
    scenes: List[StoryScene] = Field(..., min_items=3, max_items=20,
                                    description="List of story scenes")
    metadata: Optional[StoryMetadata] = None
    
    @validator('scenes')
    def validate_scene_numbering(cls, v):
        """Ensure scenes are properly numbered sequentially."""
        expected_numbers = list(range(1, len(v) + 1))
        actual_numbers = [scene.scene_number for scene in v]
        if actual_numbers != expected_numbers:
            raise ValueError("Scenes must be numbered sequentially starting from 1")
        return v


class StoryConcept(BaseModel):
    """Input concept for story generation."""
    characters: Dict[str, str] = Field(..., description="Character roles and descriptions")
    plot: str = Field(..., min_length=20, description="Main plot description")
    moral: str = Field(..., min_length=10, description="Story moral or theme")
    genre: Optional[str] = "fantasy"
    target_age: Optional[str] = "children"
    style_examples: Optional[List[str]] = Field(None, description="Example story styles to follow")


class GenerationConfig(BaseModel):
    """Configuration for story generation."""
    model_name: str = "gpt-4o"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4000, ge=1000, le=8000)
    include_validation: bool = True
    retry_attempts: int = Field(3, ge=1, le=5)
    

class GenerationResult(BaseModel):
    """Result of story generation process."""
    success: bool
    story: Optional[GeneratedStory] = None
    error_message: Optional[str] = None
    generation_time: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    model_used: Optional[str] = None


class AssetGenerationStatus(BaseModel):
    """Status of multi-modal asset generation."""
    scene_number: int
    image_generated: bool = False
    audio_generated: bool = False
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    error_message: Optional[str] = None
