# Presenting NIC VentureForge AI

## What problem does it solve?

New founders often notice a problem but do not know how to turn it into a business. VentureForge gives them three approaches, a plan, an initial assessment, and a chance to practice defending the idea. It helps structure their thinking; it does not prove a business will succeed.

## Why Streamlit?

Streamlit creates a web interface using Python. We can build forms, navigation, charts, and downloads without writing a separate frontend application. Exactly two pages keep this assignment easy to demonstrate.

## What Groq does

Groq hosts the AI models. The official Python SDK sends our prompts and receives model output. Text generation creates concepts and business content. A separate Whisper transcription endpoint converts recorded speech into text. The API key stays in configuration outside the source code.

## Voice transcription

The microphone widget records audio. Clicking Transcribe sends that WAV recording to Groq's speech-to-text endpoint with the selected language (English, Urdu, or automatic detection). The transcript appears in the editable problem field. The founder checks it, corrects any errors, and then generates concepts using the normal text workflow. A failed microphone or transcription never blocks typing.

## How prompts work

The system prompt defines the advisor's role and requires honest assumptions. Each task prompt gives a specific job and startup context. For concepts, scores, interview feedback, and the canvas, we also send a JSON schema. Pydantic checks the returned data. Long business plans use Markdown with required section headings. Invalid output gets one repair attempt, then an error instead of invented data.

## How feasibility is calculated

Groq proposes five scores and explains them. Python calculates the total:

```text
Demand × 0.30 + Competition × 0.20 + Investment × 0.20
    + Technical feasibility × 0.15 + Scalability × 0.15
```

All scores are out of 100. Higher means better. A high competition score means stronger competitive positioning, and a high technical feasibility score means implementation is more realistic. These weights are defined in `utils.py`. For category scores 80, 60, 70, 90, and 50, the total is 71, not a hardcoded app score.

## How the Investor Challenge works

The model reads the original plan and generates five questions covering demand, revenue, competition, acquisition, and execution. The founder answers one question at a time. The model evaluates evidence (up to 4 points), reasoning (3), and specificity (3), and gives actionable feedback. Python stores each answer once, then calculates readiness as total points divided by 50, multiplied by 100. The improvement prompt receives the original plan, optional feasibility, questions, answers, and feedback. The revised plan is shown beside the preserved original.

## How export works

Groq creates a concise pitch summary and nine-block Business Model Canvas. ReportLab turns this content into a PDF with a cover, headings, wrapped tables, and page numbers. Optional assessments are included only when present. Missing stages are labeled as unassessed, and investor feedback is included only after all five rounds. The complete business plan can be downloaded independently.

## Simple architecture

```text
Founder
   |
Streamlit: Welcome / Generator (six stages)
   |                  |
Session State      Groq service <--- Prompts + Pydantic models
   |                  |
Python scoring     Groq text / Whisper transcription
   |
ReportLab ---> PDF download
```

## Five-minute demonstration script

Before class: configure a working API key, run the app, check internet and Groq limits, and prepare a short transport problem. Do one real run beforehand; keep downloaded results as backup and clearly label them as previously generated. Recording and long AI responses may exceed five minutes, so prepare the plan in the same session if needed.

- **0:00–0:35:** Show Welcome. “This is a mini incubator, from problem to pitch. There are exactly two pages.” Open the generator.
- **0:35–1:15:** Show microphone recording in English or Urdu, transcribe, edit the text, and enter Pakistan with a currency-specific budget. “Audio is transcribed first; the text model does not receive raw audio.”
- **1:15–1:55:** Generate and compare three concepts. Explain why their approaches differ and select one.
- **1:55–2:35:** Generate or show the prepared complete business plan. Highlight budget assumptions, MVP, and the 90-day roadmap.
- **2:35–3:15:** Run feasibility and explain the five weights. Point to the dynamic chart and assumptions requiring validation.
- **3:15–4:15:** Show one investor answer and feedback. If the other rounds were prepared, show the final score and improved plan beside the original. Explain that this is a simulation.
- **4:15–5:00:** Prepare the pitch and canvas, download the pitch pack, and open the PDF. Close by explaining the simple Python architecture and tests.

## Ten likely teacher questions

1. **Is this a chatbot?** No. It is a staged workflow with specific outputs and checks at each step.
2. **Why three ideas?** They offer different operating approaches so the founder makes a meaningful choice.
3. **Are scores hardcoded?** No. Groq supplies provisional category scores; Python applies fixed transparent formulas.
4. **Why Pydantic?** It checks required fields, exact counts, and score ranges before the UI uses AI data.
5. **Does it work without a key?** The interface loads, but real generation and transcription need a configured Groq key.
6. **What happens if the API fails?** We show a clear error, preserve saved results, and never substitute fake content.
7. **Where is the data stored?** In Streamlit Session State for the browser session. There is no database.
8. **Is the investor real?** No. It is an educational simulation and says so throughout.
9. **Can users export without completing the interview?** Yes. The plan and pitch pack are available; missing assessments are marked appropriately.
10. **How did you test it?** Unit tests verify schemas, prompts, scoring, API handling, workflow state and PDFs. Streamlit AppTest exercises widgets with mocked AI. Real microphone and live Groq checks must be reported separately.
