"""
ABOUTME: Betty Prompt Injection Detection System
ABOUTME: Implements Phase 1 basic security measures for prompt injection prevention
"""

import re
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BettyInjectionDetector:
    """
    Phase 1: Basic prompt injection detection for Betty
    Implements pattern matching and heuristic analysis
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.detection_patterns = self._load_patterns()
        self.max_input_length = 10000
        self.security_log = []
        
    def _load_patterns(self) -> Dict[str, List[str]]:
        """Load detection patterns for various injection types"""
        return {
            'direct_injection': [
                r'ignore\s+(all\s+)?previous\s+instructions?',
                r'disregard\s+(all\s+)?prior\s+instructions?',
                r'forget\s+everything',
                r'system\s+(override|prompt|message)',
                r'reveal\s+(your\s+)?(system\s+)?prompt',
                r'show\s+me\s+your\s+instructions',
                r'what\s+are\s+your\s+instructions',
            ],
            'role_manipulation': [
                r'you\s+are\s+now\s+in\s+(developer|debug|admin|god)\s+mode',
                r'pretend\s+you\s+are',
                r'act\s+as\s+if\s+you',
                r'you\s+are\s+now\s+\w+',
                r'from\s+now\s+on\s+you',
                r'switch\s+to\s+\w+\s+mode',
            ],
            'encoding_attempts': [
                r'base64[:=]',
                r'\\x[0-9a-f]{2}',
                r'\\u[0-9a-f]{4}',
                r'%[0-9a-f]{2}',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'data_extraction': [
                r'list\s+all\s+(your\s+)?functions',
                r'show\s+all\s+capabilities',
                r'what\s+can\s+you\s+access',
                r'print\s+debug\s+info',
                r'dump\s+(memory|database|logs)',
            ],
            'tool_abuse': [
                r'execute\s+command',
                r'run\s+shell\s+script',
                r'access\s+file\s+system',
                r'read\s+/etc/passwd',
                r'cat\s+/etc/',
                r'sudo\s+',
                r'rm\s+-rf',
            ]
        }
    
    def detect_injection(self, text: str, context: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Main detection method - analyzes input for injection attempts
        
        Args:
            text: User input to analyze
            context: Optional context for advanced detection
            
        Returns:
            Tuple of (is_injection, details)
        """
        # Sanitize and normalize input
        normalized_text = self._normalize_input(text)
        
        # Check input length
        if len(text) > self.max_input_length:
            return True, {
                'reason': 'Input exceeds maximum length',
                'length': len(text),
                'max_length': self.max_input_length
            }
        
        # Pattern matching
        detected_patterns = self._check_patterns(normalized_text)
        if detected_patterns:
            self._log_detection(text, detected_patterns, context)
            return True, {
                'reason': 'Injection pattern detected',
                'patterns': detected_patterns,
                'confidence': self._calculate_confidence(detected_patterns)
            }
        
        # Heuristic analysis
        heuristic_score = self._heuristic_analysis(normalized_text)
        if heuristic_score > 0.7:
            self._log_detection(text, ['heuristic'], context)
            return True, {
                'reason': 'Heuristic analysis triggered',
                'score': heuristic_score
            }
        
        return False, {'status': 'clean'}
    
    def _normalize_input(self, text: str) -> str:
        """Normalize input for consistent detection"""
        # Convert to lowercase for pattern matching
        normalized = text.lower()
        
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove zero-width characters
        normalized = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', normalized)
        
        return normalized.strip()
    
    def _check_patterns(self, text: str) -> List[str]:
        """Check text against known injection patterns"""
        detected = []
        
        for category, patterns in self.detection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected.append(f"{category}:{pattern[:30]}...")
                    
        return detected
    
    def _heuristic_analysis(self, text: str) -> float:
        """
        Perform heuristic analysis for subtle injection attempts
        Returns confidence score 0-1
        """
        score = 0.0
        
        # Check for unusual character density
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text))
        if special_chars / max(len(text), 1) > 0.3:
            score += 0.3
            
        # Check for suspicious keywords
        suspicious_keywords = [
            'system', 'prompt', 'instruction', 'override', 
            'ignore', 'admin', 'debug', 'mode', 'execute'
        ]
        keyword_count = sum(1 for kw in suspicious_keywords if kw in text.lower())
        score += min(keyword_count * 0.1, 0.4)
        
        # Check for repetitive patterns (common in attacks)
        words = text.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:
                score += 0.2
                
        # Check for encoding indicators
        if any(enc in text for enc in ['base64', '\\x', '\\u', 'eval', 'exec']):
            score += 0.3
            
        return min(score, 1.0)
    
    def _calculate_confidence(self, detected_patterns: List[str]) -> float:
        """Calculate confidence score based on detected patterns"""
        if not detected_patterns:
            return 0.0
            
        # More patterns = higher confidence
        base_score = min(len(detected_patterns) * 0.2, 0.8)
        
        # Critical patterns get higher weight
        critical_patterns = ['system_override', 'direct_injection', 'tool_abuse']
        critical_count = sum(1 for p in detected_patterns 
                           if any(crit in p for crit in critical_patterns))
        
        return min(base_score + (critical_count * 0.2), 1.0)
    
    def _log_detection(self, text: str, patterns: List[str], context: Optional[Dict]):
        """Log injection detection for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'text_hash': hashlib.sha256(text.encode()).hexdigest()[:16],
            'patterns': patterns,
            'context': context or {},
            'action': 'blocked'
        }
        
        self.security_log.append(log_entry)
        logger.warning(f"Injection attempt detected: {patterns[:3]}")
        
        # Save to file for analysis
        log_file = Path('/home/jarvis/projects/Betty/logs/security/injection_attempts.jsonl')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            'total_checks': len(self.security_log),
            'injections_blocked': len([l for l in self.security_log if l['action'] == 'blocked']),
            'patterns_loaded': sum(len(p) for p in self.detection_patterns.values()),
            'last_detection': self.security_log[-1]['timestamp'] if self.security_log else None
        }


class InputSanitizer:
    """
    Input sanitization for safe processing
    """
    
    @staticmethod
    def sanitize(text: str) -> str:
        """
        Sanitize user input for safe processing
        
        Args:
            text: Raw user input
            
        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        text = text[:10000]
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normalize Unicode
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Collapse excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {3,}', '  ', text)
        
        return text.strip()
    
    @staticmethod
    def validate_json(data: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate and parse JSON safely
        
        Args:
            data: JSON string to validate
            
        Returns:
            Tuple of (is_valid, parsed_data)
        """
        try:
            # Limit JSON size
            if len(data) > 100000:
                return False, None
                
            parsed = json.loads(data)
            
            # Check for suspicious keys
            suspicious_keys = ['__proto__', 'constructor', 'prototype']
            
            def check_dict(d):
                if isinstance(d, dict):
                    for key in d:
                        if key in suspicious_keys:
                            return False
                        if not check_dict(d[key]):
                            return False
                elif isinstance(d, list):
                    for item in d:
                        if not check_dict(item):
                            return False
                return True
            
            if not check_dict(parsed):
                return False, None
                
            return True, parsed
            
        except (json.JSONDecodeError, RecursionError):
            return False, None


# Canary token system for detecting data exfiltration
class CanaryTokens:
    """
    Canary token system for detecting prompt leaks
    """
    
    def __init__(self):
        self.tokens = {}
        
    def generate_token(self, context: str) -> str:
        """Generate a unique canary token"""
        token = f"CANARY_{hashlib.sha256(f'{context}_{datetime.now()}'.encode()).hexdigest()[:12]}"
        self.tokens[token] = {
            'created': datetime.now().isoformat(),
            'context': context,
            'triggered': False
        }
        return token
    
    def check_token(self, text: str) -> Optional[Dict]:
        """Check if text contains any canary tokens"""
        for token, info in self.tokens.items():
            if token in text and not info['triggered']:
                info['triggered'] = True
                info['triggered_at'] = datetime.now().isoformat()
                logger.critical(f"CANARY TOKEN TRIGGERED: {token}")
                return info
        return None