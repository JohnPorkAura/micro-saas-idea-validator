# Micro-SaaS Idea Validator
Find SaaS ideas worth building

---

## Setup

**1. Install dependencies**

Open your terminal, navigate to this folder, and run:

Mac / Linux:

    python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

Windows:

    python -m venv venv && .\venv\Scripts\activate && pip install -r requirements.txt

**2. Start the app**

    uvicorn main:app --reload

Then open http://localhost:8000 in your browser.

**3. Enter your API key**

The app will ask for your Groq API key on first run.
Get a free key at https://console.groq.com

---

Built with Deplo · Powered by Groq
