import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface SkillData {
  skill: string;
  required: number;
  current: number;
}

interface SkillRadarChartProps {
  data: SkillData[];
  showLegend?: boolean;
}

export default function SkillRadarChart({ data, showLegend = true }: SkillRadarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-gray-500">
        No data available for chart
      </div>
    );
  }

  // Limit to top 8 skills for readability
  const chartData = data.slice(0, 8).map((item) => ({
    skill: item.skill.length > 15 ? item.skill.slice(0, 15) + '...' : item.skill,
    required: item.required,
    current: item.current,
    fullName: item.skill,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
        <PolarGrid strokeDasharray="3 3" />
        <PolarAngleAxis
          dataKey="skill"
          tick={{ fill: '#6b7280', fontSize: 11 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 10]}
          tick={{ fill: '#9ca3af', fontSize: 10 }}
        />
        <Radar
          name="Required Level"
          dataKey="required"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Radar
          name="Your Level"
          dataKey="current"
          stroke="#10b981"
          fill="#10b981"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Tooltip
          content={({ payload }) => {
            if (!payload || payload.length === 0) return null;
            const data = payload[0]?.payload;
            return (
              <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                <p className="font-medium text-gray-900 mb-2">{data?.fullName}</p>
                <p className="text-sm text-primary-600">
                  Required: {data?.required?.toFixed(1)}
                </p>
                <p className="text-sm text-green-600">
                  Your Level: {data?.current?.toFixed(1)}
                </p>
              </div>
            );
          }}
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
          />
        )}
      </RadarChart>
    </ResponsiveContainer>
  );
}
