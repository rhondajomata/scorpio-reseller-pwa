import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("GEMINI_API_KEY") 
client = genai.Client(api_key=API_KEY)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scorpio Rizn - AI Scanner</title>
        <link rel="manifest" href="manifest.json">
        <meta name="theme-color" content="#0a0a0c">
        <link rel="apple-touch-icon" href="icons/icon-512.png">
        <style>
            :root {
                --bg: #0a0a0c;
                --surface: #121216;
                --border: #22222a;
                --text: #e4e4ed;
                --text-muted: #8e8e9f;
                --accent: #58a6ff;
                --success: #238636;
                --success-hover: #2ea043;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 40px 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .container {
                max-width: 550px;
                width: 100%;
                background-color: var(--surface);
                padding: 35px;
                border-radius: 16px;
                border: 1px solid var(--border);
                box-shadow: 0 12px 40px rgba(0,0,0,0.6);
                box-sizing: border-box;
            }
            h1 { 
                color: #fff; 
                text-align: center; 
                font-size: 26px; 
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 8px; 
                letter-spacing: -0.5px;
            }
            .subtitle {
                text-align: center;
                color: var(--text-muted);
                font-size: 14px;
                margin-bottom: 30px;
            }
            .input-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
            input[type="file"] {
                width: 100%;
                padding: 14px;
                background: #181820;
                border: 1px dashed #3a3a4a;
                border-radius: 8px;
                color: var(--text);
                box-sizing: border-box;
                cursor: pointer;
                transition: border-color 0.2s;
            }
            input[type="file"]:hover { border-color: var(--accent); }
            
            button {
                width: 100%;
                background-color: var(--success);
                color: white;
                border: none;
                padding: 14px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 10px;
                transition: background 0.2s, transform 0.1s;
            }
            button:hover { background-color: var(--success-hover); }
            button:active { transform: scale(0.99); }
            button:disabled { background-color: #1c1c24; color: #525262; cursor: not-allowed; transform: none; }
            
            #pwaInstallBtn { background-color: #21212b; color: var(--accent); border: 1px solid var(--border); margin-bottom: 20px; display: none; }
            #pwaInstallBtn:hover { background-color: #2a2a37; }
            
            #copyBtn {
                background-color: #21212b;
                color: #fff;
                border: 1px solid var(--border);
                margin-top: 0;
                margin-bottom: 12px;
                padding: 10px;
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            #copyBtn:hover { background-color: #2a2a37; border-color: #444455; }
            
            #loading { display: none; text-align: center; margin-top: 20px; font-style: italic; color: var(--accent); font-size: 14px; }
            #resultContainer { margin-top: 35px; display: none; }
            h2 { color: #fff; font-size: 18px; margin-bottom: 12px; font-weight: 600; }
            pre {
                background-color: #070709;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid var(--border);
                white-space: pre-wrap;
                word-wrap: break-word;
                line-height: 1.6;
                font-size: 14px;
                color: #e4e4ed;
            }
        </style>
    </head>
    <body>
    <div class="container">
        <button id="pwaInstallBtn">📲 Install ScorpioAI App</button>
        <h1>Scorpio Rizn AI</h1>
        <div class="subtitle">Visual Measurement & Adaptive Marketplace Generator</div>
        
        <div class="input-group">
            <label>📸 Photo 1: Full Item (with Quarter reference)</label>
            <input type="file" id="shirtInput" accept="image/*">
        </div>
        <div class="input-group">
            <label>🏷️ Photo 2: Size / Fabric / Care Tag</label>
            <input type="file" id="tagInput" accept="image/*">
        </div>
        <button id="scanBtn" onclick="runAIScan()">Generate Marketplace Listing</button>
        <div id="loading">🧠 Processing assets and calculating scale metrics...</div>
        
        <div id="resultContainer">
            <h2>✨ Generated Output</h2>
            <!-- New One-Click Copy To Clipboard Button -->
            <button id="copyBtn" onclick="copyToClipboard()">📋 Copy Listing Description</button>
            <pre id="resultText"></pre>
        </div>
    </div>

    <script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => { navigator.serviceWorker.register('/sw.js'); });
    }

    let deferredPrompt;
    const installBtn = document.getElementById('pwaInstallBtn');
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault(); deferredPrompt = e; installBtn.style.display = 'block';
    });
    installBtn.addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') installBtn.style.display = 'none';
            deferredPrompt = null;
        }
    });

    async function runAIScan() {
        const shirtInput = document.getElementById('shirtInput');
        const tagInput = document.getElementById('tagInput');
        if (shirtInput.files.length === 0 || tagInput.files.length === 0) {
            alert("Please provide both image captures."); return;
        }
        const btn = document.getElementById('scanBtn');
        const loading = document.getElementById('loading');
        const resultContainer = document.getElementById('resultContainer');
        const resultText = document.getElementById('resultText');

        btn.disabled = true; loading.style.display = "block"; resultContainer.style.display = "none";
        const formData = new FormData();
        formData.append("shirt", shirtInput.files[0]);
        formData.append("tag", tagInput.files[0]);

        try {
            const response = await fetch("/scan-clothing/", { method: "POST", body: formData });
            const data = await response.json();
            if (data.success) {
                resultText.innerText = data.listing;
                resultContainer.style.display = "block";
            } else { alert("Processing Error: " + data.error); }
        } catch (err) { alert("Server communication loss."); console.error(err); }
        finally { btn.disabled = false; loading.style.display = "none"; }
    }

    // Smooth Clipboard Copy Function
    function copyToClipboard() {
        const textToCopy = document.getElementById('resultText').innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            const copyBtn = document.getElementById('copyBtn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = "✅ Copied to Clipboard!";
            copyBtn.style.borderColor = "var(--success)";
            copyBtn.style.color = "#2ea043";
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.style.borderColor = "var(--border)";
                copyBtn.style.color = "#fff";
            }, 2000);
        }).catch(err => { alert("Failed to copy text."); });
    }
    </script>
    </body>
    </html>
    """

@@app.post("/scan-clothing/")
async def scan_clothing(shirt: UploadFile = File(...), tag: UploadFile = File(...)):
    try:
        shirt_bytes = await shirt.read()
        tag_bytes = await tag.read()

        image_shirt = types.Part.from_bytes(data=shirt_bytes, mime_type="image/jpeg")
        image_tag = types.Part.from_bytes(data=tag_bytes, mime_type="image/jpeg")

    try:
             prompt = (
            "You are an expert reselling assistant for eBay and Vinted. "
            "Analyze these two images. One image contains the full retail item (clothing, shoes, or accessory) "
            "along with a standard US Quarter coin (0.955 inches in diameter) placed on it as a size reference. "
            "First, locate the quarter. Use its known size to visually calculate the approximate real-world measurements "
            "relevant to this specific item type (e.g., pit-to-pit/length for tops, waist/inseam for pants, outsole for shoes).\n\n"
            "Next, read the care tag/branding for materials and sizing. Finally, generate an optimized marketplace listing. "
            "Do NOT use placeholders like [Insert Measurement Here]. Fill in the exact measurements you calculated."
        )

 response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_shirt, image_tag, prompt]
        )
        return {"success": True, "listing": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}
