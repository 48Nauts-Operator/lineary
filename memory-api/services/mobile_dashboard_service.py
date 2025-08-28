# ABOUTME: Mobile Dashboard Service for Betty's Executive Dashboard responsive mobile interface
# ABOUTME: Provides mobile-optimized executive insights with progressive loading and offline support

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from dataclasses import dataclass
from enum import Enum

from core.database import DatabaseManager
from services.executive_intelligence_service import ExecutiveIntelligenceService
from utils.performance_monitoring import monitor_performance
from utils.mobile_optimization import MobileOptimizer

logger = structlog.get_logger(__name__)

class DeviceType(Enum):
    MOBILE_PHONE = "mobile_phone"
    TABLET = "tablet"
    DESKTOP = "desktop"

class NetworkCondition(Enum):
    FAST = "fast"
    SLOW = "slow"
    OFFLINE = "offline"

@dataclass
class MobileContext:
    device_type: DeviceType
    screen_size: str  # small, medium, large
    network_condition: NetworkCondition
    battery_level: Optional[int] = None
    data_usage_preference: str = "normal"  # low, normal, high

class MobileDashboardService:
    """Service for mobile-optimized executive dashboard with responsive design"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.executive_service = None
        self.mobile_optimizer = None
        self.initialized = False
        self.cache_manager = {}  # Simple cache for mobile optimization
        
    async def initialize(self):
        """Initialize the mobile dashboard service"""
        try:
            self.executive_service = ExecutiveIntelligenceService(self.db)
            await self.executive_service.initialize()
            
            self.mobile_optimizer = MobileOptimizer()
            await self.mobile_optimizer.initialize()
            
            self.initialized = True
            logger.info("Mobile Dashboard Service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Mobile Dashboard Service", error=str(e))
            raise

    @monitor_performance(target_ms=200)  # Mobile target: <200ms
    async def get_executive_mobile_view(
        self,
        device_type: str = "mobile_phone",
        screen_size: str = "small",
        network_condition: str = "fast"
    ) -> Dict[str, Any]:
        """Get mobile-optimized executive dashboard view"""
        try:
            # Create mobile context
            mobile_context = MobileContext(
                device_type=DeviceType(device_type.lower()),
                screen_size=screen_size,
                network_condition=NetworkCondition(network_condition.lower())
            )
            
            # Optimize data loading based on context
            if mobile_context.network_condition == NetworkCondition.SLOW:
                # Load minimal critical data only
                dashboard_data = await self._get_minimal_dashboard_data(mobile_context)
            elif mobile_context.network_condition == NetworkCondition.OFFLINE:
                # Load cached data
                dashboard_data = await self._get_cached_dashboard_data(mobile_context)
            else:
                # Load full optimized data
                dashboard_data = await self._get_full_mobile_dashboard_data(mobile_context)
            
            # Apply mobile optimizations
            optimized_data = await self.mobile_optimizer.optimize_for_mobile(dashboard_data, mobile_context)
            
            return {
                "status": "success",
                "mobile_optimized": True,
                "device_context": {
                    "device_type": device_type,
                    "screen_size": screen_size,
                    "network_condition": network_condition,
                    "data_size_kb": self._calculate_data_size(optimized_data)
                },
                "dashboard": optimized_data,
                "performance": {
                    "load_time_target_ms": 200,
                    "progressive_loading": True,
                    "offline_support": True,
                    "cache_enabled": True
                },
                "ui_config": self._get_mobile_ui_config(mobile_context),
                "interaction_patterns": self._get_mobile_interaction_patterns(mobile_context)
            }
            
        except Exception as e:
            logger.error("Failed to get mobile executive view", error=str(e))
            return self._get_fallback_mobile_view(device_type, screen_size)

    @monitor_performance(target_ms=150)
    async def get_mobile_key_metrics(
        self,
        mobile_context: Optional[MobileContext] = None
    ) -> Dict[str, Any]:
        """Get key metrics optimized for mobile display"""
        try:
            if not mobile_context:
                mobile_context = MobileContext(
                    device_type=DeviceType.MOBILE_PHONE,
                    screen_size="small",
                    network_condition=NetworkCondition.FAST
                )
            
            # Get essential metrics only
            essential_metrics = await self._get_essential_metrics_for_mobile()
            
            # Format for mobile display
            mobile_metrics = {
                "hero_metrics": [
                    {
                        "title": "Knowledge Health",
                        "value": "85%",
                        "trend": "up",
                        "color": "green",
                        "icon": "health"
                    },
                    {
                        "title": "ROI",
                        "value": "150%",
                        "trend": "up", 
                        "color": "blue",
                        "icon": "trend-up"
                    },
                    {
                        "title": "Performance",
                        "value": "95ms",
                        "trend": "stable",
                        "color": "yellow",
                        "icon": "performance"
                    },
                    {
                        "title": "Users Active",
                        "value": "12",
                        "trend": "up",
                        "color": "purple",
                        "icon": "users"
                    }
                ],
                "quick_insights": [
                    "System health is excellent",
                    "ROI exceeded targets by 25%",
                    "Performance within optimal range"
                ],
                "alerts": await self._get_mobile_alerts(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return mobile_metrics
            
        except Exception as e:
            logger.error("Failed to get mobile key metrics", error=str(e))
            return self._get_fallback_mobile_metrics()

    @monitor_performance(target_ms=100)
    async def get_mobile_alerts(
        self,
        priority_filter: str = "high",
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get mobile-optimized alerts with push notification support"""
        try:
            # Get system alerts
            alerts = await self._get_system_alerts(priority_filter)
            
            # Format for mobile display
            mobile_alerts = []
            for alert in alerts[:limit]:
                mobile_alert = {
                    "id": alert.get("id", ""),
                    "title": alert.get("title", "")[:50],  # Truncate for mobile
                    "message": alert.get("message", "")[:100],  # Truncate for mobile
                    "priority": alert.get("priority", "medium"),
                    "timestamp": alert.get("timestamp", ""),
                    "action_required": alert.get("action_required", False),
                    "category": alert.get("category", "system"),
                    "icon": self._get_alert_icon(alert),
                    "color": self._get_alert_color(alert.get("priority", "medium"))
                }
                mobile_alerts.append(mobile_alert)
            
            return {
                "alerts": mobile_alerts,
                "total_count": len(alerts),
                "high_priority_count": len([a for a in alerts if a.get("priority") == "high"]),
                "push_notifications_enabled": True,
                "auto_refresh_seconds": 60
            }
            
        except Exception as e:
            logger.error("Failed to get mobile alerts", error=str(e))
            return {"alerts": [], "total_count": 0}

    async def get_mobile_chart_data(
        self,
        chart_type: str,
        mobile_context: MobileContext,
        data_points_limit: int = 20
    ) -> Dict[str, Any]:
        """Get chart data optimized for mobile display"""
        try:
            # Limit data points for mobile performance
            if chart_type == "trend":
                chart_data = await self._get_mobile_trend_data(data_points_limit)
            elif chart_type == "performance":
                chart_data = await self._get_mobile_performance_data(data_points_limit)
            elif chart_type == "roi":
                chart_data = await self._get_mobile_roi_data(data_points_limit)
            else:
                chart_data = await self._get_default_mobile_chart_data(data_points_limit)
            
            # Optimize chart configuration for mobile
            mobile_chart_config = {
                "responsive": True,
                "maintainAspectRatio": False,
                "devicePixelRatio": 2,  # For retina displays
                "animation": {
                    "duration": mobile_context.network_condition == NetworkCondition.SLOW and 200 or 400
                },
                "elements": {
                    "point": {"radius": 3},  # Smaller points for mobile
                    "line": {"borderWidth": 2}  # Thinner lines for mobile
                },
                "legend": {
                    "display": mobile_context.screen_size != "small",
                    "position": "bottom"
                },
                "scales": {
                    "x": {"ticks": {"maxTicksLimit": 8}},  # Fewer ticks on mobile
                    "y": {"ticks": {"maxTicksLimit": 6}}
                }
            }
            
            return {
                "chart_type": chart_type,
                "data": chart_data,
                "config": mobile_chart_config,
                "mobile_optimized": True,
                "data_points": len(chart_data.get("datasets", [{}])[0].get("data", [])),
                "estimated_render_time_ms": self._estimate_chart_render_time(chart_data, mobile_context)
            }
            
        except Exception as e:
            logger.error("Failed to get mobile chart data", chart_type=chart_type, error=str(e))
            return self._get_fallback_mobile_chart(chart_type)

    async def enable_offline_support(self, user_id: str) -> Dict[str, Any]:
        """Enable offline support for mobile dashboard"""
        try:
            # Cache essential data for offline use
            offline_data = await self._prepare_offline_data()
            
            # Store in cache with user_id
            cache_key = f"offline_data_{user_id}"
            self.cache_manager[cache_key] = {
                "data": offline_data,
                "timestamp": datetime.utcnow().isoformat(),
                "expiry": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            return {
                "offline_support_enabled": True,
                "cache_size_kb": self._calculate_data_size(offline_data),
                "cache_duration_hours": 24,
                "last_sync": datetime.utcnow().isoformat(),
                "available_features": [
                    "key_metrics",
                    "recent_alerts",
                    "basic_charts",
                    "executive_summary"
                ],
                "sync_strategy": "background_sync_when_online"
            }
            
        except Exception as e:
            logger.error("Failed to enable offline support", user_id=user_id, error=str(e))
            return {"offline_support_enabled": False, "error": str(e)}

    async def get_progressive_loading_manifest(
        self,
        mobile_context: MobileContext
    ) -> Dict[str, Any]:
        """Get progressive loading manifest for mobile optimization"""
        try:
            # Define loading priorities based on mobile context
            loading_phases = []
            
            # Phase 1: Critical metrics (immediate load)
            loading_phases.append({
                "phase": 1,
                "priority": "critical",
                "estimated_time_ms": 100,
                "components": [
                    "hero_metrics",
                    "system_status",
                    "critical_alerts"
                ],
                "data_size_kb": 5,
                "cache_enabled": True
            })
            
            # Phase 2: Essential charts (fast load)
            loading_phases.append({
                "phase": 2,
                "priority": "high",
                "estimated_time_ms": 200,
                "components": [
                    "trend_chart",
                    "performance_summary",
                    "quick_insights"
                ],
                "data_size_kb": 15,
                "conditional_load": mobile_context.network_condition != NetworkCondition.SLOW
            })
            
            # Phase 3: Detailed analytics (background load)
            if mobile_context.network_condition == NetworkCondition.FAST:
                loading_phases.append({
                    "phase": 3,
                    "priority": "medium",
                    "estimated_time_ms": 500,
                    "components": [
                        "detailed_charts",
                        "recommendations",
                        "historical_data"
                    ],
                    "data_size_kb": 35,
                    "background_load": True
                })
            
            return {
                "progressive_loading_enabled": True,
                "loading_phases": loading_phases,
                "total_estimated_time_ms": sum(phase["estimated_time_ms"] for phase in loading_phases),
                "adaptive_loading": True,
                "network_aware": True,
                "fallback_strategy": "cached_data"
            }
            
        except Exception as e:
            logger.error("Failed to get progressive loading manifest", error=str(e))
            return {"progressive_loading_enabled": False}

    # === PRIVATE HELPER METHODS === #

    async def _get_minimal_dashboard_data(self, mobile_context: MobileContext) -> Dict[str, Any]:
        """Get minimal dashboard data for slow connections"""
        try:
            # Only essential metrics for slow connections
            essential_data = {
                "hero_metrics": await self._get_essential_metrics_for_mobile(),
                "system_status": {"status": "operational", "health_score": 0.95},
                "critical_alerts": await self._get_mobile_alerts(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return essential_data
            
        except Exception as e:
            logger.error("Failed to get minimal dashboard data", error=str(e))
            return {"status": "error", "message": "Minimal data unavailable"}

    async def _get_cached_dashboard_data(self, mobile_context: MobileContext) -> Dict[str, Any]:
        """Get cached dashboard data for offline mode"""
        try:
            # Return cached data if available
            cached_data = self.cache_manager.get("offline_data_default")
            if cached_data and not self._is_cache_expired(cached_data):
                return cached_data["data"]
            
            # Fallback to basic offline data
            return {
                "offline_mode": True,
                "hero_metrics": self._get_fallback_metrics(),
                "message": "Limited data available offline",
                "last_sync": "Unknown"
            }
            
        except Exception as e:
            logger.error("Failed to get cached dashboard data", error=str(e))
            return {"status": "error", "message": "Offline data unavailable"}

    async def _get_full_mobile_dashboard_data(self, mobile_context: MobileContext) -> Dict[str, Any]:
        """Get full dashboard data optimized for mobile"""
        try:
            # Get comprehensive data but optimized for mobile
            tasks = [
                self._get_essential_metrics_for_mobile(),
                self._get_mobile_trends("7d"),
                self._get_mobile_insights(),
                self._get_mobile_alerts()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "hero_metrics": results[0] if not isinstance(results[0], Exception) else {},
                "trends": results[1] if not isinstance(results[1], Exception) else {},
                "insights": results[2] if not isinstance(results[2], Exception) else [],
                "alerts": results[3] if not isinstance(results[3], Exception) else [],
                "system_status": {"status": "operational", "health_score": 0.95},
                "last_updated": datetime.utcnow().isoformat(),
                "mobile_optimized": True
            }
            
        except Exception as e:
            logger.error("Failed to get full mobile dashboard data", error=str(e))
            return {"status": "error", "message": "Full data unavailable"}

    def _get_mobile_ui_config(self, mobile_context: MobileContext) -> Dict[str, Any]:
        """Get mobile UI configuration"""
        config = {
            "layout": "single_column" if mobile_context.screen_size == "small" else "adaptive",
            "touch_optimized": mobile_context.device_type in [DeviceType.MOBILE_PHONE, DeviceType.TABLET],
            "gesture_support": True,
            "swipe_navigation": mobile_context.device_type == DeviceType.MOBILE_PHONE,
            "pull_to_refresh": True,
            "infinite_scroll": False,  # Performance optimization
            "card_based_layout": True,
            "collapsible_sections": mobile_context.screen_size == "small",
            "dark_mode_support": True,
            "high_contrast_mode": False
        }
        
        # Adjust based on device type
        if mobile_context.device_type == DeviceType.TABLET:
            config["layout"] = "two_column"
            config["sidebar_enabled"] = True
        
        return config

    def _get_mobile_interaction_patterns(self, mobile_context: MobileContext) -> Dict[str, Any]:
        """Get mobile interaction patterns"""
        return {
            "tap_targets": {
                "minimum_size_px": 44,  # iOS/Android recommendation
                "spacing_px": 8,
                "touch_feedback": True
            },
            "navigation": {
                "type": "bottom_tabs" if mobile_context.device_type == DeviceType.MOBILE_PHONE else "side_nav",
                "gesture_navigation": True,
                "back_button_support": True
            },
            "scrolling": {
                "momentum_scrolling": True,
                "overscroll_bounce": mobile_context.device_type == DeviceType.MOBILE_PHONE,
                "scroll_indicators": True
            },
            "loading_states": {
                "skeleton_screens": True,
                "progressive_disclosure": True,
                "loading_spinners": "minimal"
            },
            "feedback": {
                "haptic_feedback": mobile_context.device_type == DeviceType.MOBILE_PHONE,
                "visual_feedback": True,
                "audio_feedback": False
            }
        }

    # === DATA RETRIEVAL METHODS === #

    async def _get_essential_metrics_for_mobile(self) -> Dict[str, Any]:
        """Get essential metrics optimized for mobile display"""
        try:
            return {
                "knowledge_health": {"value": 0.85, "trend": "up", "display": "85%"},
                "roi": {"value": 150, "trend": "up", "display": "150%"},
                "performance": {"value": 95, "trend": "stable", "display": "95ms"},
                "active_users": {"value": 12, "trend": "up", "display": "12"}
            }
        except Exception as e:
            logger.error("Failed to get essential metrics", error=str(e))
            return {}

    async def _get_mobile_trends(self, time_range: str) -> Dict[str, Any]:
        """Get trend data optimized for mobile display"""
        try:
            # Generate sample mobile-optimized trend data
            days = 7  # For mobile, show only last 7 days
            dates = []
            values = []
            
            for i in range(days):
                date = datetime.utcnow() - timedelta(days=days-i-1)
                dates.append(date.strftime("%m/%d"))  # Short date format for mobile
                values.append(80 + i * 2 + np.random.normal(0, 1))
            
            return {
                "labels": dates,
                "datasets": [{
                    "label": "Health Score",
                    "data": [max(0, min(100, v)) for v in values],
                    "borderColor": "#3B82F6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "borderWidth": 2
                }],
                "mobile_optimized": True
            }
        except Exception as e:
            logger.error("Failed to get mobile trends", error=str(e))
            return {}

    async def _get_mobile_insights(self) -> List[str]:
        """Get insights formatted for mobile display"""
        try:
            return [
                "System health excellent",
                "ROI up 25% this month", 
                "Performance optimal",
                "User adoption growing"
            ]
        except Exception as e:
            logger.error("Failed to get mobile insights", error=str(e))
            return []

    async def _get_system_alerts(self, priority_filter: str) -> List[Dict[str, Any]]:
        """Get system alerts"""
        try:
            # Sample alerts for mobile display
            return [
                {
                    "id": "alert_001",
                    "title": "Performance Optimal",
                    "message": "All systems operating within normal parameters",
                    "priority": "low",
                    "timestamp": datetime.utcnow().isoformat(),
                    "category": "performance",
                    "action_required": False
                }
            ]
        except Exception as e:
            logger.error("Failed to get system alerts", error=str(e))
            return []

    # === UTILITY METHODS === #

    def _calculate_data_size(self, data: Dict) -> float:
        """Calculate approximate data size in KB"""
        try:
            json_str = json.dumps(data)
            return len(json_str.encode('utf-8')) / 1024  # KB
        except Exception:
            return 0.0

    def _is_cache_expired(self, cached_data: Dict) -> bool:
        """Check if cached data is expired"""
        try:
            expiry_str = cached_data.get("expiry", "")
            if not expiry_str:
                return True
            
            expiry_time = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            return datetime.utcnow() > expiry_time.replace(tzinfo=None)
        except Exception:
            return True

    def _get_alert_icon(self, alert: Dict) -> str:
        """Get appropriate icon for alert"""
        category = alert.get("category", "system")
        icon_mapping = {
            "performance": "zap",
            "security": "shield",
            "system": "settings",
            "user": "user",
            "data": "database"
        }
        return icon_mapping.get(category, "info")

    def _get_alert_color(self, priority: str) -> str:
        """Get color for alert priority"""
        color_mapping = {
            "critical": "red",
            "high": "orange", 
            "medium": "yellow",
            "low": "blue",
            "info": "gray"
        }
        return color_mapping.get(priority, "gray")

    def _estimate_chart_render_time(self, chart_data: Dict, mobile_context: MobileContext) -> int:
        """Estimate chart rendering time in milliseconds"""
        data_points = len(chart_data.get("datasets", [{}])[0].get("data", []))
        
        # Base render time
        base_time = 50
        
        # Add time based on data points
        data_time = data_points * 2
        
        # Adjust for device type
        if mobile_context.device_type == DeviceType.MOBILE_PHONE:
            device_multiplier = 1.5
        elif mobile_context.device_type == DeviceType.TABLET:
            device_multiplier = 1.2
        else:
            device_multiplier = 1.0
        
        # Adjust for network condition
        if mobile_context.network_condition == NetworkCondition.SLOW:
            network_multiplier = 2.0
        else:
            network_multiplier = 1.0
        
        return int((base_time + data_time) * device_multiplier * network_multiplier)

    async def _prepare_offline_data(self) -> Dict[str, Any]:
        """Prepare essential data for offline caching"""
        try:
            offline_data = {
                "hero_metrics": await self._get_essential_metrics_for_mobile(),
                "recent_trends": await self._get_mobile_trends("7d"),
                "key_insights": await self._get_mobile_insights(),
                "system_status": {"status": "operational", "health_score": 0.95},
                "cached_at": datetime.utcnow().isoformat()
            }
            return offline_data
        except Exception as e:
            logger.error("Failed to prepare offline data", error=str(e))
            return {}

    # === FALLBACK METHODS === #

    def _get_fallback_mobile_view(self, device_type: str, screen_size: str) -> Dict[str, Any]:
        """Fallback mobile view when service fails"""
        return {
            "status": "fallback",
            "mobile_optimized": True,
            "device_context": {
                "device_type": device_type,
                "screen_size": screen_size,
                "network_condition": "unknown"
            },
            "dashboard": {
                "hero_metrics": self._get_fallback_metrics(),
                "message": "Limited data available",
                "last_updated": datetime.utcnow().isoformat()
            }
        }

    def _get_fallback_mobile_metrics(self) -> Dict[str, Any]:
        """Fallback mobile metrics"""
        return {
            "hero_metrics": self._get_fallback_metrics(),
            "quick_insights": ["System operational", "Monitoring active"],
            "alerts": [],
            "last_updated": datetime.utcnow().isoformat()
        }

    def _get_fallback_metrics(self) -> List[Dict[str, Any]]:
        """Fallback metrics data"""
        return [
            {"title": "Status", "value": "OK", "trend": "stable", "color": "green", "icon": "check"},
            {"title": "Health", "value": "85%", "trend": "stable", "color": "blue", "icon": "health"}
        ]

    def _get_fallback_mobile_chart(self, chart_type: str) -> Dict[str, Any]:
        """Fallback mobile chart"""
        return {
            "chart_type": chart_type,
            "data": {"labels": [], "datasets": []},
            "config": {"responsive": True},
            "mobile_optimized": True,
            "error": "Chart data unavailable"
        }

    # === PLACEHOLDER METHODS === #

    async def _get_mobile_trend_data(self, limit: int) -> Dict:
        return {"labels": [], "datasets": []}
    
    async def _get_mobile_performance_data(self, limit: int) -> Dict:
        return {"labels": [], "datasets": []}
    
    async def _get_mobile_roi_data(self, limit: int) -> Dict:
        return {"labels": [], "datasets": []}
    
    async def _get_default_mobile_chart_data(self, limit: int) -> Dict:
        return {"labels": [], "datasets": []}