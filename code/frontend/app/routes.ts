import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  route("mantine", "routes/mantine-sample.tsx"),
  index("routes/onboarding.tsx"),
  route("onboarding", "routes/onboarding-form.tsx"),
  route("home", "routes/home.tsx"),
  route("workout", "routes/workout.tsx"),
] satisfies RouteConfig;
