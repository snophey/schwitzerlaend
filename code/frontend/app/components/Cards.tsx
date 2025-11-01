import React, { useState } from 'react';
import { GiSkateboard } from 'react-icons/gi';
import { LuDumbbell } from 'react-icons/lu';
import { FiCheck, FiPlus } from 'react-icons/fi';

interface Activity {
  id: string;
  label: string;
  icon: React.ReactNode;
}

export default function Cards() {
  const activities: Activity[] = [
    { id: 'skateboard', label: 'Skateboard', icon: <GiSkateboard className="w-10 h-10 mb-2 text-gray-700" /> },
    { id: 'strength', label: 'Strength', icon: <LuDumbbell className="w-10 h-10 mb-2 text-gray-700" /> },
    { id: 'custom', label: 'Add my own', icon: <FiPlus className="w-10 h-10 mb-2 text-gray-700" /> },
  ];

  const [selected, setSelected] = useState<string[]>(['skateboard', 'strength']);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 p-6 place-items-center">
      {activities.map((activity) => {
        const isChecked = selected.includes(activity.id);
        return (
          <button
            key={activity.id}
            type="button"
            onClick={() => toggle(activity.id)}
            className={`
              relative flex flex-col items-center justify-center
              border rounded-md w-40 h-40
              transition-all duration-150
              hover:border-gray-400 hover:shadow-sm
              ${isChecked ? 'ring-2 ring-red-500 border-red-400 bg-red-50' : 'border-gray-300'}
            `}
          >
            {/* red check circle */}
            {isChecked && (
              <div className="absolute -top-2 -right-2 bg-red-500 rounded-full p-1 shadow">
                <FiCheck className="text-white w-3 h-3" />
              </div>
            )}

            {activity.icon}

            <p className="text-sm font-medium text-gray-800">{activity.label}</p>
          </button>
        );
      })}
    </div>
  );
}
