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
import { Form, redirect } from "react-router";
import { WeekdaySelector } from "~/components/weekday-select/WeekdaySelect";
import PageWrapper from "~/components/PageWrapper/PageWrapper";
import { useState } from "react";
import { Textarea } from "@mantine/core";
import { getSession } from "~/sessions.server";
import { TbInfoSquare } from "react-icons/tb";
import { useActionData } from "react-router";
import Cards from "~/components/Cards";
import SkateCards from "~/components/SkateStrengthCards";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export async function action({ request }: Route.ActionArgs) {
  const session = await getSession(request.headers.get("Cookie"));
  const userId = session.get("userId");
  const formData = await request.formData();

  console.log("Logged in as: " + userId);
  console.log("Form submitted");
  console.log(formData);

  /* --- Try to create user --- */
  try {
    const response = await fetch(`${process.env.BACKEND_URL}/users/${userId}`, {
      method: "POST",
    });

    if (!response.ok && response.status !== 409) {
      // throw error if not OK (except if user already exists, that's a 409 error which is fine ;)
      throw new Error("Backend request failed");
    }
  } catch (e) {
    console.error("Error posting workout data", e);
    return { error: "Submit failed" };
  }

  /* ------------------ */

  // Convert FormData → plain object → JSON
  const data = Object.fromEntries(formData.entries());
  const prompt =
    "You are a professional, virtual fitness coach. As an LLM, queried over an API you should help users create their personalized weekly workout plan based on the attached context information. Generate a detailed workout schedule that includes specific exercises, sets, reps, and rest periods for each training day. Ensure the plan is balanced and considers recovery time. Respect the given context information the user has provided, like body condition, existing experience and selected sports. | Here is an explanation of the given data structure key by key: " +
    "'injuries-specialties': Any injuries or physical limitations." +
    "'<sport>-<weekday>': preferred weekdays are marked with an on flag" +
    "'experience-<sport>': experience level description for the given sport" +
    "'goals-<sport>': main training goals for the given sport" +
    " | Here is the context information in JSON format: | ";

  const jsonPayload = JSON.stringify({ prompt: prompt + JSON.stringify(data) });
  console.log("Submitting JSON:", jsonPayload);

  try {
    const response = await fetch(
      `${process.env.BACKEND_URL}/users/${userId}/generate-workout`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: jsonPayload,
      }
    );

    if (!response.ok) {
      throw new Error("Backend request failed");
    }

    const jsonResponse = await response.json();
    console.log("Received response:", jsonResponse);

    return redirect("/home");
  } catch (e) {
    console.error("Error posting workout data", e);
    return { error: "Submit failed" };
  }
}

export default function OnboardingForm() {
  const data = useActionData<{ error?: string; workout?: any }>();
  let [step, setStep] = useState(0);

  return (
    <PageWrapper>
      {data?.error && <Alert color="red">{data.error}</Alert>}
      {data && !data.error && <pre>{JSON.stringify(data, null, 2)}</pre>}

      <Form method="post" action="/onboarding">
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
            <SkateCards />
            <Textarea
              style={{ textAlign: "left" }}
              mt={"md"}
              variant="filled"
              label="Strength"
              name="experience-strength"
              placeholder="For example, how long have you been training? What fitness-related achievement are you most proud of?"
            />

            <SkateCards />
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
      </Form>
    </PageWrapper>
  );
}
