import { Button, Container, Stack, Text, Title, Image, type ButtonProps } from "@mantine/core";
import type React from "react";
import { Link } from "react-router";

interface ButtonText {
  text: string,
}

const StartButton: React.FC<ButtonText> = ({ text }) => {
  return (
    < Button
      component={Link}
      to="/onboarding"
      color="red"
      radius="xs"
      size="md"
      mt="md"
    >
      {text}
    </Button >
  );
}

export default StartButton;