import { Button, Container, Stack, Text, Title, Image, type ButtonProps } from "@mantine/core";
import type React from "react";
import { FaArrowLeft } from "react-icons/fa6";

interface ButtonText {
    text: string,
    onClick: () => void,
}

const BackButton: React.FC<ButtonText> = ({ text, onClick}) => {
    return (
        <Button
            onClick={onClick}
            component="a"
            href="#"
            variant="subtle"
            color="gray"
            radius="xs"
            size="md"
            leftSection={<FaArrowLeft />}
            mt="md" style={{
                height: 70,
            }}
        >
            {text}
        </Button>
    );
}

export default BackButton;