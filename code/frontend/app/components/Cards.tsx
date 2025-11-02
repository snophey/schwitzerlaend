import React, { useEffect, useState } from "react";
import { GiSkateboard } from "react-icons/gi";
import { LuDumbbell } from "react-icons/lu";
import { FiCheck, FiPlus } from "react-icons/fi";

interface Activity {
  id: string;
  label: string;
  icon: React.ReactNode;
  freitext?: boolean;
}

interface CardsProps {
  onSelect?: (selected: string[]) => void;
  selected?: string[];
}

export default function Cards({
  onSelect,
  selected: controlledSelected = [],
}: CardsProps) {
  const [selected, setSelected] = useState<string[]>(
    controlledSelected as string[]
  );

  const activities: Activity[] = [
    {
      id: "skateboard",
      label: "Skateboard",
      icon: <GiSkateboard className="max-sm:w-8 w-10 h-10 mb-2 text-gray-700" />,
    },
    {
      id: "strength",
      label: "Strength",
      icon: <LuDumbbell className="max-sm:w-8 w-10 h-10 mb-2 text-gray-700" />,
    },
    {
      id: "custom",
      label: "Add my own",
      icon: <FiPlus className="max-sm:w-8 w-10 h-10 mb-2 text-gray-700" />,
      freitext: true,
    },
  ];

  // set default selected from props
  useEffect(() => {
    setSelected(controlledSelected);
  }, [controlledSelected]);

  const toggle = (id: string) => {
    setSelected((prev) => {
      const updated = prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id];

      if (onSelect) onSelect(updated);
      return updated;
    });
  };

  return (
    <div className="flex flex-col items-center space-y-6 p-6">
      {/* top row */}
      <div className="grid grid-cols-2 gap-6">
        {activities.slice(0, 2).map((activity) => {
          const isChecked = selected.includes(activity.id);
          return (
            <button
              key={activity.id}
              type="button"
              onClick={() => toggle(activity.id)}
              className={`
                max-sm:w-24 max-sm:h-24
                relative flex flex-col items-center justify-center
                border rounded-md w-40 h-40
                transition-all duration-150
                hover:border-gray-400 hover:shadow-sm
                ${isChecked ? 'ring-2 ring-red-500 border-red-400 bg-red-50' : 'border-gray-300'}
              `}
            >
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

      {/* bottom card */}
      <div className="flex flex-col items-center">
        {activities.slice(2).map((activity) => (
          <button
            key={activity.id}
            type="button"
            onClick={() => toggle(activity.id)}
            className={`
              max-sm:w-24 max-sm:h-24
              relative flex flex-col items-center justify-center
              border rounded-md w-40 h-40
              transition-all duration-150
              hover:border-gray-400 hover:shadow-sm
              ${selected.includes(activity.id) ? 'ring-2 ring-red-500 border-red-400 bg-red-50' : 'border-gray-300'}
            `}
          >
            {selected.includes(activity.id) && (
              <div className="absolute -top-2 -right-2 bg-red-500 rounded-full p-1 shadow">
                <FiCheck className="text-white w-3 h-3" />
              </div>
            )}
            {activity.icon}
            <p className="text-sm font-medium text-gray-800">{activity.label}</p>
          </button>
        ))}
        <p className="mt-2 text-sm text-gray-600">Freitext</p>
      </div>
    </div>
  );
}
