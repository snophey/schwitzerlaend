import {
  Button,
  Container,
  Stack,
  Text,
  Title,
  Image,
  Group,
  Alert,
  rem,
} from "@mantine/core";
import type { Route } from "./+types/onboarding-form";
import NextButton from "~/components/NextButton";
import Backbutton from "~/components/BackButton";
import { Form } from "react-router";
import { WeekdaySelector } from "~/components/weekday-select/WeekdaySelect";
import PageWrapper from "~/components/PageWrapper/PageWrapper";
import { useState } from "react";
import { Textarea } from "@mantine/core";
import { getSession } from "~/sessions.server";
import { TbInfoSquare } from "react-icons/tb";
import Cards from "~/components/Cards";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export async function action({ request }: Route.ActionArgs) {
  const session = await getSession(request.headers.get("Cookie"));
  console.log("Logged in as: " + session.get("userId"));
  console.log("Form submitted");
  console.log(await request.formData());
}

// TODO: REPLACE LINK WITH ROUTE TO NEXT SCREEN
// TODO: REFACTOR HARD-CODED STYLES T
export default function OnboardingForm() {
  let [step, setStep] = useState(0);

  return (
    <Form method="post" action="/onboarding">
      <PageWrapper>
        <Stack align="stretch">
          <Stack
            align="center"
            gap="md"
            display={step === 0 ? "block" : "none"}
          >
            <Title mb="lg" order={2}>
              Let's start with your profile
            </Title>
            <Text size="sm">Which sport do you want to train?</Text>

            <Cards />
            <Textarea
              style={{ textAlign: "center" }}
              mt={"md"}
              variant="filled"
              label="Freitext"
              name="injuries-specialties"
              placeholder="Add your own sport"
            />

          </Stack>

          <Stack
            align="center"
            gap="md"
            display={step === 1 ? "block" : "none"}
          >
            <Title mb="lg" order={2}>
              Your training sessions
            </Title>
            <Text size="sm">
              How many training sessions would you like to have per week?
            </Text>
            <Stack align="flex-start" gap="sm">
              <Title order={3} size={"sm"} mt={"md"}>
                Skateboard
              </Title>
              <WeekdaySelector prefix="skateboard-" />
            </Stack>
            <Stack align="flex-start" gap="sm" mt={"md"}>
              <Title order={3} size={"sm"}>
                Strength
              </Title>
              <WeekdaySelector prefix="strength-" />
            </Stack>
            <Alert
              variant="light"
              color="red"
              mt="md"
              style={{ textAlign: "left" }}
            >
              <TbInfoSquare />
              Plan your training days with recovery in mind! If your muscles
              feel tired or sore, give your body time to rest. Recovery is where
              progress happens.
            </Alert>
          </Stack>
          <Stack
            align="center"
            gap="md"
            display={step === 2 ? "block" : "none"}
          >
            <Title order={2} mb={"lg"}>
              Your skill level
            </Title>
            <Text size="sm">
              How advanced are you? Briefly describe your current skill level in
              your sport.
            </Text>
            <Textarea
              style={{ textAlign: "left" }}
              mt={"md"}
              variant="filled"
              name="experience-skateboard"
              label="Skateboard"
              placeholder="For example, how long have you been training? What techniques or skills have you already mastered?"
            />
            <Textarea
              style={{ textAlign: "left" }}
              mt={"md"}
              variant="filled"
              label="Strength"
              name="experience-strength"
              placeholder="For example, how long have you been training? What fitness-related achievement are you most proud of?"
            />
          </Stack>
          <Stack
            align="center"
            gap="md"
            display={step === 3 ? "block" : "none"}
          >
            <Title order={2} mb={"lg"}>
              Your goals
            </Title>
            <Text size="sm">What are the main goal of your training?</Text>
            <Textarea
              style={{ textAlign: "left" }}
              mt={"md"}
              variant="filled"
              label="Skateboard"
              name="goals-skateboard"
              placeholder="For example, what skills are you trying to master?"
            />
            <Textarea
              style={{ textAlign: "left" }}
              mt={"md"}
              variant="filled"
              label="Strength"
              name="goals-strength"
              placeholder="For example, are you training for strength or hypertrophy?"
            />
          </Stack>
          <Stack
            align="center"
            gap="md"
            display={step === 4 ? "block" : "none"}
          >
            <Title order={2} mb={"lg"}>
              Anything we should know about your body
            </Title>
            <Text size="sm">
              Your plan will adapt to keep you safe and progressing.
            </Text>
            <Textarea
              style={{ textAlign: "left" }}
              mt={"md"}
              variant="filled"
              label="Additional information"
              name="injuries-specialties"
              placeholder="Do you have any injuries or physical limitations we should be aware of?"
            />
          </Stack>
          <Group justify="space-between" mt="auto" mb="md">
            {step > 0 && (
              <Backbutton onClick={() => setStep(step - 1)} text="Back" />
            )}
            {step < 4 && (
              <NextButton
                style={{
                  marginLeft: "auto",
                }}
                onClick={() => setStep(step + 1)}
                text="Next"
              />
            )}
            {step === 4 && (
              <NextButton type="submit" onClick={() => {}} text="Begin" />
            )}
          </Group>
        </Stack>
        <Button type="submit" fullWidth mt="xl">
          [DEBUG] Submit
        </Button>
      </PageWrapper>
    </Form>
  );
}
