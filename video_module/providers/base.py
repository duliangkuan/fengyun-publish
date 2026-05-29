from abc import ABC, abstractmethod
from pathlib import Path


class AvatarProvider(ABC):
    name: str

    @abstractmethod
    def generate(
        self,
        image_path: Path,
        audio_path: Path,
        output_path: Path,
        text_prompt: str = "",
        **kwargs,
    ) -> Path:
        """Generate a talking-head video from a portrait image and an audio clip.

        Returns the absolute path to the output mp4.
        """
