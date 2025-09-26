# Main App - Interactive Particle Effects

React-based particle effects application with real-time interaction and customizable visual themes.

## Features

- **Particle Physics**: Real-time particle simulation with gravity and velocity
- **Mouse Interaction**: Spawn particles by moving the cursor
- **Visual Themes**: Multiple color presets (Astro, LaFlame, Utopia, Jazz, Ocean, Candy)
- **Live Controls**: Adjust parameters in real-time via UI controls
- **Performance Optimized**: 60fps particle system with efficient rendering

## Development

```bash
# From repository root
npm run dev:main

# Or from this directory  
npm run dev
```

## Building

```bash
# From repository root
npm run build:main

# Or from this directory
npm run build
```

## Configuration

- **Port**: 5173 (development)
- **Build Output**: `dist/`
- **Technologies**: React 19, TypeScript, Vite

## Architecture

- `src/App.tsx` - Main application wrapper
- `src/FlowApp.tsx` - Core particle system logic
- `src/components/CursorField.tsx` - Canvas particle renderer
- `src/components/ModMenu.tsx` - Parameter controls
- `src/state.tsx` - Application state management
- `src/lib/presets.ts` - Visual theme definitions

## Customization

Edit `src/lib/presets.ts` to add new color schemes:

```typescript
export const PRESETS: Record<string, Partial<Settings>> = {
  custom: { 
    preset: "custom", 
    orbColor: "#ff6b35", 
    bgHue: 200, 
    spawn: 10, 
    speed: 1.2, 
    trail: 0.08, 
    gravity: 0.025 
  }
};
```