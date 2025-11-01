import { Text } from '@mantine/core';


interface Tag extends React.PropsWithChildren {
    color: string;
}

export const Tag = ({ color, children }: Tag) => {
    return (
      <div className="flex items-center gap-2">
        <div className={`bg-${color}  rounded-md p-1`}>
          <Text size="sm">{children}</Text>
        </div>
      </div>
    );
  };