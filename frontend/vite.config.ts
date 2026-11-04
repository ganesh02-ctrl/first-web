/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  envDir: "..", // read VITE_* from the project-root .env
  server: { port: 5173 },
  test: { environment: "jsdom", setupFiles: ["./src/setupTests.ts"], globals: true },
});
