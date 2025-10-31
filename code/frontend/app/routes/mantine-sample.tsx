/**
 * This is just a sample route to experiment with
 * the Mantine UI component library.
 */

import type { Route } from "./+types/home";
import { useState } from "react";
import { Switch, Group, Text } from "@mantine/core";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Sample Route for Mantine UI" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export default function Sample() {
  const [checked, setChecked] = useState(false);

  return (
    <Group justify="center" mt="xl">
      <Text fw={500}>Toggle mode:</Text>
      <Switch
        checked={checked}
        onChange={(event) => setChecked(event.currentTarget.checked)}
        onLabel="ON"
        offLabel="OFF"
        size="lg"
        color="teal"
      />
      <Text>{checked ? "Enabled" : "Disabled"}</Text>
    </Group>
  );
}
