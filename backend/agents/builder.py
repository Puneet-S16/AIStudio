import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

async def build_node(state):
    emit_log = state["emit_log"]
    emit_code = state["emit_code"]
    emit_preview_reload = state["emit_preview_reload"]
    
    await emit_log("Builder", "Generating frontend code based on the plan...")
    
    plan = state["plan"]
    preview_dir = state["preview_dir"]
    
    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.2)
    
    system_prompt = """You are Agent B (Builder) - Elite Autonomous Frontend Engineer.
You consume the Ideator's structured JSON plan and generate exceptionally high-quality, WOW-factor frontend code.

Do NOT output JSON. You must output EXACTLY three markdown code blocks: one for HTML, one for CSS, and one for JavaScript.
Format your output exactly like this:

```html
<!-- your html code here -->
```

```css
/* your css code here */
```

```javascript
// your js code here
```

ABSOLUTE RULES (YOU ARE A GOD-TIER SENIOR DEVELOPER, ACT LIKE IT):
- NEVER build a simple, boring MVP. Ensure the UI is an absolute MASTERPIECE of art that rivals Apple or Vercel's marketing pages. It must be breathtakingly beautiful, highly polished, and functionally perfect.
- You MUST use **Tailwind CSS** for 95% of your styling. The runtime environment already has Tailwind CSS injected via CDN.
- FLAWLESS RESPONSIVENESS IS MANDATORY: You must use mobile-first design. Everything must look perfect on mobile (`flex-col`, `w-full`, `p-4`) and elegantly expand on desktop (`md:flex-row`, `md:grid-cols-3`, `lg:p-12`). NEVER use fixed widths that break on small screens.
- Use Tailwind utility classes extensively for responsive grids, typography (`text-4xl md:text-6xl`, `font-extrabold`, `tracking-tight`), and spacing.
- **Material Icons** are available. Use them perfectly aligned with text.
- Your `styles.css` block should ONLY contain custom styles that Tailwind cannot easily handle (e.g., highly complex keyframe animations, glowing orbital effects, or deeply customized scrollbars). 
- IMPORTANT AESTHETIC: Design a breathtakingly professional, elite enterprise interface. Use subtle, incredibly sleek gradients (e.g., a dark mode with `bg-black text-white` and subtle `bg-gradient-to-tr from-gray-900 to-black` with glowing accent borders, OR an ultra-clean light mode with glassmorphism). Make it a piece of art!
- If you are provided with existing code, you must MODIFY that code to implement the new plan, keeping the structure intact rather than generating from scratch.
- JS must be flawless, modular, and handle complex DOM manipulations effortlessly with smooth transitions.
"""
    
    user_prompt = f"Plan: {json.dumps(plan)}\n\nGenerate the code blocks for HTML, CSS, and JS."
    
    current_code = state.get("current_code", {})
    if current_code and any(current_code.values()):
        user_prompt += "\n\n--- EXISTING CODE (You must modify this to implement the plan) ---\n"
        if current_code.get("html"):
            user_prompt += f"HTML:\n```html\n{current_code.get('html')}\n```\n"
        if current_code.get("css"):
            user_prompt += f"CSS:\n```css\n{current_code.get('css')}\n```\n"
        if current_code.get("js"):
            user_prompt += f"JS:\n```javascript\n{current_code.get('js')}\n```\n"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content
        
        import re
        
        html_match = re.search(r'```html\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
        css_match = re.search(r'```css\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
        js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
        
        if html_match:
            html = html_match.group(1).strip()
        else:
            # Fallback if no markdown block is found but it contains HTML tags
            if "<div" in content or "<html" in content or "<body" in content or "<main" in content:
                html = content.strip()
                # Strip out CSS and JS blocks if they exist elsewhere
                html = re.sub(r'```css.*?```', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = re.sub(r'```(?:javascript|js).*?```', '', html, flags=re.DOTALL|re.IGNORECASE)
                html = html.replace("```html", "").replace("```", "").strip()
            else:
                html = "<h1>Error parsing HTML</h1>"
                
        css = css_match.group(1).strip() if css_match else ""
        js = js_match.group(1).strip() if js_match else ""
        
        # Ensure HTML has boilerplate and links to CSS/JS
        if "<html" not in html.lower():
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>body {{ font-family: 'Inter', sans-serif; }}</style>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
{html}
<script src="script.js"></script>
</body>
</html>"""
        else:
            if "tailwindcss.com" not in html:
                html = html.replace("</head>", '    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">\n</head>')
            if "styles.css" not in html:
                html = html.replace("</head>", '    <link rel="stylesheet" href="styles.css">\n</head>')
            if "script.js" not in html:
                html = html.replace("</body>", '    <script src="script.js"></script>\n</body>')
        
        # Write files to preview_dir
        with open(os.path.join(preview_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        with open(os.path.join(preview_dir, "styles.css"), "w", encoding="utf-8") as f:
            f.write(css)
        with open(os.path.join(preview_dir, "script.js"), "w", encoding="utf-8") as f:
            f.write(js)
            
        await emit_log("Builder", "Code generation complete.")
        await emit_code(html, css, js)
        await emit_preview_reload()
        
        return {"html": html, "css": css, "js": js}
    except Exception as e:
        await emit_log("Builder", f"Error during build: {str(e)}")
        return {"html": "", "css": "", "js": ""}
