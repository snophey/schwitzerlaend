import { useDisclosure } from "@mantine/hooks";
import {
  Stack,
  Modal,
  Button,
  Text,
  Title,
  Image,
  Container,
} from "@mantine/core";
import animation from "assets/img/deadhang.gif";

import { Link } from "react-router";

export function VictoryModal({
  opened,
  close,
  open,
}: {
  opened: boolean;
  open: () => void;
  close: () => void;
}) {
  return (
    <>
      <Modal
        opened={opened}
        onClose={close}
        title=""
        radius={0}
        fullScreen
        transitionProps={{ transition: "fade", duration: 200 }}
      >
        <Container maw={450} mx="auto">
          <Image
            src={animation}
            alt="Victory animation"
            fit="contain"
            style={{
              margin: "-4rem auto -3rem auto",
              maxWidth: "20rem",
            }}
          />
          <Stack align="center" mb="md" ta="center" gap={20}>
            <Title>Well done!</Title>
            <Text size="md" mb="md">
              You have completed your workout for today. Great job on staying
              consistent and pushing yourself! Keep up the good work and see you
              in the next session.
            </Text>
            <Button
              component={Link}
              to={"/workout"}
              onClick={close}
              size="lg"
              mt="auto"
            >
              Next Workout
            </Button>
          </Stack>
        </Container>
      </Modal>
    </>
  );
}
