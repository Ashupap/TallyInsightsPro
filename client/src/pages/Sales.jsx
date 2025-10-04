import { motion } from 'framer-motion';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const salesData = [
  { month: 'Jan', revenue: 45000, orders: 120 },
  { month: 'Feb', revenue: 52000, orders: 145 },
  { month: 'Mar', revenue: 48000, orders: 132 },
  { month: 'Apr', revenue: 61000, orders: 168 },
  { month: 'May', revenue: 55000, orders: 152 },
  { month: 'Jun', revenue: 67000, orders: 185 },
];

export default function Sales() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Total Revenue</h3>
          <p className="text-3xl font-bold text-gray-800">₹3,28,000</p>
          <p className="text-sm text-green-600 mt-1">↑ 12.5% from last period</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Total Orders</h3>
          <p className="text-3xl font-bold text-gray-800">902</p>
          <p className="text-sm text-green-600 mt-1">↑ 8.3% from last period</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Average Order Value</h3>
          <p className="text-3xl font-bold text-gray-800">₹3,637</p>
          <p className="text-sm text-blue-600 mt-1">+₹150 from last period</p>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Revenue Trend</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={salesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="revenue" stroke="#0052CC" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Orders by Month</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={salesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="orders" fill="#4CAF50" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
