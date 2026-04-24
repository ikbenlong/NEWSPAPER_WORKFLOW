import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_mfyolzacjukmlbqvcygt",
  dirs: ["src/trigger"],
  maxDuration: 300, // 5 minutes — covers Perplexity + Claude + email send
  retries: {
    enabledInDev: false,
  },
});
