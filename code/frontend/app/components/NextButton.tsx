import { Button, Container, Stack, Text, Title, Image, type ButtonProps } from "@mantine/core";
import type React from "react";

interface ButtonText {
    text: string
}

const NextButton: React.FC<ButtonText> = ({ text }) => {
    return (
        <Button
            component="a"
            href="#"
            color="red"
            radius="xs"
            size="md"
            mt="md" style={{
                width: 60,
                height: 60,
                padding: 0,
            }}
        >
            {text}
        </Button>
    );
}

export default NextButton;