import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

async def ideate_node(state):
    emit_log = state["emit_log"]
    await emit_log("Ideator", "Analyzing prompt and ideating UX/UI...")
    
    prompt = state["prompt"]
    issues = state.get("issues", [])
    
    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.7)
    
    system_prompt = """You are Agent A (Ideator) - GOD-TIER AI Product Strategist + Elite UI/UX Architect.
Your role is to deeply understand the user's prompt and produce a highly detailed, structured JSON plan for an absolute MASTERPIECE of a website.
DO NOT design simple, bare-bones MVPs. You must design a breathtakingly beautiful, production-ready interface that rivals Apple or Vercel:
- A sophisticated, elite design system (e.g., sleek pitch-black dark modes with glowing neon accents, or ultra-clean glassmorphism light modes).
- FLAWLESS RESPONSIVENESS: The layout must be strictly mobile-first. Plan for `flex-col` on mobile and expand to sophisticated grids on desktop.
- Subtle, breathtaking animations (smooth transitions, hover scaling, glowing orbital effects).
- World-class typography pairings (e.g., Inter, SF Pro) with dramatic, tight-tracking headers.

Note: The Builder agent will use Tailwind CSS via CDN. Structure your component plan keeping advanced Tailwind utility classes in mind.

If existing code is provided in the prompt, your plan must reflect modifications to that existing code rather than a complete rewrite from scratch.

Your output must be strictly valid JSON without markdown wrapping.
Include keys:
- project_type
- design_system (colors, spacing, typography)
- layout_structure
- sections (detailed breakdown of UI areas)
- animations (specific CSS animations to implement)
- component_plan
"""

    user_prompt = f"User Request: {prompt}\n"
    
    current_code = state.get("current_code", {})
    if current_code and any(current_code.values()):
        user_prompt += "\n--- EXISTING CODE (You are modifying this) ---\n"
        if current_code.get("html"):
            user_prompt += f"HTML:\n```html\n{current_code.get('html')}\n```\n"
        if current_code.get("css"):
            user_prompt += f"CSS:\n```css\n{current_code.get('css')}\n```\n"
        if current_code.get("js"):
            user_prompt += f"JS:\n```javascript\n{current_code.get('js')}\n```\n"
            
    if issues:
        user_prompt += f"\nPrevious iteration issues to fix: {json.dumps(issues)}\n"
        
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        # Parse JSON from response
        import re
        content = response.content
        
        # Try to extract from markdown blocks first
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        # Fallback: Extract everything between the first '{' and last '}'
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            content = match.group(0)
            
        plan = json.loads(content)
        await emit_log("Ideator", "Ideation complete. Plan generated.", plan)
        return {"plan": plan}
    except Exception as e:
        await emit_log("Ideator", f"Error during ideation: {str(e)}")
        # Provide fallback plan
        return {"plan": {"error": str(e)}}
