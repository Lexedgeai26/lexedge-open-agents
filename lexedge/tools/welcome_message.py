
from .global_imports import *
from .agents_and_tools import get_available_agents_and_tools


def generate_welcome_message(user_name: str, tenant_name: str) -> Dict[str, Any]:
    """
    Generate a personalized welcome message with agent capabilities overview.
    
    Args:
        user_name (str): User's name from token validation
        tenant_name (str): Tenant name from token validation
        
    Returns:
        dict: {
            "welcome_message": str,
            "formatted_welcome": str,
            "capabilities_overview": dict,
            "quick_start_suggestions": list
        }
    """
    logger.info(f"[WELCOME] Generating welcome message for user: {user_name}, tenant: {tenant_name}")
    
    # Get comprehensive agent and tool information
    agents_info = get_available_agents_and_tools()
    
    # Create personalized welcome message
    welcome_text = f"""Welcome {user_name}! 🎉

Your token has been successfully validated for {tenant_name}. I'm your AI-powered recruiting assistant, ready to help you find the perfect candidates and job opportunities.

🚀 **What I can help you with:**

**👥 Candidate Search & Management:**
• Search for candidates by skills, experience, education, and location
• Get detailed candidate profiles and resume information
• Filter candidates by salary expectations and experience levels
• Use advanced search with Boolean logic and wildcard patterns

**💼 Job Search & Discovery:**
• Browse and search job openings by title, company, and requirements
• Filter jobs by salary ranges and experience requirements
• Find jobs that match specific criteria and locations

**🎯 AI-Powered Matching:**
• Match candidates to job requirements using AI scoring
• Find jobs that best fit a candidate's profile
• Get similarity-based recommendations for both jobs and candidates

**🔍 Advanced Search Capabilities:**
• Natural language search with semantic understanding
• Deep search using vector embeddings for better matches
• Field-specific searches for precise results
• Range searches for salary, experience, and dates

**📊 Platform Features:**
• Real-time notifications and alerts
• Comprehensive company information
• Session management and chat history
• Streaming results for large datasets

**🏃‍♂️ Quick Start Ideas:**
• "Show me all candidates" - Browse available talent
• "Find Python developers" - Search by specific skills
• "List all job openings" - Explore opportunities
• "Match John Smith to jobs" - AI-powered job matching
• "Find candidates with 5+ years experience" - Experience-based search

Just ask me anything in natural language, and I'll help you navigate the platform efficiently!"""

    # Create HTML formatted version
    formatted_welcome = f"""
<div class="welcome-message">
    <h2>🎉 Welcome {user_name}!</h2>
    
    <p>Your token has been successfully validated for <strong>{tenant_name}</strong>. I'm your AI-powered recruiting assistant, ready to help you find the perfect candidates and job opportunities.</p>
    
    <h3>🚀 What I can help you with:</h3>
    
    <div class="capability-section">
        <h4>👥 Candidate Search & Management:</h4>
        <ul>
            <li>Search for candidates by skills, experience, education, and location</li>
            <li>Get detailed candidate profiles and resume information</li>
            <li>Filter candidates by salary expectations and experience levels</li>
            <li>Use advanced search with Boolean logic and wildcard patterns</li>
        </ul>
    </div>
    
    <div class="capability-section">
        <h4>💼 Job Search & Discovery:</h4>
        <ul>
            <li>Browse and search job openings by title, company, and requirements</li>
            <li>Filter jobs by salary ranges and experience requirements</li>
            <li>Find jobs that match specific criteria and locations</li>
        </ul>
    </div>
    
    <div class="capability-section">
        <h4>🎯 AI-Powered Matching:</h4>
        <ul>
            <li>Match candidates to job requirements using AI scoring</li>
            <li>Find jobs that best fit a candidate's profile</li>
            <li>Get similarity-based recommendations for both jobs and candidates</li>
        </ul>
    </div>
    
    <div class="capability-section">
        <h4>🔍 Advanced Search Capabilities:</h4>
        <ul>
            <li>Natural language search with semantic understanding</li>
            <li>Deep search using vector embeddings for better matches</li>
            <li>Field-specific searches for precise results</li>
            <li>Range searches for salary, experience, and dates</li>
        </ul>
    </div>
    
    <div class="capability-section">
        <h4>📊 Platform Features:</h4>
        <ul>
            <li>Real-time notifications and alerts</li>
            <li>Comprehensive company information</li>
            <li>Session management and chat history</li>
            <li>Streaming results for large datasets</li>
        </ul>
    </div>
    
    <div class="quick-start">
        <h4>🏃‍♂️ Quick Start Ideas:</h4>
        <ul>
            <li><em>"Show me all candidates"</em> - Browse available talent</li>
            <li><em>"Find Python developers"</em> - Search by specific skills</li>
            <li><em>"List all job openings"</em> - Explore opportunities</li>
            <li><em>"Match John Smith to jobs"</em> - AI-powered job matching</li>
            <li><em>"Find candidates with 5+ years experience"</em> - Experience-based search</li>
        </ul>
    </div>
    
    <p><strong>Just ask me anything in natural language, and I'll help you navigate the platform efficiently!</strong></p>
</div>
"""

    # Create quick start suggestions for UI buttons
    quick_start_suggestions = [
        {
            "id": "welcome_browse_candidates",
            "caption": "Browse All Candidates",
            "command": "show me all candidates",
            "icon": "user",
            "icon_display": "👥 People",
            "priority": 1,
            "category": "navigation"
        },
        {
            "id": "welcome_browse_jobs",
            "caption": "Browse All Jobs",
            "command": "list all job openings",
            "icon": "briefcase",
            "icon_display": "💼 Jobs",
            "priority": 1,
            "category": "navigation"
        },
        {
            "id": "welcome_search_skills",
            "caption": "Search by Skills",
            "command": "find Python developers",
            "icon": "skills",
            "icon_display": "🛠️ Skills",
            "priority": 2,
            "category": "search"
        },
        {
            "id": "welcome_ai_matching",
            "caption": "AI Matching",
            "command": "match candidates to jobs",
            "icon": "match",
            "icon_display": "🎯 Match",
            "priority": 2,
            "category": "match"
        },
        {
            "id": "welcome_company_info",
            "caption": "Company Info",
            "command": "tell me about the company",
            "icon": "company",
            "icon_display": "🏢 About",
            "priority": 3,
            "category": "info"
        }
    ]
    
    # Create capabilities overview
    capabilities_overview = {
        "total_agents": len(agents_info.get("agents", {})),
        "main_categories": [
            "Candidate Search & Management",
            "Job Search & Discovery", 
            "AI-Powered Matching",
            "Advanced Search Capabilities",
            "Platform Features"
        ],
        "key_features": [
            "Natural language queries",
            "Boolean and wildcard search", 
            "AI-powered matching",
            "Real-time notifications",
            "Vector-based similarity search",
            "Range and filter searches"
        ],
        "available_agents": list(agents_info.get("agents", {}).keys())
    }
    
    logger.info(f"[WELCOME] Generated welcome message for {user_name} from {tenant_name}")
    
    return {
        "welcome_message": welcome_text,
        "formatted_welcome": formatted_welcome,
        "capabilities_overview": capabilities_overview,
        "quick_start_suggestions": quick_start_suggestions
    }
