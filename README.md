# NIC VentureForge AI
**From Problem to Pitch-Ready Startup**

A Python and Streamlit assignment that turns a problem into startup concepts, a business plan and a downloadable pitch pack using Groq AI.

## Features
- English/Urdu voice recording and editable transcription, with text input available.
- Three concepts: Budget-Friendly, Technology-Driven and High-Growth.
- Complete Markdown business plan.
- Five-category feasibility analysis with a weighted score and chart.
- Five-question simulated investor interview, feedback and improved plan.
- Pitch summary, nine-block Business Model Canvas and PDF downloads.

There are exactly two Streamlit pages. All AI features are stages inside the generator.

## Files to explain
| File or folder | Purpose |
|---|---|
| `streamlit_app.py` | Starts the app and registers the two pages. |
| `pages/landing.py` | Welcome page and navigation button. |
| `pages/generator.py` | Input, concepts, plan, feasibility, interview and export interface. |
| `services/groq_service.py` | Groq text generation, voice transcription and API errors. |
| `services/pdf_service.py` | Formats and creates PDF downloads. |
| `services/__init__.py` | Marks services as a Python package. |
| `prompts.py` | Instructions sent to the AI. |
| `models.py` | Pydantic rules that validate AI responses. |
| `utils.py` | Session state, workflow resets and score calculations. |
| `styles.py` | Custom interface styling. |
| `.streamlit/config.toml` | Streamlit colors and app settings. |
| `tests/` | Automated tests using mocked AI responses. |
| `requirements.txt` | Python packages needed for the app and tests. |
| `.env.example` | Empty credential template for another computer. |
| `.gitignore` | Excludes credentials, installed packages and generated caches. |
| `run_app.bat` | Windows shortcut to run the app. |
| `PRESENTATION_GUIDE.md` | Architecture, demo script and teacher questions. |

## Setup and run (Windows PowerShell)
Use Python 3.11 or newer. Run these commands from this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On a new computer, copy `.env.example` to `.env`. Keep your existing `.env` if already configured. Edit it locally:

```dotenv
GROQ_API_KEY=your_actual_key
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo
```

Start by double-clicking `run_app.bat`, or run:

```powershell
.\.venv\Scripts\python.exe -B -m streamlit run streamlit_app.py
```

Open http://localhost:8501. The generator also opens directly at http://localhost:8501/generator. Restart after changing credentials. Microphone access requires browser permission and localhost or HTTPS. Record a short clip under 24 MB, transcribe it, review the editable text, then generate concepts. Generated plans and PDFs are in English.

## Simple data flow
Problem or voice transcript -> Three concepts -> Selected idea -> Business plan -> Feasibility -> Investor Challenge -> Improved plan -> Pitch PDF.

Groq performs the AI tasks. Pydantic checks structured responses. Python calculates scores. Streamlit Session State keeps results during the session. ReportLab creates PDFs. There is no login, database or agent framework.

## Scoring
Feasibility = demand x 30% + competitive positioning x 20% + investment practicality x 20% + technical feasibility x 15% + scalability x 15%. Higher always means better.

Pitch readiness = sum of five answer scores / 50 x 100. Each answer is scored out of 10. These are educational AI estimates; verify market and financial assumptions independently.

## Tests
```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

The project passed 59 automated tests covering validation, prompts, scoring, state, API failures, transcription wiring, PDFs and the full mocked Streamlit journey. Mock tests do not verify live Groq quality or real microphone recording. Run a short live test with your own key before presenting.

## What to submit
Submit the source files, configuration template, tests, README and presentation guide listed above. Do not submit `.venv/`, your private `.env`, `.streamlit/secrets.toml`, or generated cache folders. `.venv` contains installed libraries for this computer; it is not your application code. `.env` contains your local API configuration. Both stay locally so the app remains ready to run.

AI requests send the submitted text/audio and relevant startup context to Groq. Results are session-only, so download important work. The investor is simulated; no official NIC endorsement is implied.

## Rate-limit handling
The app uses task-specific output budgets and low reasoning effort for GPT-OSS. A temporary Groq rate limit with a wait of 60 seconds or less triggers a visible countdown and one retry. Longer waits, daily quotas and oversized requests show actionable messages instead of retrying indefinitely. A complete 18-section plan followed by feasibility analysis was verified live after this change. Account limits still apply.
