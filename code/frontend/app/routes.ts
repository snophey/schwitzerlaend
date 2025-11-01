import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/onboarding.tsx"),
  route("onboarding", "routes/onboarding-form.tsx"),
  route("home", "routes/home.tsx"),
  route("done", "routes/done.tsx"),
] satisfies RouteConfig;
