import os
import json
import base64
from playwright.async_api import async_playwright
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

async def review_node(state):
    emit_log = state["emit_log"]
    await emit_log("Reviewer", "Running Playwright to visually inspect the build...")
    
    preview_dir = state["preview_dir"]
    index_path = os.path.join(preview_dir, "index.html")
    
    file_url = f"file:///{index_path.replace(chr(92), '/')}"
    
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
Identify any errors or warnings.
If you find issues, output a strictly formatted JSON array of strings describing the issues.
If everything looks perfect and premium (no errors), output an empty JSON array: []
Do not include markdown wrappers, just the JSON array.
"""
    
    user_prompt = "Console Logs:\n" + "\n".join(console_logs) + "\n\nAnalyze the logs."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        issues = json.loads(content)
        if issues:
            await emit_log("Reviewer", f"Found {len(issues)} issues.", issues)
        else:
            await emit_log("Reviewer", "No issues found. Build looks solid.")
            
        return {"issues": issues}
    except Exception as e:
        await emit_log("Reviewer", f"Error during vision analysis: {str(e)}")
        return {"issues": [f"Vision Error: {str(e)}"]}
