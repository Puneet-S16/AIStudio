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
    
    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.2, max_tokens=4000)
    
    system_prompt = """You are Agent B (Builder) - Elite Autonomous Frontend Engineer.
You consume the Ideator's structured JSON plan and generate exceptionally high-quality, WOW-factor frontend code.

CRITICAL INSTRUCTION: DO NOT OUTPUT ANY CONVERSATIONAL FILLER OR REASONING (e.g., "Okay, let's tackle this..."). START YOUR RESPONSE IMMEDIATELY WITH THE FIRST `### FILE:` HEADER.

Do NOT output JSON. You must output markdown code blocks. For each file you generate, you MUST provide a header comment indicating the filename exactly like this:

### FILE: index.html
```html
<!-- your html code here -->
```

### FILE: dashboard.html
```html
<!-- dashboard code here -->
```

### FILE: styles.css
```css
/* your css code here */
```

### FILE: script.js
```javascript
// your js code here
```

ABSOLUTE RULES (YOU ARE A GOD-TIER SENIOR DEVELOPER, ACT LIKE IT):
- NEVER build a simple, boring MVP. Ensure the UI is an absolute MASTERPIECE of art that rivals Apple or Vercel's marketing pages.
- MASSIVE SCALE & DEPTH: Your generated `index.html` MUST be incredibly long, comprehensive, and descriptive. You must output at least 5-7 deeply nested, highly detailed sections (Hero, Features, Testimonials, Pricing, FAQ, Footer). DO NOT output a short 50-line file. A complete site should be 300+ lines of rich HTML.
- DESCRIPTIVE COPY: NEVER use "Lorem Ipsum" or short 3-word placeholder text. Write actual, highly persuasive, lengthy marketing copy for every paragraph, header, and feature description so the judges see a "real" product.
- You MUST use **Tailwind CSS** for 95% of your styling.
- FLAWLESS RESPONSIVENESS: You must use mobile-first design (`flex-col`, `w-full`) and elegantly expand on desktop (`md:grid-cols-3`).
- **Material Icons** are available. Use them perfectly aligned with text.
- Generate MULTIPLE HTML files (e.g., `index.html`, `dashboard.html`) if the project requires it. Link them properly.
- If existing code is provided, MODIFY it rather than starting from scratch.

CRITICAL DESIGN TOKENS (YOU MUST USE THESE):
- Backgrounds: Use `bg-slate-950 text-white` for dark mode or `bg-slate-50 text-slate-900` for light. Use massive, subtle gradients: `bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#09090b] to-[#09090b]`.
- Glassmorphism: Use `backdrop-blur-xl bg-white/5 border border-white/10` for premium cards.
- Typography: Use `font-sans tracking-tight` for body and `tracking-tighter font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400` for primary headers.
- Micro-interactions: EVERY interactive element must have `transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-blue-500/20`.
- Rich Media: You MUST USE placeholder images to make the site look complete. Use `https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80` (or similar high-res Unsplash links).
- Custom CSS: Your `styles.css` MUST define keyframes like `@keyframes fade-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }` and apply them to elements.
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
        
        files = {}
        pattern = r'###\s*FILE:\s*([a-zA-Z0-9_\-\.]+)\s*```[a-z]*\s*(.*?)\s*```'
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            filename = match.group(1).strip()
            code = match.group(2).strip()
            files[filename] = code
            
        # Fallback if the LLM forgot the ### FILE: headers
        if not files:
            html_match = re.search(r'```html\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
            css_match = re.search(r'```css\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
            js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
            
            if html_match:
                files["index.html"] = html_match.group(1).strip()
            else:
                first_tag_match = re.search(r'<(?:!DOCTYPE|html|body|main|div|nav|header)', content, re.IGNORECASE)
                if first_tag_match:
                    html = content[first_tag_match.start():].strip()
                    html = re.sub(r'```css.*?```', '', html, flags=re.DOTALL|re.IGNORECASE)
                    html = re.sub(r'```(?:javascript|js).*?```', '', html, flags=re.DOTALL|re.IGNORECASE)
                    html = html.replace("```html", "").replace("```", "").strip()
                    files["index.html"] = html
                    
            if css_match: files["styles.css"] = css_match.group(1).strip()
            if js_match: files["script.js"] = js_match.group(1).strip()
            
        # Process HTML files for boilerplate
        for filename, code in files.items():
            if filename.endswith(".html"):
                if "<html" not in code.lower():
                    code = f"""<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Generated App</title>\n    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">\n    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">\n    <style>body {{ font-family: 'Inter', sans-serif; }}</style>\n    <link rel="stylesheet" href="styles.css">\n</head>\n<body>\n{code}\n<script src="script.js"></script>\n</body>\n</html>"""
                else:
                    if "tailwindcss.com" not in code:
                        code = code.replace("</head>", '    <script src="https://cdn.tailwindcss.com"></script>\n    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">\n</head>')
                    if "styles.css" not in code:
                        code = code.replace("</head>", '    <link rel="stylesheet" href="styles.css">\n</head>')
                    if "script.js" not in code:
                        code = code.replace("</body>", '    <script src="script.js"></script>\n</body>')
                files[filename] = code
        
        # Write files to preview_dir
        for filename, code in files.items():
            # Security: Prevent directory traversal (e.g. filename = "../../main.py")
            safe_filename = os.path.basename(filename)
            filepath = os.path.join(preview_dir, safe_filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            
        await emit_log("Builder", f"Code generation complete. Generated {len(files)} files.")
        
        # We need to emit files to the frontend
        # The existing emit_code takes html, css, js. We can change the backend graph later, but for now we'll pass the files dict.
        await state["emit_files"](files)
        await emit_preview_reload()
        
        return {"files": files}
    except Exception as e:
        await emit_log("Builder", f"Error during build: {str(e)}")
        return {"html": "", "css": "", "js": ""}
