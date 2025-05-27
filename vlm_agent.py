import logging
from PIL import Image
import ollama
from io import BytesIO
import base64
import hashlib
import os
from functools import lru_cache
import re

# Configure logging
logger = logging.getLogger(__name__)

class BreastMRIAnalyzer:
    def __init__(self):
        self.model_name = 'gemma3:4b'
        self.cache_dir = 'cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
    def _compress_image(self, image, max_size=(800, 800)):
        """Compress image while maintaining aspect ratio."""
        if isinstance(image, bytes):
            image = Image.open(BytesIO(image))
        
        # Calculate new dimensions while maintaining aspect ratio
        ratio = min(max_size[0]/image.size[0], max_size[1]/image.size[1])
        new_size = tuple(int(dim * ratio) for dim in image.size)
        
        # Resize image
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return image
    
    def _get_cache_key(self, image_data):
        """Generate a cache key for the image."""
        if isinstance(image_data, bytes):
            return hashlib.md5(image_data).hexdigest()
        return hashlib.md5(image_data.tobytes()).hexdigest()
    
    @lru_cache(maxsize=100)
    def _get_cached_analysis(self, cache_key):
        """Get cached analysis if available."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                import json
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _save_to_cache(self, cache_key, analysis):
        """Save analysis to cache."""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            import json
            with open(cache_file, 'w') as f:
                json.dump(analysis, f)
        except:
            pass
        
    

    def analyze_mri_scan(self, image_data):
        """
        Analyzes a breast MRI scan image and determines the stage of cancer.
        
        Args:
            image_data: Image data in bytes or PIL Image format
            
        Returns:
            dict: Analysis results containing stage, confidence, and markdown report
        """
        try:
            # Generate cache key
            cache_key = self._get_cache_key(image_data)
            
            # Compress image
            image = self._compress_image(image_data)
            
            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Prepare the prompt for analysis
            prompt = """
    You are a medical AI Vision-Language assistant specialized in analyzing breast cancer medical images and generating diagnostic insights.

    Your task is to:
    1. Accurately analyze the uploaded breast scan image.
    2. Identify and classify the cancer stage as one of the following:
    - Preliminary Stage
    - Middle Stage
    - Final Stage
    3. Provide a concise medical explanation justifying your stage classification based on visual markers observed in the image (e.g., tumor size, lymph node involvement, tissue structure, etc.).
    4. Based on the identified stage, follow these outputs:
    - If **Preliminary Stage**:
        • Provide key **precautionary measures** based on standard medical guidelines to prevent cancer progression.
    - If **Middle or Final Stage**:
        • Provide an **analysis of the cancer progression**, and suggest medically recommended **treatment strategies** or **recovery plans** aligned with current oncology practices.

    Your output should be clear, accurate, medically relevant, and ready to be included in a structured PDF report. Avoid speculative language. Do not generate treatment or medical advice outside of recognized guidelines.
   
                     """
            
            # Generate analysis using Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [img_str]
                    }
                ]
            )
            
            # Process and structure the response
            content = response['message']['content']
            analysis = {
                'stage': self._extract_stage(content),
                'observations': self._extract_observations(content),
                'confidence': self._extract_confidence(content),
                'raw_response': content
            }

            # Format analysis as plain text
            analysis_text = (
                f"Stage: {analysis['stage']}\n"
                f"Observations: {analysis['observations']}\n"
                f"Confidence: {analysis['confidence']}\n"
                f"Raw Response:\n{analysis['raw_response']}"
            )

            print(analysis['observations'])
            print("")

            # Prompt for Markdown formatting
            markdown_prompt = f"""
            Convert the following text into a well-structured Markdown format. Include ALL of the following sections:
            1. Analysis (including stage, observations, and confidence level)
            2. Detailed medical explanation
            3. Treatment recommendations or precautionary measures based on the stage
            4. A medical disclaimer

            Format it with proper Markdown headers, bullet points, and emphasis where appropriate.
            and Give entire response in between ```markdown``` tags

            {analysis_text}
            """

            # Generate markdown from analysis
            analysis_md_response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": markdown_prompt.strip()
                    }
                ]
            )
            
            analysis_md = analysis_md_response['message']['content']
            # Extract markdown content between ```markdown``` tags
            match = re.search(r'```markdown\n([\s\S]*?)\n```', analysis_md)
            if not match:
                # If no markdown tags found, use the content as is
                analysis_new_md = analysis_md
            else:
                analysis_new_md = match.group(1)
            
            print("------------------------------------------------")
            print(analysis_new_md)

            # Include markdown result in final output
            analysis['markdown'] = analysis_new_md
            
            return {
                'stage': analysis['stage'],
                'observations': analysis['observations'],
                'confidence': analysis['confidence'],
                'raw_response': analysis['raw_response'],
                'markdown': analysis_new_md
            }

        except Exception as e:
            logger.error(f"Error analyzing MRI scan: {str(e)}")
            return {
                'error': f"Failed to analyze image: {str(e)}",
                'stage': 'unknown',
                'observations': [],
                'confidence': 0.0,
                'markdown': ''
            }

    
    def _extract_stage(self, response_text):
        """Extract the cancer stage from the model response."""
        stages = ['preliminary', 'middle', 'final']
        response_lower = response_text.lower()
        
        for stage in stages:
            if stage in response_lower:
                return stage
        return 'unknown'
    
    def _extract_observations(self, response_text):
        """Extract key observations from the model response."""
        observations = []
        lines = response_text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['observe', 'note', 'finding', 'indicate', 'show', 'reveal', 'detect']):
                observations.append(line.strip())
        return observations
    
    def _extract_confidence(self, response_text):
        """Extract confidence level from the model response."""
        try:
            if 'confidence' in response_text.lower():
                # Look for percentage or decimal
                import re
                confidence_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response_text)
                if confidence_match:
                    return float(confidence_match.group(1)) / 100
        except:
            pass
        return 0.0