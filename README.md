# FixiLab — Intelligent Laboratory Documentation Audit Software

Detect calculation discrepancies, documentation gaps and inconsistencies in analytical laboratory worksheets with FixiLab's intelligent documentation audit platform.

## Features

- **Text extraction and OCR**: Read text from PDFs and use Tesseract OCR for scanned PDFs and images
- **Automated Calculation Checks**: Verify recorded values against their formulas (e.g. pendulum period/`g`, dilutions) and flag discrepancies
- **ALCOA+ Validation**: Support data integrity reviews against Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, and Available principles
- **Consistency & Documentation Checks**: Detect cross-section contradictions, unit mismatches, dangling references and typographical issues
- **Actionable Audit Reports**: Generate downloadable PDF reports with findings and evidence
- **Traceable Review Workflow**: Document reviewer decisions and comments

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Tailwind CSS 4
- Framer Motion

### Backend
- FastAPI
- PyMuPDF (primary PDF text extraction, with pypdf and a standard-library fallback)
- SQLAlchemy (with SQLite)
- Pydantic (for data validation)
- PDF report generation using the Python standard library (no external PDF library required)

## Installation

### Prerequisites

- Node.js 20+ and npm
- Python 3.10+
- pip (Python package manager)
- Tesseract OCR for scanned PDFs and images (text-based PDFs do not require it)

### Frontend Setup

1. Install dependencies:
```bash
npm install
```
In Windows PowerShell, use `npm.cmd install` and `npm.cmd run dev` if the execution policy blocks `npm` scripts.

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:8080`

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# macOS/Linux: source venv/bin/activate
# Windows PowerShell: .\venv\Scripts\Activate.ps1
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`. To process scanned documents, install Tesseract OCR and make sure `tesseract` is available on `PATH`. If it is not on `PATH`, set `TESSERACT_CMD` to the full executable path before starting the backend.

### Running Both Services

For the full application to work, both the frontend and backend must be running simultaneously:

- Terminal 1: `npm run dev` (frontend on port 8080)
- Terminal 2: `cd backend` then `uvicorn app.main:app --reload --port 8000` (backend on port 8000)

The frontend defaults to `http://localhost:8000` for the API. Set `VITE_API_URL` only when your backend uses a different address.

### Windows Troubleshooting

- **`'npm' is not recognized as an internal or external command`** — Node.js is installed but its folder is missing from your *current* terminal's `PATH`. Close that terminal and open a new one (a shell only reads `PATH` when it starts). Verify with `where npm` in Command Prompt or `Get-Command npm` in PowerShell; it should resolve to `...\nodejs\npm.cmd`. If it still fails, add `C:\Program Files\nodejs` to your User `PATH` (Start → *Edit the system environment variables* → *Environment Variables*).
- **PowerShell: `npm.ps1 cannot be loaded because running scripts is disabled on this system`** — Windows PowerShell's default execution policy blocks npm's `.ps1` shim. Either use Command Prompt, or run `npm.cmd run dev` in PowerShell, or allow local scripts once with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Usage

1. Open `http://localhost:8080` in your browser
2. Click "Start Your First Audit"
3. Upload a PDF or image worksheet (max 15 MB)
4. Open the **Preview** tab to see the uploaded document
5. Findings are generated on upload. Select **Extract Data**, then **Validate** to (re)run extraction and the full audit rules — calculation checks, ALCOA+ data-integrity, cross-section consistency and documentation completeness
6. Review findings and add comments
7. Download the PDF audit report

## API Endpoints

- `POST /api/audits` - Upload a document and create an audit
- `GET /api/audits/{id}` - Get audit details and findings
- `GET /api/audits/{id}/file` - Preview the uploaded document
- `POST /api/audits/{id}/extract` - Extract data from document
- `POST /api/audits/{id}/validate` - Validate extracted data and generate findings
- `PATCH /api/audits/{id}/findings/{finding_id}` - Update finding status and comments
- `GET /api/audits/{id}/report` - Download a PDF report
- `GET /api/health` - Health check

## Security Notes

- File uploads are validated for type, size, and content
- Filenames are sanitized to prevent path traversal
- Files are stored in a private uploads directory
- The /audit route is set to noindex for search engines
- Do not upload sensitive laboratory data to public deployments

## Development

### Build for Production

```bash
npm run build
```

### Run Tests

Frontend:

```bash
npm test
```

Backend (from the `backend` directory, with the virtual environment active):

```bash
python -m pytest
```

### Lint Code

```bash
npm run lint
```

### Format Code

```bash
npm run format
```

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic (pdf_reader, extraction, rules, validation, reports)
│   │   ├── database.py     # Database models and session
│   │   ├── schemas.py      # Pydantic schemas
│   │   └── main.py         # FastAPI app entry point
│   ├── tests/             # Backend tests (pytest)
│   ├── uploads/           # Local uploaded document storage (created at runtime)
│   ├── reports/           # Local generated PDF reports (created at runtime)
│   └── requirements.txt    # Python dependencies
├── src/
│   ├── components/         # React components
│   ├── routes/             # TanStack Router pages
│   ├── lib/                # Utilities
│   └── styles.css          # Global styles
├── public/                 # Static assets
└── package.json            # Frontend dependencies
```

## License

This project is for demonstration purposes. FixiLab supports documentation review and does not replace qualified human review or guarantee regulatory compliance.

## Disclaimer

Automated checks cover calculation verification, ALCOA+ data-integrity signals, cross-section consistency and documentation completeness for supported worksheet formats. They do not interpret every laboratory formula, verify scientific correctness, or independently certify regulatory compliance. A qualified reviewer must verify the full worksheet and applicable requirements.
