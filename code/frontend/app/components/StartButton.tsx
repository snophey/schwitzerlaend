import { Button, Container, Stack, Text, Title, Image, type ButtonProps } from "@mantine/core";
import type React from "react";

interface ButtonText {
  text: string 
}

const StartButton: React.FC<ButtonText> = ({ text }) => {
  return (
    < Button
      component="a"
      href="#"
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