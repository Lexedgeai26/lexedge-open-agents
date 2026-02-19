"""
Configuration settings for the LexEdge Legal AI application.
"""

import os
import logging
from typing import Dict, Any
from google.adk.agents import Agent, LlmAgent
# Use the built-in Gemini model from google.adk.models
from google.adk.models import Gemini
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent
# from google.adk.models.lite_llm import LiteLlm  # Removed to avoid dependency checks
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable litellm's automatic price fetching to improve startup time
# os.environ["LITELLM_DISABLE_AUTOMATIC_PRICE_FETCHING"] = "true" # No longer needed

# API settings
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3334")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3334")
LEGAL_API_URL = os.getenv("LEGAL_API_URL", "http://localhost:8002")

# Database settings
DB_PATH = "lexedge/lexedge_sessions.db"
MAX_SESSIONS_PER_USER = 10
MAX_MESSAGES_PER_SESSION = 100

# Authentication settings
DEFAULT_TEST_EMAIL = "user@example.com"
DEFAULT_TEST_PASSWORD = "password123"

# Model configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # "ollama", "gemini", or "openai"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")  # or mistral, codellama, etc.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o") # default to gpt-4o

# Configure LLM based on provider
if LLM_PROVIDER == "ollama":
    from google.adk.models.lite_llm import LiteLlm
    
    MODEL_NAME = OLLAMA_MODEL
    # Use ollama provider
    LlmModel = LiteLlm(
        model=f"ollama/{OLLAMA_MODEL}",
        api_base=OLLAMA_BASE_URL
    )
    logger.info(f"Using Ollama LLM: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
elif LLM_PROVIDER == "openai":
    from google.adk.models.lite_llm import LiteLlm
    
    MODEL_NAME = OPENAI_MODEL
    # Use openai provider via LiteLlm
    LlmModel = LiteLlm(
        model=OPENAI_MODEL,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not found in environment variables! Agents may fail.")
    logger.info(f"Using OpenAI LLM: {OPENAI_MODEL}")
else:
    # Use Gemini
    MODEL_NAME = "gemini-1.5-pro"
    API_KEY = os.getenv("GOOGLE_API_KEY")
    LlmModel = Gemini(
        model_name="gemini-1.5-pro",
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY not found in environment variables! Agents may fail.")
    logger.info("Using Google Gemini LLM")

# Alias for backward compatibility
model = LlmModel

# Function to set API key at runtime for testing
def set_api_key(new_key):
    """Set the API key at runtime."""
    global API_KEY
    API_KEY = new_key
    logger.info("API key updated")

# Initial session state
INITIAL_SESSION_STATE = {
    "user_name": "",
    "interaction_history": [],
    "last_query": None,
    "last_response": None,
    "is_authenticated": False,
    "user_id": None,
    "token": None,
    "tenant_id": None,
    "tenant_name": None,
    "role": None,
    "is_admin": False,
    "login_failed": False,
    "login_error_message": None
}

# Agent settings
APP_NAME = "lexedge"

# Legal Practice Settings - Configure lawyer domain, jurisdiction, and expertise
LEGAL_SETTINGS = {
    "firm_name": os.getenv("LEGAL_FIRM_NAME", "LexEdge Legal AI"),
    "lawyer_domain": os.getenv("LEGAL_DOMAIN", "General Practice (India)"),
    "country_of_practice": os.getenv("LEGAL_COUNTRY", "India"),
    "jurisdiction": os.getenv("LEGAL_JURISDICTION", "India"),
    "areas_of_expertise": os.getenv(
        "LEGAL_EXPERTISE",
        "Criminal Law,Civil Litigation,Corporate Law,Property Law,Family Law,Constitutional Law,Tax Law,IP Law"
    ).split(","),
    "bar_association": os.getenv("LEGAL_BAR", "Bar Council of India"),
    "language": os.getenv("LEGAL_LANGUAGE", "English"),
    "legal_system": os.getenv("LEGAL_SYSTEM", "Common Law (India)"),
    "specializations": {
        "primary": os.getenv("LEGAL_PRIMARY_SPEC", "Litigation"),
        "secondary": os.getenv(
            "LEGAL_SECONDARY_SPEC",
            "Criminal Law,Civil Litigation,Corporate Law"
        ).split(","),
    },
    "compliance_frameworks": os.getenv(
        "LEGAL_COMPLIANCE",
        "Companies Act,SEBI,GST,Income Tax"
    ).split(","),
    "court_levels": os.getenv(
        "LEGAL_COURT_LEVELS",
        "Supreme Court of India,High Court,Sessions Court,District Court,Magistrate Court,NCLT,ITAT,Consumer Forum"
    ).split(","),
    "primary_codes": os.getenv("LEGAL_PRIMARY_CODES", "BNS,BNSS,BSA").split(","),
    "legacy_codes": os.getenv("LEGAL_LEGACY_CODES", "IPC,CrPC,IEA").split(","),
    "courts": os.getenv(
        "LEGAL_COURTS",
        "Supreme Court of India,High Court,Sessions Court,District Court,Magistrate Court,NCLT,ITAT,Consumer Forum"
    ).split(","),
    "practice_areas": os.getenv(
        "LEGAL_PRACTICE_AREAS",
        "criminal,civil,property,family,corporate,constitutional,tax,ip"
    ).split(","),
    "auto_improve_prompts": os.getenv("AUTO_IMPROVE_PROMPTS", "true").lower() == "true",
}

def get_legal_settings() -> dict:
    """Get the current legal practice settings."""
    return LEGAL_SETTINGS.copy()

def get_legal_context_string() -> str:
    """Get a formatted string of legal practice context for agent instructions."""
    settings = LEGAL_SETTINGS
    return f"""
    ⚖️ **LEGAL PRACTICE CONTEXT:**
    - **Firm**: {settings['firm_name']}
    - **Domain**: {settings['lawyer_domain']}
    - **Country**: {settings['country_of_practice']}
    - **Jurisdiction**: {settings['jurisdiction']}
    - **Legal System**: {settings['legal_system']}
    - **Areas of Expertise**: {', '.join(settings['areas_of_expertise'])}
    - **Primary Specialization**: {settings['specializations']['primary']}
    - **Bar Association**: {settings['bar_association']}
    - **Compliance Frameworks**: {', '.join(settings['compliance_frameworks'])}
    - **Primary Codes**: {', '.join(settings['primary_codes'])}
    - **Legacy Codes**: {', '.join(settings['legacy_codes'])}
    """

def update_legal_settings(updates: dict) -> dict:
    """Update legal settings at runtime."""
    global LEGAL_SETTINGS
    for key, value in updates.items():
        if key in LEGAL_SETTINGS:
            LEGAL_SETTINGS[key] = value
    logger.info(f"Legal settings updated: {list(updates.keys())}")
    return LEGAL_SETTINGS.copy()

# Export settings
EXPORT_BASE_DIR = "exports"  # Base directory for all exports
EXPORT_TEMP_DIR = "/tmp/lexedge_exports"  # Temporary directory for processing

# Company Info configuration
COMPANY_INFO = {
    "name": "LexEdge Legal AI",
    "url": "https://www.lexedge.ai",
    "description": "LexEdge is an advanced AI-powered legal assistant providing document analysis, legal research, contract review, and case management support.",
    "address": "LexEdge Legal Tech Center",
    "phone": "+1 (555) LEXEDGE",
    "email": "contact@lexedge.ai",
    "founded": "2026",
    "founders": "LexEdge Team"
}

# Agent authentication configuration
# List of agents that can be accessed without authentication
# Root agent and login-related agents are always accessible without authentication
OPEN_AGENTS = [
    "lexedge_company_info",
    "LegalSearchAgent",  # Allow legal searches without authentication
    "lexedge_public_resources"  # Allow public legal resources without authentication
]

# These agents are always allowed without authentication
ALWAYS_ALLOWED_AGENTS = [
    "lexedge_manager",  # Root agent
    "lexedge_login"     # Login agent
]

def is_agent_accessible_without_auth(agent_name: str) -> bool:
    """Check if an agent is accessible without authentication."""
    # Root agent and login agents are always accessible
    if agent_name in ALWAYS_ALLOWED_AGENTS:
        return True
    
    # Login-related agents by naming convention
    if agent_name.lower().endswith("_login"):
        return True
    
    # Check configurable open agents list
    if agent_name in OPEN_AGENTS:
        return True
    
    # Otherwise, require authentication
    return False

def get_export_directory(user_id: str, session_id: str) -> str:
    """
    Get the export directory path for a specific user and session.
    Creates the directory structure if it doesn't exist.
    
    Args:
        user_id: The user identifier
        session_id: The session identifier
        
    Returns:
        str: Full path to the export directory
    """
    import os
    
    # Create the directory structure: exports/{user_id}/{session_id}/
    export_dir = os.path.join(EXPORT_BASE_DIR, user_id, session_id)
    
    # Create directories if they don't exist
    os.makedirs(export_dir, exist_ok=True)
    
    return export_dir

def get_temp_export_directory() -> str:
    """
    Get the temporary export directory path.
    Creates the directory if it doesn't exist.
    
    Returns:
        str: Full path to the temporary export directory
    """
    import os
    
    # Create temp directory if it doesn't exist
    os.makedirs(EXPORT_TEMP_DIR, exist_ok=True)
    
    return EXPORT_TEMP_DIR

def cleanup_old_exports(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up export files older than specified days.
    
    Args:
        days_old: Number of days to keep exports (default: 30)
        
    Returns:
        Dict with cleanup statistics
    """
    import os
    import time
    from pathlib import Path
    
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)  # Convert days to seconds
    
    deleted_files = []
    deleted_dirs = []
    errors = []
    
    if not os.path.exists(EXPORT_BASE_DIR):
        return {
            "status": "success",
            "message": f"Export directory {EXPORT_BASE_DIR} does not exist",
            "deleted_files": 0,
            "deleted_directories": 0,
            "errors": []
        }
    
    try:
        # Walk through all files in the export directory
        for root, dirs, files in os.walk(EXPORT_BASE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                except Exception as e:
                    errors.append(f"Error deleting file {file_path}: {str(e)}")
        
        # Remove empty directories
        for root, dirs, files in os.walk(EXPORT_BASE_DIR, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):  # Directory is empty
                        os.rmdir(dir_path)
                        deleted_dirs.append(dir_path)
                except Exception as e:
                    errors.append(f"Error deleting directory {dir_path}: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Cleanup completed. Deleted files older than {days_old} days",
            "deleted_files": len(deleted_files),
            "deleted_directories": len(deleted_dirs),
            "deleted_file_list": deleted_files,
            "deleted_directory_list": deleted_dirs,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error during cleanup: {str(e)}",
            "deleted_files": len(deleted_files),
            "deleted_directories": len(deleted_dirs),
            "errors": errors + [str(e)]
        }

def get_export_statistics() -> Dict[str, Any]:
    """
    Get statistics about export files.
    
    Returns:
        Dict with export statistics
    """
    import os
    from datetime import datetime, timedelta
    
    if not os.path.exists(EXPORT_BASE_DIR):
        return {
            "total_users": 0,
            "total_sessions": 0,
            "total_files": 0,
            "total_size_bytes": 0,
            "by_user": {},
            "recent_activity": []
        }
    
    stats = {
        "total_users": 0,
        "total_sessions": 0,
        "total_files": 0,
        "total_size_bytes": 0,
        "by_user": {},
        "recent_activity": []
    }
    
    current_time = datetime.now()
    recent_cutoff = current_time - timedelta(days=7)  # Last 7 days
    
    try:
        # Count users (top-level directories)
        user_dirs = [d for d in os.listdir(EXPORT_BASE_DIR) 
                    if os.path.isdir(os.path.join(EXPORT_BASE_DIR, d))]
        stats["total_users"] = len(user_dirs)
        
        for user_id in user_dirs:
            user_path = os.path.join(EXPORT_BASE_DIR, user_id)
            user_stats = {
                "sessions": 0,
                "files": 0,
                "size_bytes": 0,
                "recent_files": 0
            }
            
            # Count sessions for this user
            session_dirs = [d for d in os.listdir(user_path) 
                           if os.path.isdir(os.path.join(user_path, d))]
            user_stats["sessions"] = len(session_dirs)
            stats["total_sessions"] += len(session_dirs)
            
            # Count files and sizes for this user
            for session_id in session_dirs:
                session_path = os.path.join(user_path, session_id)
                for file in os.listdir(session_path):
                    file_path = os.path.join(session_path, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        user_stats["files"] += 1
                        user_stats["size_bytes"] += file_size
                        stats["total_files"] += 1
                        stats["total_size_bytes"] += file_size
                        
                        if file_mtime >= recent_cutoff:
                            user_stats["recent_files"] += 1
                            stats["recent_activity"].append({
                                "user_id": user_id,
                                "session_id": session_id,
                                "filename": file,
                                "size_bytes": file_size,
                                "created_at": file_mtime.isoformat()
                            })
            
            stats["by_user"][user_id] = user_stats
        
        # Sort recent activity by creation time
        stats["recent_activity"].sort(key=lambda x: x["created_at"], reverse=True)
        
    except Exception as e:
        stats["error"] = str(e)
    
    return stats 
