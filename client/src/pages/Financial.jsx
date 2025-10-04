import { motion } from 'framer-motion';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const plData = [
  { month: 'Jan', revenue: 85000, expenses: 62000, profit: 23000 },
  { month: 'Feb', revenue: 92000, expenses: 68000, profit: 24000 },
  { month: 'Mar', revenue: 88000, expenses: 65000, profit: 23000 },
  { month: 'Apr', revenue: 98000, expenses: 72000, profit: 26000 },
  { month: 'May', revenue: 105000, expenses: 78000, profit: 27000 },
  { month: 'Jun', revenue: 112000, expenses: 82000, profit: 30000 },
];

export default function Financial() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Total Revenue</h3>
          <p className="text-3xl font-bold text-green-600">₹5,80,000</p>
          <p className="text-sm text-gray-500 mt-1">Last 6 months</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Total Expenses</h3>
          <p className="text-3xl font-bold text-red-600">₹4,27,000</p>
          <p className="text-sm text-gray-500 mt-1">Last 6 months</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Net Profit</h3>
          <p className="text-3xl font-bold text-blue-600">₹1,53,000</p>
          <p className="text-sm text-green-600 mt-1">↑ 15.3% margin</p>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Profit & Loss Statement</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={plData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="revenue" stroke="#4CAF50" strokeWidth={2} />
            <Line type="monotone" dataKey="expenses" stroke="#F44336" strokeWidth={2} />
            <Line type="monotone" dataKey="profit" stroke="#0052CC" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Monthly Comparison</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={plData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="revenue" fill="#4CAF50" />
            <Bar dataKey="expenses" fill="#F44336" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
