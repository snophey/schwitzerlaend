import { Button, Container, Stack, Text, Title, Image, type MantineStyleProp } from "@mantine/core";
import type React from "react";

interface ButtonProps {
    text: string,
    onClick: () => void,
    type?: "button" | "submit",
    style?: MantineStyleProp;
}

const NextButton: React.FC<ButtonProps> = ({ text, onClick, type="button", style }) => {
    return (
        <Button
            onClick={onClick}
            type={type}
            color="red"
            radius="xs"
            size="md"
            mt="md" style={{
                width: 60,
                height: 60,
                padding: 0,
                ...(style || {})
            }}
        >
            {text}
        </Button>
    );
}

export default NextButton;