import { Button, Container, Stack, Text, Title, Image } from "@mantine/core";
import type React from "react";

interface ButtonProps {
    text: string,
    onClick: () => void,
}

const NextButton: React.FC<ButtonProps> = ({ text, onClick }) => {
    return (
        <Button
            onClick={onClick}
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