import { motion } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Brain, Target } from 'lucide-react';

const forecastData = [
  { month: 'Jul', actual: 112000, forecast: 115000 },
  { month: 'Aug', actual: null, forecast: 120000 },
  { month: 'Sep', actual: null, forecast: 125000 },
  { month: 'Oct', actual: null, forecast: 130000 },
  { month: 'Nov', actual: null, forecast: 135000 },
  { month: 'Dec', actual: null, forecast: 142000 },
];

export default function Analytics() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">AI Insights</h3>
              <p className="text-3xl font-bold text-gray-800">12</p>
              <p className="text-sm text-blue-600 mt-1">actionable recommendations</p>
            </div>
            <Brain className="text-purple-500" size={32} />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">Growth Rate</h3>
              <p className="text-3xl font-bold text-green-600">+18.5%</p>
              <p className="text-sm text-gray-500 mt-1">projected next quarter</p>
            </div>
            <TrendingUp className="text-green-500" size={32} />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm text-gray-500 mb-1">Forecast Accuracy</h3>
              <p className="text-3xl font-bold text-blue-600">94.2%</p>
              <p className="text-sm text-gray-500 mt-1">based on last quarter</p>
            </div>
            <Target className="text-blue-500" size={32} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Revenue Forecast</h3>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={forecastData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area
              type="monotone"
              dataKey="actual"
              stroke="#0052CC"
              fill="#0052CC"
              fillOpacity={0.6}
              name="Actual Revenue"
            />
            <Area
              type="monotone"
              dataKey="forecast"
              stroke="#4CAF50"
              fill="#4CAF50"
              fillOpacity={0.3}
              strokeDasharray="5 5"
              name="Forecasted Revenue"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">AI-Powered Insights</h3>
        <div className="space-y-4">
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="p-4 bg-blue-50 border border-blue-200 rounded-lg"
          >
            <h4 className="font-medium text-blue-900 mb-1">Revenue Opportunity</h4>
            <p className="text-sm text-blue-700">
              Product category "Electronics" shows 23% growth potential. Consider increasing inventory by 15%.
            </p>
          </motion.div>
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="p-4 bg-green-50 border border-green-200 rounded-lg"
          >
            <h4 className="font-medium text-green-900 mb-1">Cost Optimization</h4>
            <p className="text-sm text-green-700">
              Vendor consolidation could reduce procurement costs by ₹12,000/month based on current patterns.
            </p>
          </motion.div>
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="p-4 bg-purple-50 border border-purple-200 rounded-lg"
          >
            <h4 className="font-medium text-purple-900 mb-1">Customer Segmentation</h4>
            <p className="text-sm text-purple-700">
              Top 20% customers generate 68% of revenue. Implement loyalty program to increase retention.
            </p>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
