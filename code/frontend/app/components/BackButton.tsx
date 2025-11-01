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
            color="transpart"
            radius="xs"
            size="md"
            mt="md" style={{
                width: 60,
                height: 60,
                padding: 0,
            }}
        >

            <FaArrowLeft />
            {text}
        </Button>
    );
}

export default BackButton;