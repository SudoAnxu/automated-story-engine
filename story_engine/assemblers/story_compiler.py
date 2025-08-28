"""Story compiler for assembling multi-modal assets into final output."""

import asyncio
import json
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

try:
    from moviepy.editor import (
        ImageClip, AudioFileClip, CompositeVideoClip, 
        concatenate_videoclips, VideoFileClip
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    # Moviepy not available - video compilation will be disabled
    ImageClip = AudioFileClip = CompositeVideoClip = None
    concatenate_videoclips = VideoFileClip = None
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    Image = ImageDraw = ImageFont = None
    PIL_AVAILABLE = False

from ..core.models import GeneratedStory, AssetGenerationStatus

logger = logging.getLogger(__name__)


class StoryCompiler:
    """Compile multi-modal story assets into final output formats."""
    
    def __init__(self, config: Dict[str, Any], output_dir: str = "./generated_stories"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Check available features
        self.moviepy_available = MOVIEPY_AVAILABLE
        self.pil_available = PIL_AVAILABLE
        
        if not self.moviepy_available:
            logger.warning("MoviePy not available - video compilation disabled")
        if not self.pil_available:
            logger.warning("PIL not available - image processing limited")
        
        # Compilation settings
        self.scene_duration = config.get('story_parameters', {}).get('scene_duration', 30)
        self.transition_duration = config.get('story_parameters', {}).get('transition_duration', 2)
        self.video_resolution = (1920, 1080)  # Full HD
        self.fps = 24
        
        # Compilation statistics
        self.stats = {
            'total_compilations': 0,
            'successful_compilations': 0,
            'failed_compilations': 0,
            'total_output_duration': 0
        }
    
    async def compile_story(self, story: GeneratedStory, 
                          image_statuses: List[AssetGenerationStatus],
                          audio_statuses: List[AssetGenerationStatus],
                          story_title: str = "story",
                          output_formats: List[str] = None) -> Dict[str, Any]:
        """Compile a complete story from generated assets."""
        
        if output_formats is None:
            output_formats = ['mp4', 'json', 'html']
        
        self.stats['total_compilations'] += 1
        
        try:
            story_dir = self.output_dir / story_title
            story_dir.mkdir(exist_ok=True)
            
            # Validate assets
            asset_validation = self._validate_assets(story, image_statuses, audio_statuses)
            if not asset_validation['valid']:
                return {
                    'success': False,
                    'error': f"Asset validation failed: {asset_validation['error']}",
                    'outputs': {}
                }
            
            compilation_results = {}
            
            # Generate different output formats
            for format_type in output_formats:
                try:
                    if format_type == 'mp4':
                        if not self.moviepy_available:
                            result = {
                                'success': False,
                                'error': 'MoviePy not available - install with: pip install moviepy'
                            }
                        else:
                            result = await self._compile_video(
                                story, image_statuses, audio_statuses, story_title
                            )
                    elif format_type == 'json':
                        result = await self._compile_json_package(
                            story, image_statuses, audio_statuses, story_title
                        )
                    elif format_type == 'html':
                        result = await self._compile_interactive_html(
                            story, image_statuses, audio_statuses, story_title
                        )
                    elif format_type == 'epub':
                        result = await self._compile_epub(
                            story, image_statuses, audio_statuses, story_title
                        )
                    else:
                        result = {'success': False, 'error': f'Unknown format: {format_type}'}
                    
                    compilation_results[format_type] = result
                    
                except Exception as e:
                    logger.error(f"Failed to compile {format_type}: {str(e)}")
                    compilation_results[format_type] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Check if any compilation succeeded
            success = any(result.get('success', False) for result in compilation_results.values())
            
            if success:
                self.stats['successful_compilations'] += 1
            else:
                self.stats['failed_compilations'] += 1
            
            return {
                'success': success,
                'outputs': compilation_results,
                'story_directory': str(story_dir)
            }
            
        except Exception as e:
            logger.error(f"Story compilation failed: {str(e)}")
            self.stats['failed_compilations'] += 1
            return {
                'success': False,
                'error': str(e),
                'outputs': {}
            }
    
    def _validate_assets(self, story: GeneratedStory,
                        image_statuses: List[AssetGenerationStatus],
                        audio_statuses: List[AssetGenerationStatus]) -> Dict[str, Any]:
        """Validate that all required assets are available."""
        
        scene_count = len(story.scenes)
        
        # Check image assets
        image_scenes = {status.scene_number for status in image_statuses if status.image_generated}
        missing_images = set(range(1, scene_count + 1)) - image_scenes
        
        # Check audio assets
        audio_scenes = {status.scene_number for status in audio_statuses if status.audio_generated}
        missing_audio = set(range(1, scene_count + 1)) - audio_scenes
        
        if missing_images:
            return {
                'valid': False,
                'error': f"Missing images for scenes: {sorted(missing_images)}"
            }
        
        if missing_audio:
            return {
                'valid': False,
                'error': f"Missing audio for scenes: {sorted(missing_audio)}"
            }
        
        # Validate file existence
        for status in image_statuses:
            if status.image_generated and status.image_path:
                if not Path(status.image_path).exists():
                    return {
                        'valid': False,
                        'error': f"Image file not found: {status.image_path}"
                    }
        
        for status in audio_statuses:
            if status.audio_generated and status.audio_path:
                if not Path(status.audio_path).exists():
                    return {
                        'valid': False,
                        'error': f"Audio file not found: {status.audio_path}"
                    }
        
        return {'valid': True}
    
    async def _compile_video(self, story: GeneratedStory,
                           image_statuses: List[AssetGenerationStatus],
                           audio_statuses: List[AssetGenerationStatus],
                           story_title: str) -> Dict[str, Any]:
        """Compile story into MP4 video format."""
        
        try:
            # Create scene clips
            scene_clips = []
            
            for scene in story.scenes:
                # Find corresponding assets
                image_status = next((s for s in image_statuses if s.scene_number == scene.scene_number), None)
                audio_status = next((s for s in audio_statuses if s.scene_number == scene.scene_number), None)
                
                if not image_status or not audio_status:
                    continue
                
                # Create scene clip
                scene_clip = await self._create_scene_clip(
                    scene, image_status.image_path, audio_status.audio_path
                )
                
                if scene_clip:
                    scene_clips.append(scene_clip)
            
            if not scene_clips:
                return {
                    'success': False,
                    'error': 'No valid scene clips could be created'
                }
            
            # Concatenate all scenes
            final_video = concatenate_videoclips(scene_clips, method="compose")
            
            # Add title and credits
            final_video = await self._add_title_and_credits(final_video, story, story_title)
            
            # Export video
            output_path = self.output_dir / story_title / f"{story_title}_complete.mp4"
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Update stats
            self.stats['total_output_duration'] += final_video.duration
            
            # Clean up
            final_video.close()
            for clip in scene_clips:
                clip.close()
            
            return {
                'success': True,
                'output_path': str(output_path),
                'duration': final_video.duration,
                'format': 'mp4'
            }
            
        except Exception as e:
            logger.error(f"Video compilation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _create_scene_clip(self, scene, image_path: str, audio_path: str) -> Optional[VideoFileClip]:
        """Create a video clip for a single scene."""
        
        try:
            # Load audio to get duration
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # Load and prepare image
            image_clip = ImageClip(image_path).set_duration(audio_duration)
            image_clip = image_clip.resize(self.video_resolution)
            
            # Add subtle zoom effect for visual interest
            image_clip = image_clip.resize(lambda t: 1 + 0.02 * t / audio_duration)
            
            # Combine image and audio
            scene_clip = image_clip.set_audio(audio_clip)
            
            # Add scene number overlay (optional)
            if self.config.get('video_settings', {}).get('show_scene_numbers', False):
                scene_clip = self._add_scene_number_overlay(scene_clip, scene.scene_number)
            
            return scene_clip
            
        except Exception as e:
            logger.error(f"Failed to create scene clip {scene.scene_number}: {str(e)}")
            return None
    
    def _add_scene_number_overlay(self, clip, scene_number: int):
        """Add scene number overlay to video clip."""
        # This would require more complex text overlay implementation
        # For now, return clip as-is
        return clip
    
    async def _add_title_and_credits(self, video_clip, story: GeneratedStory, story_title: str):
        """Add title card and credits to the video."""
        
        try:
            # Create title card
            title_clip = await self._create_title_card(story_title, story.story_summary)
            
            # Create credits
            credits_clip = await self._create_credits_card()
            
            # Combine: title + story + credits
            if title_clip and credits_clip:
                final_clip = concatenate_videoclips([title_clip, video_clip, credits_clip])
            elif title_clip:
                final_clip = concatenate_videoclips([title_clip, video_clip])
            else:
                final_clip = video_clip
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Failed to add title/credits: {str(e)}")
            return video_clip
    
    async def _create_title_card(self, title: str, summary: str) -> Optional[VideoFileClip]:
        """Create an animated title card."""
        
        try:
            # Create title image using PIL
            img = Image.new('RGB', self.video_resolution, color='#2c3e50')
            draw = ImageDraw.Draw(img)
            
            # Try to load a nice font, fallback to default
            try:
                title_font = ImageFont.truetype("arial.ttf", 72)
                subtitle_font = ImageFont.truetype("arial.ttf", 36)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # Calculate text positions
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            title_x = (self.video_resolution[0] - title_width) // 2
            title_y = self.video_resolution[1] // 3
            
            # Draw title
            draw.text((title_x, title_y), title, fill='white', font=title_font)
            
            # Draw summary (wrapped)
            summary_words = summary.split()
            lines = []
            current_line = []
            
            for word in summary_words:
                test_line = ' '.join(current_line + [word])
                test_bbox = draw.textbbox((0, 0), test_line, font=subtitle_font)
                test_width = test_bbox[2] - test_bbox[0]
                
                if test_width <= self.video_resolution[0] - 200:  # Leave margins
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw summary lines
            summary_y = title_y + title_height + 50
            line_height = 50
            
            for i, line in enumerate(lines[:3]):  # Limit to 3 lines
                line_bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (self.video_resolution[0] - line_width) // 2
                
                draw.text((line_x, summary_y + i * line_height), line, 
                         fill='#ecf0f1', font=subtitle_font)
            
            # Save title image
            title_image_path = self.output_dir / "temp_title.png"
            img.save(title_image_path)
            
            # Create video clip from image
            title_clip = ImageClip(str(title_image_path)).set_duration(3)
            
            # Clean up temp file
            title_image_path.unlink()
            
            return title_clip
            
        except Exception as e:
            logger.error(f"Failed to create title card: {str(e)}")
            return None
    
    async def _create_credits_card(self) -> Optional[VideoFileClip]:
        """Create a credits card."""
        
        try:
            # Simple credits card
            img = Image.new('RGB', self.video_resolution, color='#34495e')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            credits_text = "Created with Automated Story Engine"
            credits_bbox = draw.textbbox((0, 0), credits_text, font=font)
            credits_width = credits_bbox[2] - credits_bbox[0]
            
            credits_x = (self.video_resolution[0] - credits_width) // 2
            credits_y = self.video_resolution[1] // 2
            
            draw.text((credits_x, credits_y), credits_text, fill='white', font=font)
            
            # Save and create clip
            credits_image_path = self.output_dir / "temp_credits.png"
            img.save(credits_image_path)
            
            credits_clip = ImageClip(str(credits_image_path)).set_duration(2)
            
            # Clean up
            credits_image_path.unlink()
            
            return credits_clip
            
        except Exception as e:
            logger.error(f"Failed to create credits: {str(e)}")
            return None
    
    async def _compile_json_package(self, story: GeneratedStory,
                                  image_statuses: List[AssetGenerationStatus],
                                  audio_statuses: List[AssetGenerationStatus],
                                  story_title: str) -> Dict[str, Any]:
        """Compile story into a structured JSON package."""
        
        try:
            # Create comprehensive story package
            story_package = {
                'metadata': {
                    'title': story_title,
                    'created_at': datetime.now().isoformat(),
                    'story_engine_version': '1.0.0',
                    'scene_count': len(story.scenes),
                    'total_duration': sum(
                        self._estimate_scene_duration(scene) for scene in story.scenes
                    )
                },
                'story': story.dict(),
                'assets': {
                    'images': [
                        {
                            'scene_number': status.scene_number,
                            'path': status.image_path,
                            'generated': status.image_generated
                        }
                        for status in image_statuses
                    ],
                    'audio': [
                        {
                            'scene_number': status.scene_number,
                            'path': status.audio_path,
                            'generated': status.audio_generated
                        }
                        for status in audio_statuses
                    ]
                },
                'compilation_info': {
                    'formats_generated': ['json'],
                    'scene_duration_seconds': self.scene_duration,
                    'transition_duration_seconds': self.transition_duration
                }
            }
            
            # Save JSON package
            output_path = self.output_dir / story_title / f"{story_title}_package.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(story_package, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'format': 'json'
            }
            
        except Exception as e:
            logger.error(f"JSON compilation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _compile_interactive_html(self, story: GeneratedStory,
                                      image_statuses: List[AssetGenerationStatus],
                                      audio_statuses: List[AssetGenerationStatus],
                                      story_title: str) -> Dict[str, Any]:
        """Compile story into an interactive HTML format."""
        
        try:
            html_template = self._get_html_template()
            
            # Prepare scene data for HTML
            scenes_data = []
            for scene in story.scenes:
                image_status = next((s for s in image_statuses if s.scene_number == scene.scene_number), None)
                audio_status = next((s for s in audio_statuses if s.scene_number == scene.scene_number), None)
                
                scene_data = {
                    'number': scene.scene_number,
                    'plot_summary': scene.plot_summary,
                    'narration': scene.narration_text,
                    'image_path': Path(image_status.image_path).name if image_status and image_status.image_path else None,
                    'audio_path': Path(audio_status.audio_path).name if audio_status and audio_status.audio_path else None,
                    'transition_from_previous': getattr(scene, 'transition_from_previous', None),
                    'transition_to_next': getattr(scene, 'transition_to_next', None)
                }
                scenes_data.append(scene_data)
            
            # Generate HTML
            html_content = html_template.format(
                story_title=story_title,
                story_summary=story.story_summary,
                scenes_json=json.dumps(scenes_data),
                scene_count=len(scenes_data)
            )
            
            # Save HTML file
            output_path = self.output_dir / story_title / f"{story_title}_interactive.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'format': 'html'
            }
            
        except Exception as e:
            logger.error(f"HTML compilation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_html_template(self) -> str:
        """Get HTML template for interactive story."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{story_title}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .story-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .story-title {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 2.5em;
        }}
        .story-summary {{
            text-align: center;
            font-style: italic;
            margin-bottom: 30px;
            color: #7f8c8d;
            line-height: 1.6;
        }}
        .scene {{
            margin-bottom: 40px;
            padding: 25px;
            border-radius: 15px;
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            transition: all 0.3s ease;
        }}
        .scene:hover {{
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        .scene-number {{
            font-weight: bold;
            color: #3498db;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        .scene-image {{
            width: 100%;
            max-width: 500px;
            border-radius: 10px;
            margin: 20px 0;
            display: block;
            margin-left: auto;
            margin-right: auto;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .scene-text {{
            line-height: 1.9;
            margin: 20px 0;
            font-size: 1.1em;
            text-align: justify;
        }}
        .transition-text {{
            font-style: italic;
            color: #7f8c8d;
            margin: 15px 0;
            padding: 10px;
            background: rgba(52, 152, 219, 0.1);
            border-radius: 8px;
            border-left: 3px solid #3498db;
        }}
        .scene-content {{
            margin: 15px 0;
        }}
        .audio-controls {{
            text-align: center;
            margin: 15px 0;
        }}
        .audio-controls audio {{
            width: 100%;
            max-width: 400px;
        }}
        .navigation {{
            text-align: center;
            margin: 20px 0;
        }}
        .nav-button {{
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .nav-button:hover {{
            background: #2980b9;
        }}
        .nav-button:disabled {{
            background: #bdc3c7;
            cursor: not-allowed;
        }}
        .scene {{
            display: none;
        }}
        .scene.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="story-container">
        <h1 class="story-title">{story_title}</h1>
        <p class="story-summary">{story_summary}</p>
        
        <div id="scenes-container">
            <!-- Scenes will be populated by JavaScript -->
        </div>
        
        <div class="navigation">
            <button class="nav-button" id="prev-btn" onclick="previousScene()">Previous</button>
            <span id="scene-counter">Scene 1 of {scene_count}</span>
            <button class="nav-button" id="next-btn" onclick="nextScene()">Next</button>
        </div>
    </div>

    <script>
        const scenes = {scenes_json};
        let currentScene = 0;

        function displayScene(sceneIndex) {{
            const container = document.getElementById('scenes-container');
            const scene = scenes[sceneIndex];
            
            let transitionFrom = '';
            let transitionTo = '';
            
            // Add transition from previous scene (if available)
            if (scene.transition_from_previous && sceneIndex > 0) {{
                transitionFrom = `<div class="transition-text">${{scene.transition_from_previous}}</div>`;
            }}
            
            // Add transition to next scene (if available)
            if (scene.transition_to_next && sceneIndex < scenes.length - 1) {{
                transitionTo = `<div class="transition-text">${{scene.transition_to_next}}</div>`;
            }}
            
            container.innerHTML = `
                <div class="scene active">
                    <div class="scene-number">Scene ${{scene.number}}</div>
                    ${{transitionFrom}}
                    ${{scene.image_path ? `<img src="${{scene.image_path}}" alt="Scene ${{scene.number}}" class="scene-image">` : ''}}
                    <div class="scene-content">
                        <div class="scene-text">${{scene.narration}}</div>
                        ${{scene.audio_path ? `
                            <div class="audio-controls">
                                <audio controls>
                                    <source src="${{scene.audio_path}}" type="audio/mpeg">
                                    Your browser does not support the audio element.
                                </audio>
                            </div>
                        ` : ''}}
                    </div>
                    ${{transitionTo}}
                </div>
            `;
            
            // Update navigation
            document.getElementById('scene-counter').textContent = `Scene ${{sceneIndex + 1}} of ${{scenes.length}}`;
            document.getElementById('prev-btn').disabled = sceneIndex === 0;
            document.getElementById('next-btn').disabled = sceneIndex === scenes.length - 1;
        }}

        function nextScene() {{
            if (currentScene < scenes.length - 1) {{
                currentScene++;
                displayScene(currentScene);
            }}
        }}

        function previousScene() {{
            if (currentScene > 0) {{
                currentScene--;
                displayScene(currentScene);
            }}
        }}

        // Initialize
        displayScene(0);
        
        // Keyboard navigation
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'ArrowRight') nextScene();
            if (event.key === 'ArrowLeft') previousScene();
        }});
    </script>
</body>
</html>'''
    
    async def _compile_epub(self, story: GeneratedStory,
                          image_statuses: List[AssetGenerationStatus],
                          audio_statuses: List[AssetGenerationStatus],
                          story_title: str) -> Dict[str, Any]:
        """Compile story into EPUB format (placeholder implementation)."""
        
        # This would require a library like ebooklib
        # For now, return a simple implementation status
        return {
            'success': False,
            'error': 'EPUB compilation not yet implemented'
        }
    
    def _estimate_scene_duration(self, scene) -> float:
        """Estimate duration of a scene based on text length."""
        # Rough estimation: 150 words per minute speaking rate
        word_count = len(scene.narration_text.split())
        return max(word_count / 2.5, 5)  # Minimum 5 seconds per scene
    
    def get_compilation_stats(self) -> Dict[str, Any]:
        """Get compilation statistics."""
        stats = self.stats.copy()
        if stats['total_compilations'] > 0:
            stats['success_rate'] = stats['successful_compilations'] / stats['total_compilations']
        else:
            stats['success_rate'] = 0
        
        return stats
