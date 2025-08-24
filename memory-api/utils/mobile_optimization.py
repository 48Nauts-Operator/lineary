# ABOUTME: Mobile optimization utilities for Betty's responsive executive dashboard
# ABOUTME: Provides data compression, adaptive loading, and mobile-specific optimizations

import asyncio
import json
import gzip
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class MobileContext:
    device_type: str
    screen_size: str
    network_condition: str
    battery_level: Optional[int] = None
    data_usage_preference: str = "normal"

class MobileOptimizer:
    """Optimizer for mobile dashboard performance and user experience"""
    
    def __init__(self):
        self.initialized = False
        
    async def initialize(self):
        """Initialize mobile optimizer"""
        self.initialized = True
        logger.info("Mobile Optimizer initialized")
    
    async def optimize_for_mobile(self, data: Dict[str, Any], context: MobileContext) -> Dict[str, Any]:
        """Apply mobile optimizations to dashboard data"""
        try:
            optimized_data = data.copy()
            
            # Apply data reduction based on network condition
            if context.network_condition == "slow":
                optimized_data = await self._reduce_data_for_slow_network(optimized_data)
            
            # Apply device-specific optimizations
            if context.device_type == "mobile_phone":
                optimized_data = await self._optimize_for_phone(optimized_data)
            elif context.device_type == "tablet":
                optimized_data = await self._optimize_for_tablet(optimized_data)
            
            # Apply screen size optimizations
            optimized_data = await self._optimize_for_screen_size(optimized_data, context.screen_size)
            
            return optimized_data
            
        except Exception as e:
            logger.error("Failed to optimize for mobile", error=str(e))
            return data
    
    async def _reduce_data_for_slow_network(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce data size for slow network conditions"""
        # Remove non-essential data
        reduced_data = {
            "hero_metrics": data.get("hero_metrics", {}),
            "system_status": data.get("system_status", {}),
            "critical_alerts": data.get("alerts", [])[:3],  # Only top 3 alerts
            "mobile_optimized": True,
            "data_reduced": True
        }
        return reduced_data
    
    async def _optimize_for_phone(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data structure for mobile phones"""
        # Simplify data structures for small screens
        data["ui_mode"] = "mobile_phone"
        data["layout"] = "single_column"
        return data
    
    async def _optimize_for_tablet(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data structure for tablets"""
        data["ui_mode"] = "tablet"
        data["layout"] = "two_column"
        return data
    
    async def _optimize_for_screen_size(self, data: Dict[str, Any], screen_size: str) -> Dict[str, Any]:
        """Apply screen size specific optimizations"""
        data["screen_size"] = screen_size
        
        if screen_size == "small":
            # Reduce text length and simplify layouts
            data["text_optimization"] = "condensed"
        elif screen_size == "large":
            # Can show more detailed information
            data["text_optimization"] = "detailed"
        
        return data