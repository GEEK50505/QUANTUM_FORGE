import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    svgr({
      svgrOptions: {
        icon: true,
        // This will transform your SVG to a React component
        exportType: "named",
        namedExport: "ReactComponent",
      },
    }),
  ],
  server: {
    host: true, // Enable network access
    port: 5173, // Specify port
    strictPort: true, // Don't try other ports if 5173 is taken
    proxy: {
      // Proxy API requests to mock backend
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
        }
      }
    }
  }
  ,
  resolve: {
    alias: {
      // No custom alias for react-router; rely on the installed packages so
      // `react-router/dom` resolves to the real `react-router` package.
    }
  }
});
