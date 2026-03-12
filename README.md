# Micro-SaaS Idea Validator
Find SaaS ideas worth building

---

🔑 Step 1 — Get your free Groq API key

Go to https://console.groq.com and create a free account.
Click "API Keys" then "Create API Key" and copy it. It looks like: gsk_...

💻 Step 2 — Install everything

Open your terminal in this folder and run:

    python -m venv venv 
    source venv/bin/activate
    pip install -r requirements.txt

(On Windows use: venv\Scripts\activate instead)

🔐 Step 3 — Add your API key

Find the file called .env.example in this folder.
Rename it to .env (just remove the .example part).
Open it and replace your_groq_key_here with the key you copied.

🚀 Step 4 — Start the app

    uvicorn main:app --reload

Then open your browser and go to http://localhost:8000

To stop the app press Ctrl + C in your terminal.

Built with Deplo · Powered by Groq (https://console.groq.com)
