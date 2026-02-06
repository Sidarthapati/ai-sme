# AI SME Frontend

React/Next.js frontend for the AI SME Assistant.

## 🚀 Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
cp .env.example .env.local
```

Required variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## 📁 Structure

```
frontend/
├── app/                  # Next.js App Router
│   ├── chat/            # Chat page (Week 2)
│   ├── upload/          # Document upload page (Week 2)
│   └── api/             # API routes (if needed)
├── components/
│   ├── chat/            # Chat components (Week 2)
│   ├── ui/              # Reusable UI components (Week 2)
│   └── layout/          # Layout components (Week 2)
├── lib/
│   ├── api/             # API client
│   ├── store/           # State management (Zustand)
│   └── utils/           # Utility functions
└── public/              # Static assets
```

## 🎨 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Icons**: Lucide React
- **Markdown**: react-markdown
- **Code Highlighting**: react-syntax-highlighter

## 📝 Development Timeline

### Week 2 (Days 8-14)
- [ ] Chat interface
- [ ] Message components
- [ ] Source citations display
- [ ] File upload UI
- [ ] Conversation history
- [ ] Settings panel
- [ ] Dark mode

### Week 3 (Days 15-21)
- [ ] Polish and optimization
- [ ] Admin features
- [ ] Advanced interactions
- [ ] Mobile responsiveness

## 🔧 Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## 📚 To Be Implemented

Components and features will be added during Week 2 of development:
- Chat interface
- Document upload
- Source display
- History management
- Settings and preferences
