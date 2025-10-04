import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const purchaseData = [
  { vendor: 'Vendor A', amount: 45000 },
  { vendor: 'Vendor B', amount: 38000 },
  { vendor: 'Vendor C', amount: 52000 },
  { vendor: 'Vendor D', amount: 29000 },
  { vendor: 'Vendor E', amount: 41000 },
];

export default function Purchase() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Total Purchases</h3>
          <p className="text-3xl font-bold text-gray-800">₹2,05,000</p>
          <p className="text-sm text-red-600 mt-1">↑ 5.2% from last month</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Active Vendors</h3>
          <p className="text-3xl font-bold text-gray-800">28</p>
          <p className="text-sm text-blue-600 mt-1">3 new this month</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500 mb-1">Pending Payments</h3>
          <p className="text-3xl font-bold text-gray-800">₹87,500</p>
          <p className="text-sm text-orange-600 mt-1">5 invoices overdue</p>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Top Vendors by Purchase Amount</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={purchaseData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="vendor" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="amount" fill="#FF9800" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
