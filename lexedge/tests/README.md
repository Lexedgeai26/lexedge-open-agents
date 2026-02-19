# LexEdge Test Suite

This folder contains all tests for the LexEdge Universal LLM Task Cancellation System and related functionality.

## 📋 Test Files

### 🔬 Core Functionality Tests

#### `test_universal_cancellation.py`
**Comprehensive test of the universal cancellation system**
- Tests cancellation of ANY agent command (not just specific tools)
- Demonstrates different command types: candidate analysis, company research, salary analysis, job matching
- Validates task manager integration and WebSocket broadcasting
- Shows tool-based cancellation capabilities

```bash
python tests/test_universal_cancellation.py
```

#### `test_job_cancellation.py`
**Focused test of job tool cancellation**
- Tests real-world job tool notifications
- Validates `cancel_pending_processing` flag functionality
- Shows progress vs. completion notification patterns

```bash
python tests/test_job_cancellation.py
```

### 🧩 Component Tests

#### `test_agent_pusher_basic.py`
**Basic agent pusher functionality**
- Tests message pushing to agents
- Validates session creation and management
- Tests batch message operations

```bash
python tests/test_agent_pusher_basic.py
```

#### `test_session_management.py`
**Session service integration**
- Tests session retrieval and management
- Validates current session detection
- Tests multi-user session handling

```bash
python tests/test_session_management.py
```

#### `test_websocket_integration.py`
**WebSocket broadcasting and integration**
- Tests real-time message broadcasting
- Validates different message types (user_message, response, notification)
- Tests WebSocket connection management

```bash
python tests/test_websocket_integration.py
```

### 📖 Documentation Validation

#### `test_documentation_examples.py`
**Validates all documentation examples**
- Tests every code example from the documentation
- Ensures documentation accuracy and functionality
- Validates Quick Reference templates and API examples

```bash
python tests/test_documentation_examples.py
```

## 🚀 Running Tests

### Run All Tests
```bash
# Run all tests sequentially
python tests/test_universal_cancellation.py && \
python tests/test_job_cancellation.py && \
python tests/test_agent_pusher_basic.py && \
python tests/test_session_management.py && \
python tests/test_websocket_integration.py && \
python tests/test_documentation_examples.py
```

### Run Individual Test Categories

**Core Functionality:**
```bash
python tests/test_universal_cancellation.py
python tests/test_job_cancellation.py
```

**Component Tests:**
```bash
python tests/test_agent_pusher_basic.py
python tests/test_session_management.py
python tests/test_websocket_integration.py
```

**Documentation Validation:**
```bash
python tests/test_documentation_examples.py
```

## 🧪 Test Coverage

### ✅ What's Tested

- **Universal Cancellation**: ANY agent command can be cancelled
- **Session-based Control**: Cancellation works by session ID
- **WebSocket Broadcasting**: Real-time UI notifications
- **Task Management**: Asyncio task tracking and cancellation
- **Tool Integration**: Adding cancellation to any tool
- **Priority Logic**: When to cancel vs. continue processing
- **Error Handling**: Robust error scenarios
- **Documentation Examples**: All code examples from docs

### 🎯 Key Test Scenarios

1. **User Types Long Query → Gets Urgent Notification**
   - LLM processing starts for complex query
   - Urgent notification arrives mid-processing
   - LLM task gets cancelled immediately
   - User sees notification in UI

2. **Multiple Command Types**
   - Candidate analysis, company research, salary trends
   - All can be cancelled uniformly
   - Session-based cancellation works for all

3. **Tool Notifications**
   - Email alerts, calendar reminders, security warnings
   - Different priority levels and cancellation logic
   - Progress updates vs. final results

4. **WebSocket Integration**
   - Real-time broadcasting to active clients
   - Different message types (response, notification, etc.)
   - UI integration and feedback

## 🛠 Test Requirements

### Environment Setup
```bash
# Ensure environment variables are loaded
cp .env.example .env  # Edit with your settings

# Install dependencies
pip install -r requirements.txt
```

### Active Sessions Required
Most tests require at least one active user session. You can create one by:
1. Running the LexEdge application
2. Connecting via WebSocket from the UI
3. Starting any agent conversation

### Expected Output
Tests show detailed logging including:
```
🚀 Testing UNIVERSAL LLM Task Cancellation...
🎯 Using session: 949e04b9... (User: chirag)
📊 Active tasks: 1
🛑 Sending interruption: 🚨 URGENT: Critical system alert...
📊 Tasks after cancellation: 0
✅ Successfully cancelled LLM task mid-processing!
```

## 🐛 Troubleshooting

### Common Issues

1. **"No active sessions found"**
   - Start the LexEdge application
   - Connect via WebSocket from UI
   - Create at least one user session

2. **Import errors**
   - Ensure you're running from the project root
   - Check that `lexedge` module is in Python path
   - Verify all dependencies are installed

3. **WebSocket connection issues**
   - Check if WebSocket server is running
   - Verify WebSocket manager is properly initialized
   - Look for connection errors in logs

### Debug Mode
Enable debug logging for detailed output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Tests

Planned additional tests:
- **Performance Tests**: Load testing with many concurrent cancellations
- **Edge Cases**: Network failures, timeout scenarios
- **Security Tests**: Authorization and access control
- **Integration Tests**: End-to-end UI testing
- **Stress Tests**: High-volume message broadcasting

---

**📊 Test Status**: All tests passing ✅  
**🎯 Coverage**: Core functionality, components, documentation  
**🚀 Ready for**: Production deployment and continuous integration 