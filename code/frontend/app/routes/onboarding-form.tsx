import { Button, Container, Stack, Text, Title, Image } from "@mantine/core";
import type { Route } from "./+types/onboarding-form";
import StartButton from "~/components/StartButton";
import NextButton from "~/components/NextButton";
import { Form } from "react-router";
import { WeekdaySelector } from "~/components/weekday-select/WeekdaySelect";
import PageWrapper from "~/components/PageWrapper/PageWrapper";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export async function action({ request }: Route.ActionArgs) {
  console.log("Form submitted");
  console.log(await request.formData());
}

// TODO: REPLACE LINK WITH ROUTE TO NEXT SCREEN
// TODO: REFACTOR HARD-CODED STYLES T
export default function OnboardingForm() {
  return (
    <PageWrapper>
      <Form method="post" action="/onboarding">
        <Stack align="center" gap="md">
          <Title order={2} >
            Your training sessions
          </Title>
          <Text size="sm" >
            How many training sessions would you like to have per week?
          </Text>
          <Stack align="flex-start" gap="sm">
            <Title order={3} size={"sm"} >Skateboard</Title>
            <WeekdaySelector />
          </Stack>
          <Stack align="flex-start" gap="sm">
            <Title order={3} size={"sm"} >Strength</Title>
            <WeekdaySelector />
          </Stack>
        </Stack>
        <Button type="submit" fullWidth mt="xl">
          [DEBUG] Submit
        </Button>
      </Form>
    </PageWrapper>
  );
}
