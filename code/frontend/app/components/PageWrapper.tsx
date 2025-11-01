import { Container, Flex } from "@mantine/core";

interface AppPageProps {
  children: React.ReactNode;
}

export default function PageWrapper({ children }: AppPageProps) {
  return (
    <Flex justify="center" align="center" mih="100vh">
      <Container
        size={380}
        p="xl"
        style={{
          backgroundColor: "white",
          textAlign: "center",
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        }}
      >
        {children}
      </Container>
    </Flex>
  );
}
