"""
Content filtering service for basic safety and inappropriate content detection.
"""

import re
from typing import Dict, List, Tuple

class ContentFilterService:
    """Basic content filtering service."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the service with Flask app."""
        self.app = app
        
        # Load filter patterns from config or use defaults
        self.blocked_patterns = app.config.get('BLOCKED_PATTERNS', self._get_default_patterns())
        self.warned_patterns = app.config.get('WARNED_PATTERNS', self._get_warning_patterns())
        
        # Content categories
        self.categories = {
            'violence': ['harm', 'hurt', 'kill', 'attack', 'weapon'],
            'inappropriate': ['explicit', 'adult', 'nsfw'],
            'harmful': ['self-harm', 'suicide', 'dangerous'],
            'illegal': ['illegal', 'criminal', 'fraud']
        }
    
    def _get_default_patterns(self) -> List[str]:
        """Get default blocked patterns."""
        return [
            r'\b(harm|hurt|kill|attack|weapon)\b',
            r'\b(explicit|adult|nsfw)\b',
            r'\b(self-harm|suicide|dangerous)\b',
            r'\b(illegal|criminal|fraud)\b'
        ]
    
    def _get_warning_patterns(self) -> List[str]:
        """Get patterns that trigger warnings but don't block."""
        return [
            r'\b(angry|upset|sad|depressed)\b',
            r'\b(stress|anxiety|worried)\b',
            r'\b(relationship|breakup|divorce)\b'
        ]
    
    def filter_content(self, text: str, user_id: int = None) -> Dict:
        """
        Filter content for inappropriate or harmful text.
        
        Args:
            text: Text to filter
            user_id: Optional user ID for logging
            
        Returns:
            Dict with filtering results
        """
        if not text:
            return {
                'passed': True,
                'blocked': False,
                'warnings': [],
                'filtered_text': text
            }
        
        text_lower = text.lower()
        warnings = []
        blocked = False
        blocked_reason = None
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                blocked = True
                blocked_reason = f"Content blocked due to pattern: {pattern}"
                break
        
        # Check for warning patterns
        for pattern in self.warned_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                warnings.append(f"Content may need attention: {pattern}")
        
        # Check for category violations
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category in ['violence', 'harmful', 'illegal']:
                        blocked = True
                        blocked_reason = f"Content blocked due to {category} category"
                        break
                    else:
                        warnings.append(f"Content flagged in {category} category")
        
        # Additional safety checks
        if self._contains_excessive_caps(text):
            warnings.append("Excessive use of capital letters detected")
        
        if self._contains_suspicious_links(text):
            warnings.append("Suspicious links detected")
        
        # Log if blocked (for monitoring)
        if blocked and user_id:
            self._log_blocked_content(user_id, text, blocked_reason)
        
        return {
            'passed': not blocked,
            'blocked': blocked,
            'blocked_reason': blocked_reason,
            'warnings': warnings,
            'filtered_text': text if not blocked else self._sanitize_text(text)
        }
    
    def _contains_excessive_caps(self, text: str) -> bool:
        """Check if text contains excessive capital letters."""
        if len(text) < 10:
            return False
        
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text)
        return caps_ratio > 0.7
    
    def _contains_suspicious_links(self, text: str) -> bool:
        """Check for suspicious links or URLs."""
        # Basic URL detection
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        suspicious_domains = [
            'bit.ly', 'tinyurl', 'goo.gl', 't.co',
            'suspicious.com', 'malware.com'
        ]
        
        for url in urls:
            for domain in suspicious_domains:
                if domain in url.lower():
                    return True
        
        return False
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize blocked text."""
        return "[Content blocked for safety]"
    
    def _log_blocked_content(self, user_id: int, content: str, reason: str):
        """Log blocked content for monitoring."""
        if self.app:
            self.app.logger.warning(
                f"Content blocked for user {user_id}: {reason[:100]}..."
            )
    
    def is_safe(self, text: str) -> bool:
        """Quick check if content is safe."""
        result = self.filter_content(text)
        return result['passed']
    
    def get_content_score(self, text: str) -> float:
        """
        Get a content safety score (0.0 = safe, 1.0 = very unsafe).
        
        Args:
            text: Text to score
            
        Returns:
            Float between 0.0 and 1.0
        """
        if not text:
            return 0.0
        
        result = self.filter_content(text)
        
        if result['blocked']:
            return 1.0
        
        # Calculate score based on warnings and patterns
        score = 0.0
        text_lower = text.lower()
        
        # Add points for each warning pattern found
        for pattern in self.warned_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 0.2
        
        # Add points for category violations
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category in ['violence', 'harmful', 'illegal']:
                        score += 0.4
                    else:
                        score += 0.1
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    def update_patterns(self, new_patterns: List[str], pattern_type: str = 'blocked'):
        """Update filter patterns dynamically."""
        if pattern_type == 'blocked':
            self.blocked_patterns = new_patterns
        elif pattern_type == 'warned':
            self.warned_patterns = new_patterns
        
        if self.app:
            self.app.logger.info(f"Updated {pattern_type} patterns")
    
    def get_filter_stats(self) -> Dict:
        """Get filtering statistics."""
        return {
            'blocked_patterns': len(self.blocked_patterns),
            'warning_patterns': len(self.warned_patterns),
            'categories': len(self.categories),
            'total_patterns': len(self.blocked_patterns) + len(self.warned_patterns)
        }
