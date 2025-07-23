"""
ASCII Art Optimizer - Advanced Techniques Implementation
Based on research from Medium article on ASCII Art optimization techniques:
https://medium.com/@gehnaahuja011/image-to-ascii-art-e7eb671e1d69

Key optimizations implemented:
1. Character density optimization using varying ASCII characters
2. Adaptive terminal sizing for responsive display
3. Performance-optimized rendering with ANSI escape sequences
4. Image-to-ASCII conversion capabilities
5. K-means clustering for color reduction
6. Brightness threshold optimization
7. Fallback mechanisms for different terminal environments
"""

import os
import sys
import time
import shutil
from typing import Dict, List, Tuple, Optional
import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    from sklearn.cluster import KMeans
    ADVANCED_IMAGE_PROCESSING = True
except ImportError:
    ADVANCED_IMAGE_PROCESSING = False


class ASCIIArtOptimizer:
    """
    Advanced ASCII Art optimization utility implementing research-based techniques
    for maximum visual fidelity and performance.
    """
    
    def __init__(self):
        self.terminal_width, self.terminal_height = self._get_terminal_size()
        self.char_sets = self._initialize_optimized_char_sets()
        
    def _get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions with fallback."""
        try:
            columns, rows = shutil.get_terminal_size()
            return columns, rows
        except:
            return 80, 24  # Standard fallback
    
    def _initialize_optimized_char_sets(self) -> Dict[str, str]:
        """
        Initialize optimized character sets based on visual density research.
        Characters are arranged from high to low density for better contrast.
        """
        return {
            # High-density to low-density progression for grayscale mapping
            'density_gradient': "@%#*+=-:. ",
            
            # Unicode block characters for smooth gradients
            'unicode_blocks': '█▉▊▋▌▍▎▏',
            
            # Pattern characters for textures
            'patterns': '▓▒░⋅·',
            
            # Specialized characters for different elements
            'water_waves': '~≈∼〰️',
            'sparkles': '✦✧✨⭐',
            'treasures': '💎💰🏆',
            'nautical': '⛵🚢⚓🏴‍☠️',
            'technical': '▲▼◆◇○●',
            
            # Brightness levels (research-optimized)
            'brightness_low': '█▓▒',
            'brightness_mid': '░▒▓',
            'brightness_high': '·⋅ ',
        }
    
    def clear_screen_optimized(self):
        """Optimized screen clearing using ANSI escape sequences on Unix systems."""
        if os.name == 'nt':
            os.system('cls')
        else:
            # Faster ANSI escape sequence method
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.flush()
    
    def adaptive_frame_sizing(self, base_width: int = 78) -> Tuple[int, str]:
        """
        Adaptive frame sizing based on terminal dimensions.
        Returns optimized width and size category.
        """
        if self.terminal_width < 60:
            return min(50, self.terminal_width - 4), "compact"
        elif self.terminal_width < 100:
            return min(78, self.terminal_width - 4), "standard"
        else:
            return min(120, self.terminal_width - 4), "wide"
    
    def generate_border_frame(self, width: int, content_lines: List[str]) -> str:
        """Generate optimized border frame with dynamic width adjustment."""
        top_border = f"╔{'═' * width}╗"
        bottom_border = f"╚{'═' * width}╝"
        separator = f"╠{'═' * width}╣"
        
        framed_content = [top_border]
        
        for line in content_lines:
            # Center content and pad to frame width
            content_length = len(line.encode('utf-8').decode('unicode_escape', errors='ignore'))
            padding = max(0, (width - content_length) // 2)
            padded_line = f"║{' ' * padding}{line}{' ' * (width - content_length - padding)}║"
            framed_content.append(padded_line)
        
        framed_content.append(bottom_border)
        return '\n'.join(framed_content)
    
    def image_to_ascii_basic(self, image_path: str, new_width: int = 50, threshold: int = 210) -> str:
        """
        Basic image-to-ASCII conversion using PIL (if available).
        Implements research-based pixel-to-character mapping.
        """
        if not PIL_AVAILABLE:
            return "PIL not available for image processing"
        
        try:
            # Load and process image
            image = Image.open(image_path)
            
            # Resize maintaining aspect ratio
            width, height = image.size
            aspect_ratio = height / width
            new_height = int((new_width * aspect_ratio) / 2)  # Adjust for character aspect ratio
            image = image.resize((new_width, new_height))
            
            # Convert to grayscale
            image = image.convert("L")
            
            # Convert pixels to ASCII using optimized character mapping
            pixels = np.array(image)
            ascii_chars = self.char_sets['density_gradient']
            ascii_image = []
            
            for pixel in pixels.flatten():
                if pixel > threshold:
                    ascii_image.append(' ')  # Background
                else:
                    # Map pixel intensity to character index
                    char_index = min(len(ascii_chars) - 1, pixel // (256 // len(ascii_chars)))
                    ascii_image.append(ascii_chars[char_index])
            
            # Format into lines
            ascii_str = ''.join(ascii_image)
            ascii_lines = [ascii_str[i:i + new_width] for i in range(0, len(ascii_str), new_width)]
            
            return '\n'.join(ascii_lines)
            
        except Exception as e:
            return f"Error processing image: {e}"
    
    def image_to_ascii_advanced(self, image_path: str, new_width: int = 50, 
                              n_colors: int = 32, threshold: int = 210) -> str:
        """
        Advanced image-to-ASCII conversion using K-means clustering.
        Implements research-based color reduction and optimization.
        """
        if not ADVANCED_IMAGE_PROCESSING:
            return "Advanced image processing libraries not available"
        
        try:
            # Load image using OpenCV
            image = cv2.imread(image_path)
            
            # Resize maintaining aspect ratio
            height, width = image.shape[:2]
            aspect_ratio = height / width
            new_height = int((new_width * aspect_ratio) / 2)
            image = cv2.resize(image, (new_width, new_height))
            
            # Apply K-means color reduction
            pixels = image.reshape((-1, 3))
            kmeans = KMeans(n_clusters=n_colors, init='random', n_init=10, max_iter=300)
            kmeans.fit(pixels)
            clustered_image = kmeans.cluster_centers_[kmeans.labels_]
            image = clustered_image.reshape(image.shape).astype(np.uint8)
            
            # Convert to grayscale
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Convert to ASCII using enhanced mapping
            ascii_chars = self.char_sets['density_gradient']
            ascii_image = []
            
            for pixel in image.flatten():
                if pixel > threshold:
                    ascii_image.append(' ')
                else:
                    # Enhanced pixel-to-character mapping
                    index = int((pixel / 255) * (len(ascii_chars) - 1))
                    ascii_image.append(ascii_chars[index])
            
            # Format output
            ascii_str = ''.join(ascii_image)
            ascii_lines = [ascii_str[i:i + new_width] for i in range(0, len(ascii_str), new_width)]
            
            return '\n'.join(ascii_lines)
            
        except Exception as e:
            return f"Error in advanced processing: {e}"
    
    def create_animated_sequence(self, frames: List[str], timing: List[float] = None) -> None:
        """
        Create optimized animated sequence with variable timing.
        Implements performance optimizations from research.
        """
        if timing is None:
            timing = [0.8] * len(frames)
        
        try:
            # Pre-clear for smoother animation
            self.clear_screen_optimized()
            
            for i, (frame, delay) in enumerate(zip(frames, timing)):
                self.clear_screen_optimized()
                print(frame)
                
                # Variable timing for dramatic effect
                if i == len(frames) - 1:
                    time.sleep(delay * 1.5)  # Hold final frame longer
                else:
                    time.sleep(delay)
                    
        except KeyboardInterrupt:
            self.clear_screen_optimized()
            print("Animation interrupted by user")
        except Exception as e:
            print(f"Animation error: {e}")
    
    def optimize_for_terminal_type(self, content: str) -> str:
        """
        Optimize content based on terminal capabilities.
        Implements adaptive rendering techniques.
        """
        # Detect terminal capabilities
        term_type = os.environ.get('TERM', '').lower()
        
        if 'xterm' in term_type or 'screen' in term_type:
            # Full Unicode support
            return content
        elif 'vt' in term_type:
            # Limited character set - fallback to basic ASCII
            fallback_chars = {
                '█': '#', '▓': '*', '▒': '+', '░': '.',
                '╔': '+', '╗': '+', '╚': '+', '╝': '+',
                '║': '|', '═': '-', '╠': '+', '╣': '+'
            }
            
            optimized_content = content
            for unicode_char, ascii_char in fallback_chars.items():
                optimized_content = optimized_content.replace(unicode_char, ascii_char)
            
            return optimized_content
        else:
            # Unknown terminal - use safe ASCII
            return self._safe_ascii_fallback(content)
    
    def _safe_ascii_fallback(self, content: str) -> str:
        """Fallback to safe ASCII characters for compatibility."""
        # Replace all Unicode with safe ASCII equivalents
        safe_replacements = {
            '🏴‍☠️': '[FLAG]', '⚡': '*', '💎': '$', '💰': '$',
            '🚢': '[SHIP]', '⛵': '[BOAT]', '🐋': '[WHALE]',
            '█': '#', '▓': '*', '▒': '+', '░': '.',
            '╔': '+', '╗': '+', '╚': '+', '╝': '+',
            '║': '|', '═': '-', '╠': '+', '╣': '+',
            '~': '~', '≈': '~', '∼': '~'
        }
        
        safe_content = content
        for unicode_char, safe_char in safe_replacements.items():
            safe_content = safe_content.replace(unicode_char, safe_char)
        
        return safe_content
    
    def benchmark_performance(self, test_function, iterations: int = 100) -> Dict[str, float]:
        """
        Benchmark ASCII art rendering performance.
        Useful for optimizing display operations.
        """
        import time
        
        times = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            test_function()
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_time': sum(times)
        }
    
    def generate_performance_report(self) -> str:
        """Generate performance optimization report."""
        width, size_category = self.adaptive_frame_sizing()
        
        report = f"""
ASCII Art Optimizer - Performance Report
========================================

Terminal Dimensions: {self.terminal_width}x{self.terminal_height}
Optimal Frame Width: {width}
Size Category: {size_category}
Terminal Type: {os.environ.get('TERM', 'unknown')}

Character Sets Available:
- Density Gradient: {len(self.char_sets['density_gradient'])} chars
- Unicode Blocks: {len(self.char_sets['unicode_blocks'])} chars  
- Pattern Characters: {len(self.char_sets['patterns'])} chars

Image Processing Capabilities:
- PIL Available: {PIL_AVAILABLE}
- Advanced Processing: {ADVANCED_IMAGE_PROCESSING}

Optimization Features:
✓ Adaptive terminal sizing
✓ ANSI escape sequence optimization
✓ Character density mapping
✓ Performance benchmarking
✓ Fallback mechanisms
✓ Unicode compatibility detection

Recommendations:
- Use {size_category} layout for optimal display
- Frame width: {width} characters
- {'Enable' if not PIL_AVAILABLE else 'PIL available for'} image processing
- {'Install OpenCV/sklearn for' if not ADVANCED_IMAGE_PROCESSING else 'Advanced processing ready for'} K-means optimization
        """
        
        return report


# Usage example and testing functions
def demo_optimization_techniques():
    """Demonstrate various ASCII art optimization techniques."""
    optimizer = ASCIIArtOptimizer()
    
    print("ASCII Art Optimizer Demo")
    print("=" * 50)
    
    # Show performance report
    print(optimizer.generate_performance_report())
    
    # Demo adaptive sizing
    width, category = optimizer.adaptive_frame_sizing()
    print(f"\nAdaptive sizing result: {width} chars ({category})")
    
    # Demo character sets
    print(f"\nOptimized character sets:")
    for name, chars in optimizer.char_sets.items():
        print(f"  {name}: {chars[:20]}{'...' if len(chars) > 20 else ''}")


if __name__ == "__main__":
    demo_optimization_techniques() 