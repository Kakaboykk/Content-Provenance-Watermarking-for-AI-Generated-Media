# Content-Provenance Watermarking Frontend

A modern, responsive web application for generating, protecting, and verifying AI-generated images with cryptographic provenance tracking.

---

## Tech Stack

- **Framework**: [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Routing**: [React Router DOM v7](https://reactrouter.com/)

---

## Architecture & Views

The application provides four main interactive flows wrapped in a unified layout:

| View | Path | Description |
| :--- | :--- | :--- |
| **Dashboard** | `/` | System overview, quick action tiles, and provenance verification metrics. |
| **Generate Flow** | `/generate` | Enter prompts to generate AI images with immediate, automatic watermark injection. |
| **Protect Flow** | `/protect` | Upload existing images to embed an invisible DWT-DCT watermark and download the signed asset. |
| **Verify Flow** | `/verify` | Blind watermark extraction, provenance ledger lookup, crop diagnostics, and AI probability scoring. |
| **History View** | `/history` | Searchable provenance audit log showing generated assets, SHA-256 hashes, and verification history. |

---

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Run the Development Server

```bash
npm run dev
```

The frontend will start at `http://localhost:5173`.

### 3. Build for Production

```bash
npm run build
```

---

## Backend API Proxy

Development requests made to `/api/*` are automatically forwarded to the FastAPI backend running at `http://localhost:8000` via the Vite proxy configured in `vite.config.ts`.
Ensure the backend server is running when testing live generation or verification flows.
