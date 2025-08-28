# ABOUTME: Extensions for Pattern Success Prediction Engine - completing missing ROI and strategy methods
# ABOUTME: This file contains the remaining implementations for complete ML-powered prediction capabilities

# This file contains the remaining method implementations that should be integrated into the main file
# Due to file size constraints, these are provided separately for integration

async def _identify_intangible_benefits(
    self, 
    pattern: KnowledgeItem, 
    organization: Organization, 
    context: PatternContext
) -> List[str]:
    """Identify intangible benefits based on pattern and context"""
    intangible_benefits = []
    
    # Security patterns provide security benefits
    if any(tag in ['security', 'authentication', 'encryption'] for tag in pattern.tags):
        intangible_benefits.extend([
            "Enhanced security posture",
            "Reduced compliance risk",
            "Improved customer trust"
        ])
    
    # Code quality patterns
    if any(tag in ['testing', 'architecture', 'design-patterns'] for tag in pattern.tags):
        intangible_benefits.extend([
            "Better code maintainability",
            "Reduced technical debt",
            "Improved developer experience"
        ])
    
    # Performance patterns
    if any(tag in ['performance', 'optimization', 'caching'] for tag in pattern.tags):
        intangible_benefits.extend([
            "Enhanced user experience",
            "Improved system reliability",
            "Better scalability potential"
        ])
    
    # Team and process benefits
    if context.team_experience in ['medium', 'high']:
        intangible_benefits.extend([
            "Improved team knowledge sharing",
            "Enhanced development velocity",
            "Better cross-team collaboration"
        ])
    
    # Organization-specific benefits
    if organization.maturity_level in ['mature', 'advanced']:
        intangible_benefits.extend([
            "Strengthened engineering culture",
            "Improved innovation capacity"
        ])
    
    return list(set(intangible_benefits))  # Remove duplicates

# All the strategy-related methods are in the previous implementations
# These should be integrated into the main PatternSuccessPredictionEngine class