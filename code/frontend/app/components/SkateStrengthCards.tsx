import React, { useState } from 'react';
import { TbGrowth } from "react-icons/tb";
import { TbMeteor } from "react-icons/tb";
import { FiCheck, FiPlus } from 'react-icons/fi';



interface Activity {
  id: string;
  label: string;
  icon: React.ReactNode;
  freitext?: boolean;
}

/**
 * The remaining icons should be added
 */

export default function SkateCards() {
  const activities: Activity[] = [
    { id: 'beginner', label: 'Beginner', icon: <TbGrowth className="w-10 h-10 mb-2 text-gray-700" /> },
    { id: 'master', label: 'Master', icon: <TbMeteor className="w-10 h-10 mb-2 text-gray-700" /> },
  ];

  const [selected, setSelected] = useState<string[]>(['skateboard', 'strength']);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex flex-col items-center space-y-6 p-6">
      {/* top row */}
      <div className="grid grid-cols-5 gap-6">
        {activities.slice(0, 2).map((activity) => {
          const isChecked = selected.includes(activity.id);
          return (
            <button
              key={activity.id}
              type="button"
              onClick={() => toggle(activity.id)}
              className={`
                relative flex flex-col items-center justify-center
                border rounded-md w-20 h-20
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

   </div>
  );
}
