**NEXT SESSION PROMPT: AI Agent Development**

**Context**: I have a complete portfolio analytics system with comprehensive APIs (recovery analysis, crisis testing, rebalancing strategies, rolling analysis, etc.) and a rule-based chatbot. I want to convert the chatbot into a true AI Agent that uses Claude API with tool-calling capabilities.

**Project Location**: `/Users/ashish/Claude/backtesting/`

**Current System Status**:
- ✅ FastAPI backend with 6+ specialized analytics endpoints 
- ✅ Web interface with chatbot at `http://127.0.0.1:8007/static/chatbot.html`
- ✅ All 3 items from previous session COMPLETE (port fixes, return accuracy, recovery routing)
- ✅ Rule-based `RequestClassifier` in `src/api/claude_routes.py` working but limited

**What I Want**:
Convert from **rule-based routing** to **AI Agent with tool-calling**:
- Current: `if "recovery" in message: call_recovery_api()`  
- Desired: Claude decides which tools to use and orchestrates multiple API calls

**Available Analytics APIs** (to become Agent tools):
- `/api/analyze/recovery-analysis` - Recovery time patterns from drawdowns
- `/api/analyze/crisis-analysis` - Stress testing (2008, 2020, 2022 crises)  
- `/api/rebalancing/analyze-strategies` - Rebalancing strategy optimization
- `/api/analyze/rolling-analysis` - Performance consistency analysis
- `/api/analyze/timeline-analysis` - Age-based recommendations
- `/api/chat/recommend` - Portfolio generation (keep existing)
- `/api/optimize/*` - Modern Portfolio Theory endpoints

**Desired Agent Capabilities**:
1. **Multi-API Orchestration**: "How safe is this for retirement?" → timeline + crisis + recovery analysis
2. **Intelligent Tool Selection**: Claude decides which APIs to call based on question
3. **Synthesis**: Combine results from multiple tools into comprehensive responses
4. **Context Awareness**: Remember previous portfolios and continue conversations

**Technical Approach**:
- Keep existing FastAPI infrastructure and analytics APIs (90% unchanged)
- Replace rule-based `RequestClassifier` with Claude API integration  
- Define analytics endpoints as "tools" with proper descriptions
- Let Claude orchestrate tool calls and synthesize results

**Sprint Planning Questions**:
1. Architecture: Direct Claude API calls vs local Claude server?
2. Tool definitions: How detailed should API descriptions be?
3. Response format: Stream tool calls to user or just final synthesis?
4. Migration: Phase rollout or complete replacement?
5. Testing: How to validate agent behavior vs rule-based system?

**Development Steps Requested**:
1. **Sprint Planning**: Plan the Agent architecture and implementation approach
2. **Tool Integration**: Convert analytics APIs to Claude-callable tools
3. **Agent Implementation**: Replace RequestClassifier with Claude orchestration  
4. **Testing & Validation**: Ensure Agent provides better responses than rule-based system

**Key Files**:
- `src/api/claude_routes.py` - Current rule-based routing (to be enhanced)
- `technical-reference.md` - Updated with current system architecture
- `session-context.md` - Project status and next steps
- `test_recovery_routing_fix.py` - Example of how to test chatbot functionality

Please help me plan and implement this Agent architecture as the next logical evolution of my portfolio analytics system.
