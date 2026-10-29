import { defineConfig } from "orval";

export default defineConfig({
  secureship: {
    input: "http://localhost:8000/openapi.json",
    output: {
      target: "src/api/generated/secureship.ts",
      client: "react-query",
      httpClient: "fetch",
    },
  },
});
