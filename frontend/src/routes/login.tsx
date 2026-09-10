import { createFileRoute } from "@tanstack/react-router";
import { AuthPage } from "@/components/auth/AuthPage";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign In — CycloVision" },
      { name: "description", content: "Sign in to access your CycloVision mission control workspace and real-time cyclone telemetry." },
      { property: "og:title", content: "Sign In — CycloVision" },
      { property: "og:description", content: "Sign in to access your CycloVision workspace." },
    ],
  }),
  component: AuthPage,
});
