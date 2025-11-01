import { Button, Container, Stack, Text, Title, Image } from "@mantine/core";
import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

// TODO: REPLACE LINK WITH ROUTE TO NEXT SCREEN
// TODO: REFACTOR HARD-CODED STYLES T
export default function Onboarding() {
  return (
    <Container
      size={380}
      p="xl"
      style={{
        backgroundColor: "white",
        borderRadius: "8px",
        textAlign: "center",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}
    >
      <Stack align="center" gap="md">
        {/* Logo */}
        <div>
          <Image
            src="/logo.png" // replace with your image path
            alt="Schwitzerland logo"
            w={64}
            mx="auto"
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
    </Container>
  );
}
