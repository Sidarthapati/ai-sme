export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">AI SME Assistant</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Your intelligent documentation and code assistant
        </p>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            🚧 Frontend is under construction
          </p>
          <p className="text-sm text-muted-foreground">
            Week 2: Chat interface, document upload, and more coming soon!
          </p>
        </div>
      </div>
    </main>
  )
}
