"""
Context manager for LexEdge Legal AI agents.

This module provides context preservation between agent transfers, ensuring that
important legal case information is maintained when switching between different sub-agents.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class AgentContextManager:
    """
    Context manager for preserving context between agent transfers.
    
    This class handles storing and retrieving context for each agent,
    ensuring that important information is maintained when switching
    between different sub-agents.
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self._agent_contexts = {}
        self._global_context = {}
        self._conversation_history = []
        self._api_responses = {}
        
    def store_context(self, agent_name: str, context_data: Dict[str, Any]) -> None:
        """
        Store context data for a specific agent.
        
        Args:
            agent_name: The name of the agent
            context_data: The context data to store
        """
        # Store the context for this agent in the global context
        if agent_name not in self._global_context:
            self._global_context[agent_name] = {}
            
        self._global_context[agent_name] = context_data
        logger.info(f"Stored context for agent {agent_name}")
        
    def get_context(self, agent_name: str) -> Dict[str, Any]:
        """
        Get context data for a specific agent.
        
        Args:
            agent_name: The name of the agent
            
        Returns:
            Dict[str, Any]: The context data for the agent or empty dict if not found
        """
        return self._global_context.get(agent_name, {})
        
    def update_context(self, agent_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update context data for a specific agent.
        
        Args:
            agent_name: The name of the agent
            updates: The updates to apply to the context
            
        Returns:
            Dict[str, Any]: The updated context data
        """
        current_context = self.get_context(agent_name)
        current_context.update(updates)
        self.store_context(agent_name, current_context)
        return current_context
        
    def clear_context(self, agent_name: Optional[str] = None) -> None:
        """
        Clear context data for a specific agent or all agents.
        
        Args:
            agent_name: Optional name of the agent to clear context for
                        If None, clears all context
        """
        if agent_name is None:
            # Clear all context
            self._global_context = {}
            logger.info("Cleared all context")
        elif agent_name in self._global_context:
            # Clear context for specific agent
            del self._global_context[agent_name]
            logger.info(f"Cleared context for agent {agent_name}")
            
    def transfer_context(self, from_agent: str, to_agent: str, 
                        keys: Optional[List[str]] = None) -> None:
        """
        Transfer specific context data from one agent to another.
        
        Args:
            from_agent: The source agent name
            to_agent: The destination agent name
            keys: Optional list of keys to transfer
                 If None, transfers all context data
        """
        source_context = self.get_context(from_agent)
        if not source_context:
            return
            
        # Get current destination context
        dest_context = self.get_context(to_agent)
        
        # Transfer specified keys or all keys
        if keys is not None:
            for key in keys:
                if key in source_context:
                    dest_context[key] = source_context[key]
        else:
            dest_context.update(source_context)
            
        # Store updated destination context
        self.store_context(to_agent, dest_context)
        logger.info(f"Transferred context from {from_agent} to {to_agent}")
        
    def get_all_contexts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all context data.
        
        Returns:
            Dict[str, Dict[str, Any]]: All context data
        """
        return self._global_context
    
    def store_api_response(self, agent_name: str, response_type: str, response_data: Any) -> None:
        """
        Store an API response in the context.
        
        Args:
            agent_name: The name of the agent that received the response
            response_type: The type of response (e.g., "candidate", "job", "company")
            response_data: The response data to store
        """
        if agent_name not in self._api_responses:
            self._api_responses[agent_name] = {}
            
        self._api_responses[agent_name][response_type] = response_data
        
        # Also store in the global context for easy access
        self.update_context("shared", {
            f"current_{response_type}": response_data
        })
        
        # Also store in the agent-specific context
        self.update_context(agent_name, {
            f"current_{response_type}": response_data
        })
        
        logger.info(f"Stored {response_type} API response for agent {agent_name}")
    
    def get_api_response(self, response_type: str, agent_name: Optional[str] = None) -> Any:
        """
        Get an API response from the context.
        
        Args:
            response_type: The type of response to get (e.g., "candidate", "job", "company")
            agent_name: Optional name of the agent to get the response for
                       If None, checks all agents
                       
        Returns:
            Any: The API response data or None if not found
        """
        # Try to get from shared context first
        shared_context = self.get_context("shared")
        key = f"current_{response_type}"
        if key in shared_context:
            return shared_context[key]
            
        # If agent name is provided, check that agent's context
        if agent_name is not None:
            if agent_name in self._api_responses and response_type in self._api_responses[agent_name]:
                return self._api_responses[agent_name][response_type]
                
            agent_context = self.get_context(agent_name)
            if key in agent_context:
                return agent_context[key]
                
        # Check all agents
        for agent, responses in self._api_responses.items():
            if response_type in responses:
                return responses[response_type]
                
        return None
    
    def add_conversation_entry(self, agent_name: str, user_message: str, agent_response: str) -> None:
        """
        Add an entry to the conversation history.
        
        Args:
            agent_name: The name of the agent that processed the message
            user_message: The user's message
            agent_response: The agent's response
        """
        entry = {
            "timestamp": time.time(),
            "agent_name": agent_name,
            "user_message": user_message,
            "agent_response": agent_response
        }
        self._conversation_history.append(entry)
        
        # Keep only the last 10 entries to avoid excessive memory usage
        if len(self._conversation_history) > 10:
            self._conversation_history = self._conversation_history[-10:]
            
        logger.info(f"Added conversation entry for agent {agent_name}")
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            limit: Optional limit on the number of entries to return
                 If None, returns all entries
                 
        Returns:
            List[Dict[str, Any]]: The conversation history
        """
        if limit is not None:
            return self._conversation_history[-limit:]
        return self._conversation_history
    
    def get_last_n_messages(self, n: int = 1) -> List[Dict[str, Any]]:
        """
        Get the last N messages from the conversation history.
        
        Args:
            n: Number of messages to retrieve
            
        Returns:
            List[Dict[str, Any]]: The last N messages
        """
        return self._conversation_history[-n:] if self._conversation_history else []
        
    def store_case_context(self, case_data: Dict[str, Any]) -> None:
        """
        Store legal case data in the context.
        
        This is a specialized method for storing case information that might be
        needed across different legal agents.
        
        Args:
            case_data: The case data to store
        """
        self.store_context("CaseProfile", {"data": case_data})
        # Also store in shared context for cross-agent access
        self.update_context("shared", {"current_case": case_data})
        logger.info(f"Stored case context for: {case_data.get('case_name', 'Unknown')}")
        
    def get_case_context(self) -> Dict[str, Any]:
        """
        Get legal case data from the context.
        
        Returns:
            Dict[str, Any]: The case data or empty dict if not found
        """
        case_profile = self.get_context("CaseProfile")
        return case_profile.get("data", {}) if case_profile else {}
    
    def update_case_context(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update legal case data in the context.
        
        Args:
            updates: The updates to apply to the case data
            
        Returns:
            Dict[str, Any]: The updated case data
        """
        current_case = self.get_case_context()
        current_case.update(updates)
        self.store_case_context(current_case)
        return current_case
    
    def store_legal_research(self, research_data: Dict[str, Any]) -> None:
        """
        Store legal research findings in the context.
        
        Args:
            research_data: The research data to store
        """
        self.update_context("LegalResearchAgent", {"last_research": research_data})
        logger.info(f"Stored legal research: {research_data.get('topic', 'Unknown')}")
    
    def get_legal_research(self) -> Dict[str, Any]:
        """
        Get legal research findings from the context.
        
        Returns:
            Dict[str, Any]: The research data or empty dict if not found
        """
        research_context = self.get_context("LegalResearchAgent")
        return research_context.get("last_research", {}) if research_context else {}
    
    def store_document_analysis(self, analysis_data: Dict[str, Any]) -> None:
        """
        Store document analysis results in the context.
        
        Args:
            analysis_data: The analysis data to store
        """
        self.update_context("LegalDocsAgent", {"last_analysis": analysis_data})
        logger.info(f"Stored document analysis: {analysis_data.get('document_type', 'Unknown')}")
    
    def get_document_analysis(self) -> Dict[str, Any]:
        """
        Get document analysis results from the context.
        
        Returns:
            Dict[str, Any]: The analysis data or empty dict if not found
        """
        docs_context = self.get_context("LegalDocsAgent")
        return docs_context.get("last_analysis", {}) if docs_context else {}

# Create a singleton instance
agent_context_manager = AgentContextManager()
