import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("mantine", "routes/mantine-sample.tsx"),
  route("onboarding", "routes/onboarding.tsx"),
] satisfies RouteConfig;
