import os
import json
import base64
from playwright.async_api import async_playwright
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

async def review_node(state):
    emit_log = state["emit_log"]
    await emit_log("Reviewer", "Running Playwright to visually inspect the build...")
    
    # Use localhost server instead of file:/// to accurately simulate production and avoid CORS false-positives
    file_url = "http://localhost:8000/preview/index.html"
    
    console_logs = []
    screenshot_b64 = ""
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            await page.goto(file_url)
            # wait a bit for animations
            await page.wait_for_timeout(1000)
            
            screenshot_bytes = await page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            await browser.close()
    except Exception as e:
        await emit_log("Reviewer", f"Playwright Error: {str(e)}")
        return {"issues": [f"Playwright Error: {str(e)}"]}
        
    await emit_log("Reviewer", "Screenshot captured. Analyzing console logs with LLM...", {"logs": console_logs})
    
    if not console_logs:
        await emit_log("Reviewer", "No console logs found. Skipping LLM analysis.", [])
        return {"issues": []}
        
    llm = ChatGroq(model="qwen/qwen3-32b", temperature=0.2)
    
    system_prompt = """You are Agent C (Reviewer) - Autonomous QA Engineer.
Analyze the provided console logs of a web application.
Identify any CRITICAL errors or broken UI issues.
IMPORTANT: You MUST absolutely IGNORE the following warnings/errors:
1. "warning: cdn.tailwindcss.com should not be used in production..."
2. Any CORS or "NotSameOrigin" errors (e.g., net::ERR_BLOCKED_BY_RESPONSE.NotSameOrigin).
If you find OTHER issues, output a strictly formatted JSON array of strings describing the issues.
If the only issues are the ignored ones above, output an empty JSON array: []
Do not include markdown wrappers, just the JSON array.
"""
    
    user_prompt = "Console Logs:\n" + "\n".join(console_logs) + "\n\nAnalyze the logs."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        import re
        content = response.content.strip()
        
        # Extract everything between the first '[' and last ']'
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            content = match.group(0)
        else:
            content = "[]"
            
        issues = json.loads(content)
        if issues:
            await emit_log("Reviewer", f"Found {len(issues)} issues.", issues)
        else:
            await emit_log("Reviewer", "No issues found. Build looks solid.")
            
        return {"issues": issues}
    except Exception as e:
        await emit_log("Reviewer", f"Error during vision analysis: {str(e)}")
        return {"issues": [f"Vision Error: {str(e)}"]}
