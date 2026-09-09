import { createFileRoute } from "@tanstack/react-router";
import { LandingPage } from "@/components/landing/LandingPage";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "CycloVision — Sub-kilometer Cyclone Forecasting Powered by Continuous Satellite AI" },
      { name: "description", content: "CycloVision bypasses traditional numerical simulation bottlenecks. Globally scaled neural tensor network predicting tropical cyclogenesis, wind radii, and rapid intensification." },
      { property: "og:title", content: "CycloVision — Continuous Satellite AI Cyclone Intelligence" },
      { property: "og:description", content: "Sub-kilometer cyclone forecasting powered by continuous satellite AI." },
    ],
  }),
  component: LandingPage,
});

