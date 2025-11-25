import { IconType } from 'react-icons';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: IconType;
  color: 'blue' | 'green' | 'red' | 'yellow';
}

const StatsCard = ({ title, value, icon: Icon, color }: StatsCardProps) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs sm:text-sm text-gray-600 mb-1 truncate">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold text-gray-800 truncate">{value}</p>
        </div>
        <div className={`p-2 sm:p-3 rounded-lg flex-shrink-0 ${colorClasses[color]}`}>
          <Icon className="text-lg sm:text-2xl" />
        </div>
      </div>
    </div>
  );
};

export default StatsCard;
