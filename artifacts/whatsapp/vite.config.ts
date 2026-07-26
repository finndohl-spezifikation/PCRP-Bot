import path from 'path';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

const rawPort = process.env.PORT;
const port = rawPort ? Number(rawPort) : 3000; // PORT only matters in dev/preview

// Default to '/' when not running inside Replit (e.g. Railway production build)
const basePath = process.env.BASE_PATH ?? '/';

export default defineConfig(async () => {
  const isReplit = !!process.env.REPL_ID;

  const replitPlugins = isReplit
    ? [
        (await import('@replit/vite-plugin-runtime-error-modal')).default(),
        (await import('@replit/vite-plugin-cartographer')).cartographer({
          root: path.resolve(import.meta.dirname, '..'),
        }),
        (await import('@replit/vite-plugin-dev-banner')).devBanner(),
      ]
    : [];

  return {
    base: basePath,
    plugins: [react(), tailwindcss(), ...replitPlugins],
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, 'src'),
        '@assets': path.resolve(import.meta.dirname, '..', '..', 'attached_assets'),
      },
      dedupe: ['react', 'react-dom'],
    },
    root: path.resolve(import.meta.dirname),
    build: {
      outDir: path.resolve(import.meta.dirname, 'dist/public'),
      emptyOutDir: true,
    },
    server: {
      port,
      strictPort: true,
      host: '0.0.0.0',
      allowedHosts: true,
      fs: { strict: true },
    },
    preview: {
      port,
      host: '0.0.0.0',
      allowedHosts: true,
    },
  };
});
