from playwright.sync_api import sync_playwright
import time

url = 'http://127.0.0.1:8001/empleados/alta'
output = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    def on_console(msg):
        output.append(f"CONSOLE {msg.type}: {msg.text}")
    page.on('console', on_console)

    def on_request(req):
        output.append(f"REQ {req.method} {req.url}")
    page.on('request', on_request)

    def on_response(resp):
        output.append(f"RESP {resp.status} {resp.url}")
    page.on('response', on_response)

    page.goto(url)
    time.sleep(0.5)

    # Focus documento_numero and type value slowly to simulate user
    page.focus('#documento_numero')
    for ch in 'Z2877578F':
        page.keyboard.type(ch)
        time.sleep(0.12)

    # blur by focusing another element
    page.focus('#nombre')
    time.sleep(1.0)

    # Wait a bit to capture potential loops
    time.sleep(3.0)

    # Capture validity state and error text
    validity = page.evaluate("() => { const el = document.getElementById('documento_numero'); return {valid: el.checkValidity(), message: el.validationMessage, classes: el.className}; }")
    output.append(f"VALIDITY {validity}")

    # Print first 200 console/request/response lines
    for line in output[:400]:
        print(line)

    browser.close()
