import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^lodash\/(.*)/, replacement: 'lodash/$1.js' },
    ],
  },
  build: {
    target: 'esnext',
    chunkSizeWarningLimit: 650,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-charts': ['recharts'],
          'vendor-three': ['three'],
          'vendor-r3f': ['@react-three/fiber', '@react-three/drei'],
        },
      },
    },
  },
  server: {
    port: Number(process.env.PORT) || 5173,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${process.env.VITE_BACKEND_PORT || '8000'}`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://127.0.0.1:${process.env.VITE_BACKEND_PORT || '8000'}`,
        ws: true,
        changeOrigin: true,
        rewriteWsOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            const isBenign =
              err.code === 'ECONNABORTED' ||
              err.code === 'ECONNRESET' ||
              err.code === 'EPIPE' ||
              err.message?.includes('ECONNABORTED') ||
              err.message?.includes('ECONNRESET');
            if (isBenign) {
              return;
            }
            console.error('[vite] ws proxy error:', err);
          });
          proxy.on('proxyReqWs', (_proxyReq, _req, socket, _options, _head) => {
            const originalEmit = socket.emit;
            socket.emit = function (event, ...args) {
              if (event === 'error') {
                const err = args[0];
                const isBenign =
                  err &&
                  (err.code === 'ECONNABORTED' ||
                    err.code === 'ECONNRESET' ||
                    err.code === 'EPIPE' ||
                    err.message?.includes('ECONNABORTED') ||
                    err.message?.includes('ECONNRESET'));
                if (isBenign) {
                  return false;
                }
              }
              return originalEmit.apply(this, [event, ...args]);
            };
          });
        },
      },
    },
  },
});
