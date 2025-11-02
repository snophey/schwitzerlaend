import { useDisclosure } from '@mantine/hooks';
import { Modal, Button, Text } from '@mantine/core';
import { Link } from 'react-router';

export function VictoryModal({ opened, close, open }: { opened: boolean, open: () => void; close: () => void }) {
  return (
    <>
      <Modal
        opened={opened}
        onClose={close}
        title="Well done!"
        fullScreen
        radius={0}
        transitionProps={{ transition: 'fade', duration: 200 }}
      >
        <Text size="lg" mb="md">
          You have completed your workout for today. Great job on staying consistent and pushing
          yourself! Keep up the good work and see you in the next session.
        </Text>
        <Button component={Link} to={"/workout"} onClick={close}>
          Next Workout
        </Button>
      </Modal>
    </>
  );
}