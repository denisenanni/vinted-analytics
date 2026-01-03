Add a new React component/tab to the Vinted Analytics frontend.

The user will provide: $ARGUMENTS

Steps:
1. Create component file in `web/src/components/ComponentName.tsx`
2. Add TypeScript interfaces (or import from `api/client.ts`)
3. Add component styles at the end of `web/src/App.css`
4. Import and add tab in `web/src/App.tsx`:
   - Add to tab type union
   - Add to getInitialTab()
   - Add nav button
   - Add content section

Styling conventions:
- Use `.component-name` prefix for all classes
- Colors: primary teal (#09b1ba), success green (#22c55e), warning yellow (#eab308), error red (#ef4444)
- Border radius: 6px (small), 8px (medium), 12px (large)
- Use flexbox/grid for layouts
- Add responsive breakpoints at 640px and 768px

State management:
- Keep state in App.tsx if shared between components
- Use local state in component if isolated
- Consider adding to the 2-minute cache in client.ts for expensive API calls
