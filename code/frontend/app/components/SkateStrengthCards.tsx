import React, { useState } from 'react';
import { Button, Group, Text, rem } from '@mantine/core';
import { TbGrowth, TbMeteor, TbSeeding, TbHaze, TbFlame } from "react-icons/tb";

interface SkillLevel {
  id: string;
  label: string;
  icon: React.ReactNode;
}

interface SkateCardsProps {
  selectedLevel?: string;
  onLevelChange?: (level: string) => void;
  name?: string;
}

export default function SkateCards({ selectedLevel, onLevelChange, name }: SkateCardsProps) {
  const skillLevels: SkillLevel[] = [
    { id: 'beginner', label: 'Beginner', icon: <TbSeeding size={24} /> },
    { id: 'intermediate-low', label: 'Intermediate-', icon: <TbGrowth size={24} /> },
    { id: 'intermediate', label: 'Intermediate', icon: <TbHaze size={24} /> },
    { id: 'advanced', label: 'Advanced', icon: <TbFlame size={24} /> },
    { id: 'master', label: 'Master', icon: <TbMeteor size={24} /> },
  ];

  const handleLevelSelect = (levelId: string) => {
    if (onLevelChange) {
      onLevelChange(levelId);
    }
  };

  return (
    <>
      <Group gap="xs" mb="md" w="100%">
        {skillLevels.map((level) => (
          <Button
            key={level.id}
            color='red'
            variant={selectedLevel === level.id ? "filled" : "outline"}
            size="lg"
            style={{
              flex: 1,
              height: rem(60),
              display: 'flex',
              flexDirection: 'column',
              padding: rem(8),
              border: '1px solid #e9ecef',
              borderColor: selectedLevel === level.id ? '#fa5252' : '#e9ecef'
            }}
            onClick={() => handleLevelSelect(level.id)}
          >
            {level.icon}
          </Button>
        ))}
      </Group>
      {name && (
        <input type="hidden" name={name} value={selectedLevel || ""} />
      )}
      <Group justify="space-between" w="100%" mb="md">
        <Text size="xs" c="dimmed">Beginner</Text>
        <Text size="xs" c="dimmed">Master</Text>
      </Group>
    </>
  );
}
