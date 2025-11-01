import { Button, Container, Stack, Text, Title, Image } from "@mantine/core";
import type { Route } from "./+types/home";
import PageWrapper from "~/components/PageWrapper/PageWrapper";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Welcome to Sweatzerländ!" },
    { name: "description", content: "Welcome to Sweatzerländ!" },
  ];
}

// TODO: REPLACE LINK WITH ROUTE TO NEXT SCREEN
export default function Onboarding() {
  return (
    <PageWrapper>
      <Stack align="center" gap="md">
        {/* Logo */}
        <div>
          <Image
            src="/../assets/img/logo.svg"
            alt="Schwitzerland logo"
            w={72}
            mx="auto"
            styles={{
              root: { transform: "translateX(-0.5em)" },
            }}
          />
          <Text fw={600} mt="xs">
            Schwitzerland
          </Text>
        </div>

        {/* Headline */}
        <Title order={1} mt="md" fw={700}>
          Saison egal.
          <br />
          Hauptsache du schwitzt.
        </Title>

        {/* Description */}
        <Text c="dimmed" fz="sm" maw={280}>
          Mit Schwitzerland trackst du dein Training: egal ob du pumpst, skatest
          oder frierst. Eine App für alle Sportarten, das ganze Jahr.
        </Text>

        {/* Button */}
        <Button
          component="a"
          href="#"
          color="red"
          radius="xs"
          size="md"
          mt="md"
        >
          Let’s schwiitz
        </Button>
      </Stack>
    </PageWrapper>
  );
}
